#Usage: python start_cluster.py [cluster name] [number of shards] [rep sets per shard] [keypair name] [keypair location]
#AWS key and secret taken from environment variables

import sys, commands, os, string
from py.mongo_cluster import *
from py.ec2_cluster import *
from boto.ec2.connection import EC2Connection, EC2ResponseError

def main():

	#Load command line args & environment variables
	cluster_name = sys.argv[1]
	n = int(sys.argv[2])
	reps = int(sys.argv[3])
	keypair_name = sys.argv[4]
	keypair_location = sys.argv[5]	
	key = os.environ['AWS_ACCESS_KEY_ID']
	secret = os.environ['AWS_SECRET_ACCESS_KEY']

	#Startup scripts for the EC2 instances
	shard_startup = open('sh/shard_startup.sh', 'r').read()
        config_startup = open('sh/config_startup.sh', 'r').read()

	#All mongo clusters must have either 1 or 3 config nodes
	num_config = 3

	#No negative nodes or rep sets
	assert n>0 && reps>0

	#Connect
	try:
                con = EC2Connection(key, secret)
	        mongo = con.create_security_group(cluster_name, 'Group for'+cluster_name+'mongo cluster')
	
		#Start EC2 instances
		print "Starting up instances"
		con = EC2Connection(key, secret)
		image = con.get_all_images(image_ids=['ami-68ad5201'])[0] #Ubuntu 11.04 Natty 64-bit Server

		#Replication DBs, by shard
		shard_inst = {}
		shard_names = {}

		for i in range(0, n):

			shard_name = 'set'+str(i)
			shard_startup_sub = string.replace(shard_startup, '$SETNAME', shard_name)

			shard_reservation = image.run(
				reps, 
				reps, 
				security_groups=[cluster_name], 
				instance_type='m1.large', 
				key_name=keypair_name, 
				user_data=shard_startup_sub)

			shard_primary = shard_reservation.instances[0]
			shard_secondaries = shard_reservation.instances[1:reps]
			shard_inst[shard_primary] = shard_secondary
			shard_names[shard_primary.ip_address] = shard_name

		#Config DBs
		config_reservation = image.run(
			num_config, 
			num_config, 
			security_groups=[cluster_name], 
			instance_type='m1.large', 
			key_name=keypair_name, 
			user_data=config_startup)

		config_inst = config_reservation.instances
		instances = shard_inst.keys() + shard_inst.values() + config_inst

		#Wait until all instances have been started
		ec2_wait_status('running', instances)

		#Configure security group
		print "Configuring security settings"	
		ec2_config_security(mongo, instances)

		#Print instance adresses
		ec2_print_info(shard_inst, config_inst)

		#Set up mongos process
		print "Setting up mongos"	
		os.system('sh/mongos_config.sh '+config_inst[0].ip_address+' '+config_inst[1].ip_address+' '+config_inst[2].ip_address+' '+keypair_location+' >> /dev/null')

		#Configure replication sets
		print "Configuring replication sets"
		mongo_config_repl(shard_inst, shard_names)

		#Configure sharding on cluster
		print "Configuring shards"
		mongo_config_shards(shard_inst.keys(), config_inst[0], mongo)
		print "Cluster is now up"

	except EC2ResponseError:
		print "Issue making connection to Amazon"

if __name__ == "__main__":
        main()

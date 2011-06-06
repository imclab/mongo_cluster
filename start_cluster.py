#Usage: python start_cluster.py [cluster name] [number of nodes] [keypair name] [keypair location]
#AWS key and secret taken from environment variables

import sys, commands, os
from py.mongo_cluster import *
from py.ec2_cluster import *
from boto.ec2.connection import EC2Connection, EC2ResponseError

def main():

	#Load command line args & environment variables
	cluster_name = sys.argv[1]
	n = int(sys.argv[2])
	keypair_name = sys.argv[3]
	keypair_location = sys.argv[4]	
	key = os.environ['AWS_ACCESS_KEY_ID']
	secret = os.environ['AWS_SECRET_ACCESS_KEY']

	#Startup scripts for the EC2 instances
	shard_startup = open('sh/shard_startup.sh', 'r').read()
        config_startup = open('sh/config_startup.sh', 'r').read()

	#All mongo clusters must have either 1 or 3 config nodes
	num_config = 3

	#Cluster must have at least three config nodes, plus some shards
	assert n>num_config

	#Connect
	try:
                con = EC2Connection(key, secret)
	        mongo = con.create_security_group(cluster_name, 'Group for'+cluster_name+'mongo cluster')
	
		#Start EC2 instances
		print "Starting up instances"
		con = EC2Connection(key, secret)
		image = con.get_all_images(image_ids=['ami-68ad5201'])[0] #Ubuntu 11.04 Natty 64-bit Server
		shard_reservation = image.run(
			n-num_config, 
			n-num_config, 
			security_groups=[cluster_name], 
			instance_type='m1.large', 
			key_name=keypair_name, 
			user_data=shard_startup
		)
		config_reservation = image.run(
			num_config, 
			num_config, 
			security_groups=[cluster_name], 
			instance_type='m1.large', 
			key_name=keypair_name, 
			user_data=config_startup
		)
		shard_inst = shard_reservation.instances
		config_inst = config_reservation.instances
		instances = shard_inst + config_inst

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

		#Configure sharding on cluster
		print "Configuring shards"
		mongo_config_shards(shard_inst, config_inst[0], mongo)
		print "Cluster is now up"

	except EC2ResponseError:
		print "Issue making connection to Amazon"

if __name__ == "__main__":
        main()

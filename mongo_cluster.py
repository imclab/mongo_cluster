#Usage: python mongo_cluster.py [number of nodes] [gsgkeypair location]
#AWS key and secret taken from environment variables

import sys, time, commands, os
from os import environ
from boto.ec2.connection import EC2Connection, EC2ResponseError
from pymongo import Connection

def main():

	#Load command line args & environment variables
	n = int(sys.argv[1])
	keypair_location = sys.argv[2]
	key = environ['AWS_ACCESS_KEY_ID']
	secret = environ['AWS_SECRET_ACCESS_KEY']

	#Startup scripts for the EC2 instances
	shard_startup = open('sh/shard_startup.sh', 'r').read()
        config_startup = open('sh/config_startup.sh', 'r').read()

	#All mongo clusters must have either 1 or 3 config nodes
	num_config = 3

	#Cluster must have at least three config nodes, plus some shards
	assert n>num_config

	#Connect
	try:
		print "Starting up instances"
		con = EC2Connection(key, secret)
		image = con.get_all_images(image_ids=['ami-68ad5201'])[0] #Ubuntu 11.04 Natty 64-bit Server
		shard_reservation = image.run(
			n-num_config, 
			n-num_config, 
			security_groups=['mongo'], 
			instance_type='m1.large', 
			key_name='gsgkeypair', 
			user_data=shard_startup
		)
		config_reservation = image.run(
			num_config, 
			num_config, 
			security_groups=['mongo'], 
			instance_type='m1.large', 
			key_name='gsgkeypair', 
			user_data=config_startup
		)
		shard_inst = shard_reservation.instances
		config_inst = config_reservation.instances
		instances = shard_inst + config_inst

		#Wait until all instances have been started
		wait_for_status('running', instances)

		#Print instance adresses
		print "\nShards:"

	        for shard in shard_inst:
			print shard.dns_name+": "+shard.ip_address

		print "\nConfig DBs:"

		for config in config_inst:
			print config.dns_name+": "+config.ip_address

		print "\nMongos Process:\n"+config_inst[0].dns_name+": "+config_inst[0].ip_address+"\n"

		#Set up mongos process
		print "Setting up mongos"
		time.sleep(30)	
		os.system('sh/mongos_config.sh '+config_inst[0].ip_address+' '+config_inst[1].ip_address+' '+config_inst[2].ip_address+' '+keypair_location+' >> /dev/null')

		#Configure sharding on cluster
		print "Configuring shards"
		time.sleep(20)
		config_mongo_shards(shard_inst, config_inst[0])

		#Wait for input before closing down the cluster
		raw_input("Press return to close down cluster...")	

		#Terminate all instances
		for instance in instances:
			instance.terminate()
		
		wait_for_status('terminated', instances)

	except IOError:
		print "Response Error"

#Helper function for waiting until all instances are a given status
def wait_for_status(status, instances):
	ready = False
        print "Waiting for all EC2 instances to be status "+status+"..."

        while not ready:
        	ready = True

                for instance in instances:
                	instance.update()

                        if (instance.state!=status):
                        	ready = False
                time.sleep(1)

	print "All instances now of status "+status

#Connect with the mongo servers and set up cluster
def config_mongo_shards(shard_instances, mongos_instance):
	mongo_con = Connection(mongos_instance.dns_name, 27016)
	db = mongo_con['admin']

	for shard in shard_instances: 
		db.command({'addshard': str(shard.dns_name)+':27018'})

if __name__ == "__main__":
        main()

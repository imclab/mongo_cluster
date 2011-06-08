#!/usr/bin/env python
#Usage: python start_cluster.py [cluster name] [config file]
#AWS key and secret taken from environment variables

import sys, commands, os, string, itertools, json
from py.mongo_cluster import *
from py.ec2_cluster import *
from boto.ec2.connection import EC2Connection, EC2ResponseError

def main():

	#Load command line args & environment variables
	cluster_name = sys.argv[1]
	config_json = open(sys.argv[2]).read()
	config = json.loads(config_json)
	key = os.environ['AWS_ACCESS_KEY_ID']
	secret = os.environ['AWS_SECRET_ACCESS_KEY']

	#Startup scripts for the EC2 instances
	shard_startup = open('sh/shard_startup.sh', 'r').read()
        config_startup = open('sh/config_startup.sh', 'r').read()

	#All mongo clusters must have either 1 or 3 config nodes
	num_config = 3

	#No negative nodes or rep sets
	assert config['cluster']['shards']>0 and config['cluster']['replicasPerShard']>0

	#Connect
	try:
                con = EC2Connection(key, secret)
	        mongo_group = con.create_security_group(cluster_name, 'Group for'+cluster_name+'mongo cluster')
	
		#Start EC2 instances
		con = EC2Connection(key, secret)
		image = con.get_all_images(image_ids=[config['cluster']['image']])[0] #Ubuntu 11.04 Natty 64-bit Server

		#Replication DBs, by shard
		print "Starting up shard instances"
		shard_inst = {}
		shard_names = {}

		for i in range(0, config['cluster']['shards']):

			shard_name = 'set'+str(i)
			shard_startup_sub = string.replace(shard_startup, '$SETNAME', shard_name)

			shard_reservation = image.run(
				config['cluster']['replicasPerShard'], 
				config['cluster']['replicasPerShard'], 
				security_groups=[cluster_name], 
				instance_type=config['cluster']['size'], 
				key_name=config['keypair']['name'], 
				user_data=shard_startup_sub)

	                ec2_wait_status('running', shard_reservation.instances)
			shard_primary = shard_reservation.instances[0]
			shard_secondaries = shard_reservation.instances[1:config['cluster']['replicasPerShard']]
			shard_inst[shard_primary] = shard_secondaries
			shard_names[str(shard_primary.ip_address)] = shard_name

		#Config DBs
		print "Starting up config instances"
		config_reservation = image.run(
			num_config, 
			num_config, 
			security_groups=[cluster_name], 
			instance_type=config['cluster']['size'], 
			key_name=config['keypair']['name'], 
			user_data=config_startup)

		config_inst = config_reservation.instances
		instances = shard_inst.keys() + list(itertools.chain(*shard_inst.values())) + config_inst
		ec2_wait_status('running', config_inst)

		#Configure security group
		print "Configuring security settings"	
		ec2_config_security(mongo_group, instances)

		#Set up mongos process
		print "Setting up mongos"	
		mongo_start_service(config_inst[0].ip_address, config_inst[1].ip_address, config_inst[2].ip_address, config['keypair']['location'])

	        #Temporarily allow access to port 27106 (monogs) from current real ip
        	ec2_allow_local(mongo_group)

		#Configure replication sets
		print "Configuring replication sets"
		mongo_config_repl(shard_inst, shard_names, config['replication']['master'], config['replication']['slaves'])

		ec2_print_info(shard_inst, config_inst)

		#Configure sharding on cluster
		print "Configuring shards"
		mongo_config_shards(shard_inst, shard_names, config_inst[0], mongo_group)

	        #Revoke temporarily granted access
	       	ec2_deny_local(mongo_group)

                #Print instance adresses
                ec2_print_info(shard_inst, config_inst)
		print "Cluster is now up"

	except IOError:#EC2ResponseError:
		print "Issue making connection to Amazon"

if __name__ == "__main__":
        main()

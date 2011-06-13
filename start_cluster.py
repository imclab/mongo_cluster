#!/usr/bin/env python
#Usage: python start_cluster.py [cluster name] [config file]
#AWS key and secret taken from environment variables

import sys, commands, os, itertools, json, time
from boto.ec2.connection import EC2Connection, EC2ResponseError
from cluster.mongo_setup import *
from cluster.ec2_setup import *
from cluster.remote import *
from cluster.util import * 

def main():

    #Load command line args & environment variables
    cluster_name = sys.argv[1]
    config_json = open(sys.argv[2]).read()
    config = json.loads(config_json)
    key = os.environ['AWS_ACCESS_KEY_ID']
    secret = os.environ['AWS_SECRET_ACCESS_KEY']

    #Startup scripts for the EC2 instances
    startup_script = open('config/startup_script.sh', 'r').read()

    #Must have at least one shard, at least one router, and one or three config nodes
    assert len(config['cluster']['shards'])  > 0
    assert len(config['cluster']['routers']) > 0
    assert len(config['cluster']['configs']) in [1, 3]

    #Connect
    try:
        connection = EC2Connection(key, secret)
        mongo_group = connection.create_security_group(cluster_name, 'Group for '+cluster_name+' mongo cluster')
        retries = 5 #when a connection fails, retry up to retries times
    
        #Start EC2 instances
        print "Starting up EC2 instances"
        ec2_instances = ec2_launch(config['machines'], cluster_name, config['keypair']['name'], connection, startup_script)

        #Create Mongo-EC2 dicts
        config_inst = make_dict_pairs(config['cluster']['configs'], ec2_instances)
        router_inst = make_dict_pairs(config['cluster']['routers'], ec2_instances)
        shard_map = make_shard_map(config['cluster']['shards'], ec2_instances)
        shard_inst = list(itertools.chain(*shard_map.values()))

        #Gather up all instances
        instances = shard_inst + config_inst + router_inst
        ec2_wait_status('running', ec2_instances.values())

        #Set up port and ip rules for the cluster's EC2 security group
        print "Configuring security settings"
        ec2_config_security(mongo_group, ec2_instances.values()) 

        time.sleep(60)

        #Start up the mongodb routers, config dbs, and shard dbs
        print "Starting up config dbs"
        remote_start_configs(config_inst, config['keypair']['location'])
        time.sleep(20)
        print "Starting up shard dbs"
        remote_start_shards(shard_map, config['keypair']['location'])
        time.sleep(20)
        print "Starting up routers"
        remote_start_routers(router_inst, config_inst, config['keypair']['location']) 
        time.sleep(20)

        #Perform mongo driver-based configurations
        ec2_allow_local(mongo_group)

        print "Configuring replication sets"
        mongo_try(retries, mongo_config_repl, shard_map) 

        print "Configuring shards"
        mongo_try(retries, mongo_config_shards, shard_map, router_inst)
        ec2_deny_local(mongo_group)

        #Print cluster information
        ec2_print_info(shard_map, config_inst, router_inst)
        print "Cluster is now up"

    except EC2ResponseError:
        print "Issue making connection to Amazon"

if __name__ == "__main__":
        main()

#!/usr/bin/env python
#Usage: python start_cluster.py [cluster name] [config file]
#AWS key and secret taken from environment variables

import sys, commands, os, itertools, json
from boto.ec2.connection import EC2Connection, EC2ResponseError
from py.mongo_util import *
from py.ec2_util import *
from py.launch import * 

def main():

    #Load command line args & environment variables
    cluster_name = sys.argv[1]
    config_json = open(sys.argv[2]).read()
    config = json.loads(config_json)
    key = os.environ['AWS_ACCESS_KEY_ID']
    secret = os.environ['AWS_SECRET_ACCESS_KEY']

    #Startup scripts for the EC2 instances
    shard_startup = open('sh/shard_startup.sh', 'r').read()
    con_startup = open('sh/config_startup.sh', 'r').read()

    #Must have at least one shard, and must have one or three config nodes
    assert len(config['cluster']['shards']) > 0
    assert len(config['cluster']['configs']) in [1, 3]

    #Connect
    try:
        con = EC2Connection(key, secret)
        mongo_group = con.create_security_group(cluster_name, 'Group for'+cluster_name+'mongo cluster')
        retries = 5 #when a connection fails, retry up to retries times
    
        #Start EC2 instances
        con = EC2Connection(key, secret)
        image = con.get_all_images(image_ids=[config['cluster']['image']])[0] #Ubuntu 11.04 Natty 64-bit Server

        print "Starting up shard instances"
        shard_map = launch_shards(config, cluster_name, shard_startup, image)
        shard_inst = list(itertools.chain(*shard_map.values()))
        ec2_wait_status('running', shard_inst)

        print "Starting up config instances"
        config_inst = launch_configs(config, cluster_name, con_startup, image)
        ec2_wait_status('running', config_inst)

        #Gather up all instances
        instances = shard_inst + config_inst

        #Configure security groups, then ssh into the mongos instances and start mongos
        print "Configuring security settings"
        ec2_config_security(mongo_group, instances)

        print "Setting up mongos"
        mongos_inst = mongo_start_service(shard_inst, config_inst, config['keypair']['location']) 

        #Perform mongo driver-based configurations
        ec2_allow_local(mongo_group)

        print "Configuring replication sets"
        mongo_try(retries, mongo_config_repl, shard_map) 

        print "Configuring shards"
        mongo_try(retries, mongo_config_shards, shard_map, mongos_inst)
        ec2_deny_local(mongo_group)

        #Print cluster information
        ec2_print_info(shard_map, config_inst, mongos_inst)
        print "Cluster is now up"

    except IOError: #EC2ResponseError:
        print "Issue making connection to Amazon"

if __name__ == "__main__":
        main()

from pymongo import Connection
from pymongo.errors import AutoReconnect
from py.util import safe_get
import os, time, sys

#Connect with the mongos server and set up cluster
def mongo_config_shards(shard_map, mongos_inst):

    for name in shard_map.keys():
        primary_ip = shard_map[name][0]['ec2'].ip_address
        servers = primary_ip+':27018'

        for secondary in shard_map[name][1:]:
            servers = servers+','+str(secondary['ec2'].ip_address)+':27018'

        #Connect to a mongos, tell it where the shards are 
        mongos = mongos_inst[0]
        mongo_con = Connection(mongos['ec2'].ip_address, 27016)
        db = mongo_con['admin']
        db.command({'addshard': name+'/'+servers})

#Connect with each primary replication node and initiate it with its secondary nodes
def mongo_config_repl(shard_map):

    for name in shard_map.keys():
        primary_ip = shard_map[name][0]['ec2'].ip_address
        mongo_con = Connection(primary_ip, 27018, slave_okay=True)
        db = mongo_con['admin']
        config = {'_id': name}
        config_master = safe_get(shard_map[name][0]['mongo'], 'config', {})
        config_master['_id'] = 0
        config_master['host'] = primary_ip+':27018'
        members_list = [config_master]

        #Add secondaries to configuration members list
        for secondary in shard_map[name][1:]:
            config_slave = safe_get(secondary['mongo'], 'config', {})
            config_slave['_id'] = shard_map[name].index(secondary)
            config_slave['host'] = secondary['ec2'].ip_address+':27018' 
            members_list.append(config_slave)

        config['members'] = members_list
        db.command({'replSetInitiate': config})

    time.sleep(60)

#Run a function until the connection succeeds or limit is reached. 
def mongo_try(max_tries, function, *parameters):
    connected = False
    tries = 0

    while (tries<=max_tries and connected==False):

        try:
            function(*parameters)
            connected = True

        except AutoReconnect:

            if (tries==max_tries):
                print "Could not make connecton. Aborting cluster setup."
                sys.exit(1)

            else:
                tries = tries + 1
                print "Mongo connection failed in call to "+function.__name__+". Trying again... ("+str(tries)+"/"+str(max_tries)+")"
                time.sleep(15)

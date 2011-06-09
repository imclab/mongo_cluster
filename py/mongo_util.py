from pymongo import Connection
from pymongo.errors import AutoReconnect
from py.launch import safe_get
import os, time, sys

#Connect with the mongos server and set up cluster
def mongo_config_shards(shard_map, mongos_inst):

    for primary_ip in shard_map.keys():
        servers = primary_ip+':27018'

        for secondary in shard_map[primary_ip][1:]:
            servers = servers+','+str(secondary['ec2'].ip_address)+':27018'

        #Connect to a mongos, tell it where the shards are 
        mongos = mongos_inst[0]
        mongo_con = Connection(mongos['ec2'].ip_address, 27016)
        db = mongo_con['admin']
        db.command({'addshard': str(shard_map[primary_ip][0]['name'])+'/'+servers})

#Connect with each primary replication node and initiate it with its secondary nodes
def mongo_config_repl(shard_map):

    for primary_ip in shard_map.keys():
        mongo_con = Connection(primary_ip, 27018, slave_okay=True)
        db = mongo_con['admin']
        config = {'_id': str(shard_map[primary_ip][0]['name'])}
        config_master = safe_get(shard_map[primary_ip][0]['settings'], 'config', {})
        config_master['_id'] = 0
        config_master['host'] = primary_ip+':27018'
        members_list = [config_master]

        #Add secondaries to configuration members list
        for secondary in shard_map[primary_ip][1:]:
            config_slave = safe_get(secondary['settings'], 'config', {})
            config_slave['_id'] = shard_map[primary_ip].index(secondary)
            config_slave['host'] = str(secondary['ec2'].ip_address)+':27018' 
            members_list.append(config_slave)

        config['members'] = members_list
        db.command({'replSetInitiate': config})

    time.sleep(60)

#Start the mongos process
def mongo_start_service(shard_inst, config_inst, keypair_location):
    mongos_instances = []
    all_inst = shard_inst+config_inst

    for instance in all_inst:
        mongos = safe_get(instance['settings'], 'mongos', False)
        ip_address = instance['ec2'].ip_address

        if (mongos):
            mongos_instances.append(instance)

            if (str(mongos)=='True'):
                mongos = ''

            if (len(config_inst)==3):
                os.system('sh/mongos3_config.sh '+ip_address+' '+config_inst[0]['ec2'].ip_address+' '+config_inst[1]['ec2'].ip_address+' '+config_inst[2]['ec2'].ip_address+' '+keypair_location+' '+mongos+' >> /dev/null')

            else:
                os.system('sh/mongos1_config.sh '+ip_address+' '+config_inst[0]['ec2'].ip_address+' '+keypair_location+' '+mongos+' >> /dev/null')

    return mongos_instances

#Run a function until the connection succeeds or limit is reached. 
def mongo_try(max_tries, function, *parameters):
    connected = False
    tries = 0

    while (tries<=max_tries and connected==False):

        try:
            function(*parameters)
            connected = True

        except IOError:#AutoReconnect:

            if (tries==max_tries):
                print "Could not make connecton. Aborting cluster setup."
                sys.quit(1)

            else:
                tries = tries + 1
                print "Mongo connection failed in call to "+function.__name__+". Trying again... ("+str(tries)+"/"+str(max_tries)+")"
                time.sleep(15)

from pymongo import Connection
from pymongo.errors import AutoReconnect
import os, time

#Connect with the mongos server and set up cluster
def mongo_config_shards(shard_inst, shard_names, mongos_instance, mongo_group):

    #Connect to mongos, tell it where the shards are
    mongo_con = Connection(mongos_instance.ip_address, 27016)
    db = mongo_con['admin']

    for primary in shard_inst.keys():
        servers = str(primary.ip_address)+':27018'

        for secondary in shard_inst[primary]:
            servers = servers+','+str(secondary.ip_address)+':27018'

        db.command({'addshard': shard_names[str(primary.ip_address)]+'/'+servers})    

#Connect with each primary replication node and initiate it with its secondary nodes
def mongo_config_repl(shard_inst, shard_names, config_master, config_slaves):

    for primary in shard_inst.keys():    
        mongo_con = Connection(primary.ip_address, 27018, slave_okay=True)
        db = mongo_con['admin']
        config = {'_id': shard_names[str(primary.ip_address)]}
        config_master['_id'] = 0
        config_master['host'] = str(primary.ip_address)+':27018'
        members_list = [config_master]

        #Add secondaries to configuration members list
        for secondary in shard_inst[primary]:
            config_slave = config_slaves[shard_inst[primary].index(secondary)]
            config_slave['_id'] = shard_inst[primary].index(secondary)+1
            config_slave['host'] = str(secondary.ip_address)+':27018' 
            members_list.append(config_slave)

        config['members'] = members_list
        db.command({'replSetInitiate': config})

    time.sleep(60)

#Start the mongos process
def mongo_start_service(shard_inst, config_inst, keypair_location):

    for instance in shard_inst+config_inst:
        mongos = safe_get(instance['settings'], 'mongos', False)
        ip_address = instance['ec2'].ip_address

        if (mongos):
            
            if (str(mongos)=='True'):
                mongos = ''

            if (len(config_inst)==3):
                os.system('sh/mongos3_config.sh '+ip_address+' '+config_inst[0]['ec2'].ip_address+' '+config_inst[1]['ec2'].ip_address+' '+config_inst[2]['ec2'].ip_address+' '+keypair_location+' '+mongos+' >> /dev/null')

            else:
                os.system('sh/mongos1_config.sh '+ip_address+' '+configs[0].ip_address+' '+keypair_location+' '+mongos+' >> /dev/null')

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
                sys.quit(1)
            else:
                tries = tries + 1
                print "Mongo connection failed in call to "+function.__name__+". Trying again... ("+str(tries)+"/"+str(max_tries)+")"
                time.sleep(15)

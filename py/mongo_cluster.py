from pymongo import Connection
from pymongo.errors import AutoReconnect
import os, time

#Connect with the mongos server and set up cluster
def mongo_config_shards(shard_inst, shard_names, mongos_instance, mongo_group):

	connected = False
	tries = 0
	max_tries = 5

	while (tries<max_tries and connected==False):

		try:

			#Connect to mongos, tell it where the shards are
			mongo_con = Connection(mongos_instance.ip_address, 27016)
			db = mongo_con['admin']

        		for primary in shard_inst.keys():
				servers = str(primary.ip_address)+':27018'

				for secondary in shard_inst[primary]:
					servers = servers+','+str(secondary.ip_address)+':27018'

				db.command({'addshard': shard_names[str(primary.ip_address)]+'/'+servers})
				connected = True

		except AutoReconnect:
			tries = tries + 1
			print "Could not connect. Trying again... ("+str(tries)+"/"+str(max_tries)+")"
			time.sleep(15)

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
			print config_slave
			members_list.append(config_slave)

		config['members'] = members_list
		db.command({'replSetInitiate': config})

	time.sleep(60)

#Start the mongos process
def mongo_start_service(config1_ip, config2_ip, config3_ip, keypair_location):
	os.system('sh/mongos_config.sh '+config1_ip+' '+config2_ip+' '+config3_ip+' '+keypair_location+' >> /dev/null')

#Run function until connect succeeds or limit is reached
def mongo_run_connect(function, limit, *parameters):
	pass


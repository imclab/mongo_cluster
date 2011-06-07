from pymongo import Connection
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
def mongo_config_repl(shard_inst, shard_names):

        for primary in shard_inst.keys():	
		mongo_con = Connection(primary.ip_address, 27018, slave_okay=True)
		db = mongo_con['admin']
		config = {'_id': shard_names[str(primary.ip_address)]}
		members_list = [{'_id': 0, 'host': str(primary.ip_address)+':27018'}]	

		#Add secondaries to configuration members list
		for secondary in shard_inst[primary]:
			members_list.append({'_id': shard_inst[primary].index(secondary)+1, 'host': str(secondary.ip_address)+':27018'})

		config['members'] = members_list
		db.command({'replSetInitiate': config})

	time.sleep(60)

#Start the mongos process
def mongo_start_service(config1_ip, config2_ip, config3_ip, keypair_location):
	os.system('sh/mongos_config.sh '+config1_ip+' '+config2_ip+' '+config3_ip+' '+keypair_location+' >> /dev/null')

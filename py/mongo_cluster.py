from pymongo import Connection
import os

#Connect with the mongo servers and set up cluster
def mongo_config_shards(shard_instances, mongos_instance, mongo_group):

	#Temporarily allow access to port 27106 (monogs) from current real ip
        real_ip = os.popen('curl -s http://www.whatismyip.org').read()
        mongo_group.authorize('tcp', 27016, 27016, real_ip+'/32')

	#Connect to mongos, tell it where the shards are
	mongo_con = Connection(mongos_instance.ip_address, 27016)
	db = mongo_con['admin']

	for shard in shard_instances: 
		db.command({'addshard': str(shard.ip_address)+':27018'})

	#Revoke temporarily granted access
	mongo_group.revoke('tcp', 27016, 27016, real_ip+'/32')

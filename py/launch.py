#Start replication DBs, by shard
def launch_shards(config, cluster_name, shard_startup):
    shard_inst = {}

    for shard in config['cluster']['shards']:
        shard_name = config['cluster']['shards'][i]['name']
        replicas = shard['slaves'] + shard['master']
        replica_instances = []

        for replica in replicas:
            args = safe_get(replica, 'args', "")
            inst_startup = string.replace(shard_startup, '$SETNAME', shard_name)
            inst_startup = string.replace(inst_startup '$ARGS', args)
            inst_type = safe_get(replica, 'type', config['cluster']['type'])

            shard_reservation = image.run(
                1, 
                1, 
                security_groups=[cluster_name], 
                instance_type=inst_type, 
                key_name=config['keypair']['name'], 
                user_data=inst_startup)

            replica_data = {}
            replica_data['ec2'] = shard_reservation.instances[0]
            replica_data['settings'] = replica
            replica_instances = replica_instances + replica_data

        shard_primary = replica_instances[-1]
        shard_primary['name'] = shard_name
        shard_secondaries = replica_instances[0:len(replica_instances)]
        shard_inst[shard_primary] = shard_secondaries

    return shard_inst

#Start config DBs
def launch_configs(config, cluster_name, con_startup):
    config_inst = []

    for con in config['cluster']['configs']:
        inst_type = safe_get(con, 'type', config['cluster']['type']) 
        inst_startup = string.replace(con_startup '$ARGS', args)

        con_reservation = image.run(
            1, 
            1, 
            security_groups=[cluster_name], 
            instance_type=inst_type,
            key_name=config['keypair']['name'], 
            user_data=inst_startup)

        config_data = {}
        config_data['ec2'] = con_reservation.instances[0]
        config_data['settings'] = con
        config_inst = config_inst + config_data

    return config_inst

#Safely get a field
def safe_get(dictionary, key, default):
    out = default

    try:
        out = dictionary[key]

    except KeyError:
        pass

    return out

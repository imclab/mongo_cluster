#Safely get a field
def safe_get(dictionary, key, default):

    out = default

    try:
        out = dictionary[key]

    except KeyError:
        pass

    return out


#Create Mongo-EC2 dicts
def make_dict_pairs(mongo_configs, ec2_instances):

    dict_pairs = []

    for config in mongo_configs:
        inst = {}
        inst['mongo'] = config
        inst['ec2'] = ec2_instances[config['machine']]
        dict_pairs.append(inst)

    return dict_pairs

#Create dict of (shard name) => Mongo-EC2 dict pairs
def make_shard_map(shard_configs, ec2_instances):
    
    shard_map = {}

    for config in shard_configs:
        shards = [config['master']] + config['slaves']
        dict_pairs = make_dict_pairs(shards, ec2_instances)
        shard_map[config['name']] = dict_pairs
        
    return shard_map

def twirl():
    #chars = ['|', '/', '-', '\\']
    chars = [':)', ':|', ':(', ':O', ':P']

    n = 0
    while 1:
        n = (n+1)%len(chars)
        yield chars[n]

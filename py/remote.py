import subprocess
from py.util import safe_get

#Start the mongos process
def remote_start_routers(routers, configs, keypair_location):

    for router in routers:
        ip_address = router['ec2'].ip_address
        args = safe_get(router['mongo'], 'args', '')

        if (len(configs)==3):
            pass

        else:
            run = 'sudo nohup /usr/bin/mongos --port 27016 --configdb '+configs[0]['ec2'].ip_address+':27019 '+args+' &'
            process = subprocess.Popen('ssh -f -o "StrictHostKeyChecking no" -i '+keypair_location+' ubuntu@'+ip_address+' '+run, \
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

#Start mongo daemons for each shard
def remote_start_shards(shard_map, keypair_location):

    for name in shard_map.keys():

        for shard in shard_map[name]:
            ip_address = shard['ec2'].ip_address
            args = safe_get(shard['mongo'], 'args', '')
            dbpath = safe_get(shard['mongo'], 'dbpath', '/data/db')

            #Build command, ssh into server
            mkdir = 'sudo mkdir -p '+dbpath
            chmod = 'sudo chmod  777 '+dbpath
            run = 'sudo nohup /usr/bin/mongod --port 27018 --dbpath '+dbpath+' --rest --shardsvr --replSet '+name+' '+args+' > out 2> err < /dev/null &'
            command = '"'+mkdir+'&&'+chmod+'&&'+run+'"' 
            process = subprocess.Popen('ssh -f -o "StrictHostKeyChecking no" -i '+keypair_location+' ubuntu@'+ip_address+' '+command, \
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

#Start a mongo daemon for each config database
def remote_start_configs(configs, keypair_location):

    for config in configs:
        ip_address = config['ec2'].ip_address
        args = safe_get(config['mongo'], 'args', '')
        dbpath = safe_get(config['mongo'], 'dbpath', '/data/configdb')

        #Build command, ssh into server
        mkdir = 'sudo mkdir -p '+dbpath
        chmod = 'sudo chmod  777 '+dbpath
        run = 'sudo nohup /usr/bin/mongod --port 27019 --dbpath '+dbpath+' --configsvr '+args+' > out 2> err < /dev/null &'
        command = '"'+mkdir+'&&'+chmod+'&&'+run+'"' 
        process = subprocess.Popen('ssh -f -o "StrictHostKeyChecking no" -i '+keypair_location+' ubuntu@'+ip_address+' '+command, \
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

#Call an external script, given an argument list
def execute_script(location, *args):

    command = location+' '

    for arg in args:
        command = command + arg + ' '

    command = command + '>> /dev/null'
    os.system(command)

import time, os
from boto.ec2.connection import EC2Connection, EC2ResponseError

#Helper function for waiting until all instances are a given status
def ec2_wait_status(status, instances):
    ready = False

    while not ready:
        ready = True

        for instance in instances:
            instance['ec2'].update()

            if (instance['ec2'].state!=status):
                ready = False
                time.sleep(1)

#Set up mongo security group
def ec2_config_security(mongo_group, instances):
    
    for instance in instances: 
        mongo_group.authorize('tcp', 27016, 27019, instance['ec2'].ip_address+'/32')

    mongo_group.authorize('tcp', 22, 22, '0.0.0.0/0')

#Allow accesss from local real ip
def ec2_allow_local(mongo_group):
    real_ip = os.popen('curl -s http://www.whatismyip.org').read()
    mongo_group.authorize('tcp', 27016, 27019, real_ip+'/32')

#Deny access from local real ip
def ec2_deny_local(mongo_group):
    real_ip = os.popen('curl -s http://www.whatismyip.org').read()    
    mongo_group.revoke('tcp', 27016, 27019, real_ip+'/32')

#Print EC2 information
def ec2_print_info(shard_map, config_inst, mongos_inst):
    print "\nShards:"    

    for primary_ip in shard_map.keys():
        print "Replica set "+shard_map[primary_ip][0]['name']
        print "    "+shard_map[primary_ip][0]['ec2'].dns_name+": "+shard_map[primary_ip][0]['ec2'].ip_address+" <<<"        

        for secondary in shard_map[primary_ip][1:]:
            print "    "+secondary['ec2'].dns_name+": "+secondary['ec2'].ip_address

    print "\nConfig DBs:"

    for config in config_inst:
        print config['ec2'].dns_name+": "+config['ec2'].ip_address

    print "\nMongos Processes:"
    
    for mongos in mongos_inst:
        print mongos['ec2'].dns_name+": "+mongos['ec2'].ip_address+"\n"

#Terminate all EC2 instances, remove their security group
def ec2_terminate_instances(instances, group):
    
    for instance in instances:
        instance['ec2'].terminate()

    group.delete()

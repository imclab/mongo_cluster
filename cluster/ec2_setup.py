import time, os
from boto.ec2.connection import EC2Connection, EC2ResponseError
from cluster.util import safe_get

#Launch instances
def ec2_launch(machines, cluster_name, keypair, connection, startup_script):

    ec2_instances = {}

    for machine in machines:
        image = connection.get_all_images(image_ids=[machine['image']])[0]
        con_reservation = image.run(
            1,
            1,
            key_name=keypair,
            security_groups=[cluster_name],
            user_data=startup_script,
            addressing_type=safe_get(machine, 'addressing_type', None),
            instance_type=safe_get(machine, 'instance_type', 'm1.small'),
            placement=safe_get(machine, 'placement', None),
            kernel_id=safe_get(machine, 'kernel_id', None),
            ramdisk_id=safe_get(machine, 'ramdisk_id', None),
            monitoring_enabled=safe_get(machine, 'monitoring_id', None),
            subnet_id=safe_get(machine, 'subnet_id', None),
            block_device_map=safe_get(machine, 'block_device', None))

        ec2_instances[machine['name']] = con_reservation.instances[0]

    return ec2_instances

#Helper function for waiting until all instances are a given status
def ec2_wait_status(status, ec2_instances):
    ready = False

    while not ready:
        ready = True

        for instance in ec2_instances:
            instance.update()

            if (instance.state!=status):
                ready = False
                time.sleep(1)

#Set up mongo security group
def ec2_config_security(mongo_group, ec2_instances):
    
    for instance in ec2_instances: 
        mongo_group.authorize('tcp', 1, 49151, instance.ip_address+'/32')

    mongo_group.authorize('tcp', 22, 22, '0.0.0.0/0')

#Allow accesss from local real ip
def ec2_allow_local(mongo_group):
    real_ip = os.popen('curl -s http://www.whatismyip.org').read()
    mongo_group.authorize('tcp', 1, 49151, real_ip+'/32')

#Deny access from local real ip
def ec2_deny_local(mongo_group):
    real_ip = os.popen('curl -s http://www.whatismyip.org').read()    
    mongo_group.revoke('tcp', 1, 49151, real_ip+'/32')

#Print EC2 information
def ec2_print_info(shard_map, config_inst, router_inst):
    dns_chars = 35
    ip_chars = 25
    print ""    

    for name in shard_map.keys():
        print "Replica set \""+name+"\":"
        print shard_map[name][0]['ec2'].dns_name.rjust(dns_chars),
        print shard_map[name][0]['ec2'].ip_address.rjust(ip_chars),
        print "<<<".rjust(4)

        for secondary in shard_map[name][1:]:
            print secondary['ec2'].dns_name.rjust(dns_chars),
            print secondary['ec2'].ip_address.rjust(ip_chars)

    print "\nConfig DBs:"

    for config in config_inst:
        print config['ec2'].dns_name.rjust(dns_chars),
        print config['ec2'].ip_address.rjust(ip_chars)

    print "\nMongos Processes:"
    
    for mongos in router_inst:
        print mongos['ec2'].dns_name.rjust(dns_chars),
        print mongos['ec2'].ip_address.rjust(ip_chars)

    print ""

#Terminate all EC2 instances, remove their security group
def ec2_terminate_instances(instances, group):
    
    for instance in instances:
        instance.terminate()

    group.delete()

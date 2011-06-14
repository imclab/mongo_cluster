import time, os, sys
from boto.ec2.connection import EC2Connection, EC2ResponseError
from cluster.util import safe_get, twirl

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
    twirlie = twirl()

    while not ready:
        ready = True
        #sys.stdout.write('\r'+twirlie.next())
        #sys.stdout.flush() 

        for instance in ec2_instances:
            instance.update()

            if (instance.state!=status):
                ready = False
                time.sleep(1)

#Set up mongo security group
def ec2_config_security(mongo_group, instances):

    cluster_ips = set()
    cluster_ports = set()

    for instance in instances:
        cluster_ips.add(instance['ec2'].ip_address)
        cluster_ports.add(instance['mongo']['port'])

    for port in cluster_ports:
        #mongo_group.authorize('tcp', port+1000, port+1000, '0.0.0.0/0')

        for ip in cluster_ips:
            mongo_group.authorize('tcp', port, port, ip+'/32')             
  
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
    ip_chars = 30
    port_chars = 10
    print ""    

    for name in shard_map.keys():
        print "Replica set \""+name+"\":"

        for secondary in shard_map[name]:
            print secondary['ec2'].dns_name.rjust(dns_chars),
            print secondary['ec2'].ip_address.rjust(ip_chars),
            print str(secondary['mongo']['port'])

    print "\nConfig DBs:"

    for config in config_inst:
        print config['ec2'].dns_name.rjust(dns_chars),
        print config['ec2'].ip_address.rjust(ip_chars),
        print str(config['mongo']['port'])

    print "\nMongos Processes:"
    
    for mongos in router_inst:
        print mongos['ec2'].dns_name.rjust(dns_chars),
        print mongos['ec2'].ip_address.rjust(ip_chars),
        print str(mongos['mongo']['port'])

    print ""

#Terminate all EC2 instances, remove their security group
def ec2_terminate_instances(instances, group):
    
    for instance in instances:
        instance.terminate()

    group.delete()

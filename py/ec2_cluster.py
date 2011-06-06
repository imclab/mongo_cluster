import time, os
from boto.ec2.connection import EC2Connection, EC2ResponseError

#Helper function for waiting until all instances are a given status
def ec2_wait_status(status, instances):
	ready = False
        print "Waiting for all EC2 instances to be status "+status+"..."

        while not ready:
        	ready = True

                for instance in instances:
                	instance.update()

                        if (instance.state!=status):
                        	ready = False
                time.sleep(1)

	print "All instances now of status "+status

#Set up mongo securty group
def ec2_config_security(mongo, instances):
	
	#Any machine in the cluster can speak with others via mongo ports (27016-27019)
	for instance in instances:
		mongo.authorize('tcp', 27016, 27019, instance.ip_address+'/32')

	mongo.authorize('tcp', 22, 22, '0.0.0.0/0')

#Print EC2 information
def ec2_print_info(shard_inst, config_inst):
        print "\nShards:"

        for shard in shard_inst:
        	print shard.dns_name+": "+shard.ip_address

        print "\nConfig DBs:"

        for config in config_inst:
        	print config.dns_name+": "+config.ip_address

	print "\nMongos Process:\n"+config_inst[0].dns_name+": "+config_inst[0].ip_address+"\n"

#Terminate all EC2 instances, remove their security group
def ec2_terminate_instances(instances, group):
	
	for instance in instances:
		instance.terminate()

	group.delete()

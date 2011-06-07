import time, os
from boto.ec2.connection import EC2Connection, EC2ResponseError

#Helper function for waiting until all instances are a given status
def ec2_wait_status(status, instances):
	ready = False

        while not ready:
        	ready = True

                for instance in instances:
                	instance.update()

                        if (instance.state!=status):
                        	ready = False
                time.sleep(1)

#Set up mongo security group
def ec2_config_security(mongo_group, instances):
	
	#Any machine in the cluster can speak with others via mongo ports (27016-27019)
	for instance in instances:
		mongo_group.authorize('tcp', 27016, 27019, instance.ip_address+'/32')

	mongo_group.authorize('tcp', 22, 22, '0.0.0.0/0')

#Allow accesss from local real ip
def ec2_allow_local(mongo_group):
        real_ip = os.popen('curl -s http://www.whatismyip.org').read()
        mongo_group.authorize('tcp', 27016, 27019, real_ip+'/32')

#Deny access from ip
def ec2_deny_local(mongo_group):
        real_ip = os.popen('curl -s http://www.whatismyip.org').read()	
        mongo_group.revoke('tcp', 27016, 27019, real_ip+'/32')

#Print EC2 information
def ec2_print_info(shard_inst, config_inst):
        print "\nShards:"	

        for primary in shard_inst.keys():
		print "Replica set "+str(shard_inst.keys().index(primary))+":"
        	print "    "+primary.dns_name+": "+primary.ip_address+" <<<"		

		for secondary in shard_inst[primary]:
			print "    "+secondary.dns_name+": "+secondary.ip_address

        print "\nConfig DBs:"

        for config in config_inst:
        	print config.dns_name+": "+config.ip_address

	print "\nMongos Process:\n"+config_inst[0].dns_name+": "+config_inst[0].ip_address+"\n"

#Terminate all EC2 instances, remove their security group
def ec2_terminate_instances(instances, group):
	
	for instance in instances:
		instance.terminate()

	group.delete()

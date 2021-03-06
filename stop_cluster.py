#!/usr/bin/env python
#Usage: python stop_cluster.py [cluster name]
#AWS key and secret taken from environment variables

import sys, os
from cluster.ec2_setup import *
from boto.ec2.connection import EC2Connection, EC2ResponseError

def main():

    #Load command line args & environment variables
    cluster_name = sys.argv[1]
    key = os.environ['AWS_ACCESS_KEY_ID']
    secret = os.environ['AWS_SECRET_ACCESS_KEY']

    #Connect
    try:
        con = EC2Connection(key, secret)

        #Find the security group object for the given 
        for group in con.get_all_security_groups():

            if group.name==cluster_name:
                mongo_group = group

        try:        
            ec2_instances = mongo_group.instances()

            #Terminate all instances
            print "Terminating all instances"
            ec2_terminate_instances(ec2_instances, mongo_group)
            ec2_wait_status('terminated', ec2_instances)

        except NameError:
            print "No cluster with name \""+cluster_name+"\" exists." 

    except EC2ResponseError:
        print "Issue making connection to Amazon"

if __name__ == "__main__":
        main()

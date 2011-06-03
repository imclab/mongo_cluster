#!/bin/bash
mongos1=$1
mongos2=$2
mongos3=$3
ssh -o "StrictHostKeyChecking no" -i ../ec2-api-tools-1.4.3.0/id_rsa-gsg-keypair ubuntu@$mongos1 "sudo nohup /usr/bin/mongos --port 27016 --configdb ${mongos1}:27019,${mongos2}:27019,${mongos3}:27019 &" &

#!/bin/bash
config1=$1
config2=$2
config3=$3
keypair=$4
sleep 30
ssh -o "StrictHostKeyChecking no" -i $keypair ubuntu@$config1 "sudo nohup /usr/bin/mongos --port 27016 --configdb ${config1}:27019,${config2}:27019,${config3}:27019 &" &
sleep 20

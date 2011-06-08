#!/bin/bash
server=$1
config1=$2
config2=$3
config3=$4
keypair=$5
args=$6
sleep 30
ssh -o "StrictHostKeyChecking no" -i $keypair ubuntu@$server "sudo nohup /usr/bin/mongos --port 27016 --configdb ${config1}:27019,${config2}:27019,${config3}:27019 $args  &" &
sleep 20

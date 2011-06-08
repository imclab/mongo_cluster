#!/bin/bash
server=$1
config=$2
keypair=$3
args=$4
sleep 30
ssh -o "StrictHostKeyChecking no" -i $keypair ubuntu@$server "sudo nohup /usr/bin/mongos --port 27016 --configdb ${config}:27019 $args  &" &
sleep 20

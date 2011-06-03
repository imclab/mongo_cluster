#!/bin/bash
#A single Mongo shard
sudo apt-get -y install mongodb
sudo mkdir -p /data/db
sudo chmod -R 777 /data
sudo iptables -A INPUT -p tcp --dport 27018 -j ACCEPT
sudo nohup `which mongod` --shardsvr &

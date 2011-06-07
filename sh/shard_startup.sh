#!/bin/bash
#A single Mongo shard
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10
sudo chmod 777 /etc/apt/sources.list
echo "deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen" >> /etc/apt/sources.list
sudo apt-get update 
sudo apt-get -y install mongodb-10gen
sudo mkdir -p /data/db
sudo chmod -R 777 /data
#sudo iptables -A INPUT -p tcp --dport 27018 -j ACCEPT
sudo nohup `which mongod` --rest --shardsvr --replSet $SETNAME &

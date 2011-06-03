#!/bin/bash
#A node which doubles as the config db and mongos
sudo apt-get -y install mongodb
sudo mkdir -p /data/configdb
sudo mkdir -p /data/db
sudo chmod -R 777 /data
sudo iptables -A INPUT -p tcp --dport 27016 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 27017 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 27019 -j ACCEPT
sudo nohup `which mongod` --configsvr --port 27019 &

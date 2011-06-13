#!/bin/bash
#Install mongodb
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10
sudo chmod 777 /etc/apt/sources.list
echo "deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen" >> /etc/apt/sources.list
sudo apt-get update 
sudo apt-get -y install mongodb-10gen
killall mongod

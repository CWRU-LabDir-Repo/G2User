#!/bin/bash
# 23:45 crontab job for root 
date
echo crontab 23:45 job - make /G2User/ safe github dir
git config --global --add safe.directory /home/pi/G2User
cd /home/pi/G2User/
git fetch
git reset --hard HEAD
git merge '@{u}'


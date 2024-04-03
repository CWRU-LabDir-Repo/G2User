#!/bin/bash
# 23:45 crontab job for root 
date
echo crontab 23:45 job - pull in repo exact copy and fix crontab job for g2plot
cd /home/pi/G2User/
git fetch
git reset --hard HEAD
git merge '@{u}'


#!/bin/bash
# 23:45 crontab job for root 
date
echo crontab 23:45 job - Hello!

echo Fix crontabs for g2plot
/home/pi/G2User/g2plot-crontab-fix.sh

echo Installing autostart
cp -p /home/pi/G2User/autostart /home/pi/.config/lxsession/LXDE-pi

echo crontab 23:45 job done

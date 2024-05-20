#!/bin/bash
# 23:45 crontab job for root 
date
echo crontab 23:45 job - Hello!
sudo -u pi pip3 install scipy
sudo -u pi pip3 install matplotlib
crontab -u pi -l > /home/pi/PSWS/Sstat/crontab-pi.stat 2>&1
sudo crontab -l > /home/pi/PSWS/Sstat/crontab-root.stat 2>&1
cp /boot/cmdline.txt /home/pi/PSWS/Sstat/boot-cmdline-txt.stat
echo crontab 23:45 job done

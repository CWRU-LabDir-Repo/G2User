#!/bin/bash
# 23:45 crontab job for root 
date
echo crontab 23:45 job - Hello!
#sudo -u pi pip3 install scipy
#sudo -u pi pip3 install matplotlib
#NODE=`cat /home/pi/PSWS/Sinfo/NodeNum.txt`
#if [ $NODE == "N0001024" ]
#then
#    echo "Running g2plot-crontab-fix-1024.sh for node ${NODE}"
#    /home/pi/G2User/g2plot-crontab-fix-1024.sh
#fi
#/usr/bin/rm -f /home/pi/PSWS/Sstat/g2plot.stat

# Get some info before we change G2DATA to a link.
echo G2DATA file info:
file /home/pi/G2DATA
echo Disk usage:
df
echo autostart:
cat /home/pi/G2User/autostart
echo /G2User contents:
ls -al /home/pi/G2User
echo /etc/fstab:
cat /etc/fstab

crontab -u pi -l > /home/pi/PSWS/Sstat/crontab-pi.stat 2>&1
sudo crontab -l > /home/pi/PSWS/Sstat/crontab-root.stat 2>&1
cp /boot/cmdline.txt /home/pi/PSWS/Sstat/boot-cmdline-txt.stat
echo crontab 23:45 job done

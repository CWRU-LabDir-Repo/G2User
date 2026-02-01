#!/bin/bash
# 23:45 crontab job for root 
date
echo crontab 23:45 job - Hello!
echo

NODE=`cat /home/pi/PSWS/Sinfo/NodeNum.txt`
echo This is Grape2 NODE $NODE
echo

echo Checking OS release:
cat /etc/os-release
echo

echo Checking /etc/apt/sources.list:
cat /etc/apt/sources.list
echo

echo Checking lftp installed:
CMD=lftp
which $CMD
if [ $? == 0 ]
then
    echo $CMD found, not installing
else
    echo $CMD not found, installing
    sudo apt install $CMD
fi
echo

#if [ $NODE == "N0001002" ]
#then
#echo "Running git-crontab-fix.sh for node ${NODE}"
#/home/pi/G2User/git-crontab-fix.sh
#fi

# Add the preswap alias
#grep preswap /home/pi/.bashrc
#if [ $? != 0 ]
#then
#    sudo -u pi sed -i -e '$a \
#\
#alias preswap="sudo /home/pi/G2User/preswap.sh 2>&1 | sudo tee -a /home/pi/preswap.stat; sudo mv /home/pi/preswap.stat /home/pi/PSWS/Sstat"' /home/pi/.bashrc
#fi

# Activate the new autostart script
#sudo -u pi cp -p /home/pi/G2User/autostart /home/pi/.config/lxsession/LXDE-pi

# Get some info before we change G2DATA to a link.
#echo G2DATA file info:
#file /home/pi/G2DATA

echo Checking disk usage:
/usr/bin/df -lh
echo

#echo autostart installed
#cat /home/pi/.config/lxsession/LXDE-pi/autostart
#echo /G2User contents
#ls -al /home/pi/G2User
#echo /etc/fstab
#cat /etc/fstab

echo Checking G2DATA entry in /etc/fstab:
grep G2DATA /etc/fstab
echo

#echo .bashrc
#cat /home/pi/.bashrc
echo Checking external drives:
/usr/bin/df | grep "/dev/sd"
echo

echo Logging pi user crontab
crontab -u pi -l > /home/pi/PSWS/Sstat/crontab-pi.stat 2>&1
echo Logging root user crontab
sudo crontab -l > /home/pi/PSWS/Sstat/crontab-root.stat 2>&1
echo

#cp /boot/cmdline.txt /home/pi/PSWS/Sstat/boot-cmdline-txt.stat
echo crontab 23:45 job done

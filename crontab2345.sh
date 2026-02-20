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

echo Checking the preswap alias:
grep preswap /home/pi/.bashrc
if [ $? != 0 ]
then
    sudo -u pi sed -i -e '$a \
\
alias preswap="sudo /home/pi/G2User/preswap.sh 2>&1 | sudo tee -a /home/pi/preswap.stat; sudo mv /home/pi/preswap.stat /home/pi/PSWS/Sstat"' /home/pi/.bashrc
    echo Added the preswap alias
else
    echo Preswap alias is present
fi
echo

#echo .bashrc contents:
#cat /home/pi/.bashrc
#echo

# Always replace the autostart script in case user changed it
echo Replacing autostart script
sudo -u pi cp -p -v /home/pi/G2User/autostart /home/pi/.config/lxsession/LXDE-pi
echo

#echo autostart installed
#cat /home/pi/.config/lxsession/LXDE-pi/autostart

echo G2DATA file info:
file /home/pi/G2DATA
echo

echo Contents of /home/pi/G2User:
ls -al /home/pi/G2User
echo

echo Contents of /etc/fstab:
cat /etc/fstab
echo

echo Checking G2DATA entry in /etc/fstab:
grep G2DATA /etc/fstab
echo

echo Checking disk usage:
/usr/bin/df -lh
echo

echo Checking external drives:
/usr/bin/df | grep "/dev/sd"
echo

echo Logging pi user crontab
crontab -u pi -l > /home/pi/PSWS/Sstat/crontab-pi.stat 2>&1
echo Logging root user crontab
crontab -l > /home/pi/PSWS/Sstat/crontab-root.stat 2>&1
echo Logging cmdline.txt
cp /boot/cmdline.txt /home/pi/PSWS/Sstat/boot-cmdline-txt.stat

echo

echo crontab 23:45 job done

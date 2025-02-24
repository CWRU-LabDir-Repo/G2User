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

# Add the preswap alias
grep preswap /home/pi/.bashrc
if [ $? != 0 ]
then
    sudo -u pi sed -i -e '$a \
\
alias preswap="sudo /home/pi/G2User/preswap.sh 2>&1 | sudo tee -a /home/pi/preswap.stat; sudo mv /home/pi/preswap.stat /home/pi/PSWS/Sstat"' /home/pi/.bashrc
fi

# Activate the new autostart script
sudo -u pi cp -p /home/pi/G2User/autostart /home/pi/.config/lxsession/LXDE-pi

# Get some info before we change G2DATA to a link.
echo G2DATA file info:
file /home/pi/G2DATA
echo Disk usage
/usr/bin/df
echo autostart installed
cat /home/pi/.config/lxsession/LXDE-pi/autostart
echo /G2User contents
ls -al /home/pi/G2User
echo /etc/fstab
cat /etc/fstab
echo .bashrc
cat /home/pi/.bashrc

crontab -u pi -l > /home/pi/PSWS/Sstat/crontab-pi.stat 2>&1
sudo crontab -l > /home/pi/PSWS/Sstat/crontab-root.stat 2>&1
cp /boot/cmdline.txt /home/pi/PSWS/Sstat/boot-cmdline-txt.stat
echo crontab 23:45 job done

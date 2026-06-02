#!/bin/bash
# 23:45 crontab job for root 
#
# NOTE: this script always runs as root, so any command that changes
# a file owned by the pi user must be preceded by "sudo -u pi".
#

date
echo Crontab 23:45 job
echo

NODE=`cat /home/pi/PSWS/Sinfo/NodeNum.txt`
echo This is Grape2 NODE $NODE
echo

echo "---------------------------------------------"
echo Checking OS release:
echo "---------------------------------------------"
cat /etc/os-release
echo

echo "---------------------------------------------"
echo Checking /etc/apt/sources.list:
echo "---------------------------------------------"
cat /etc/apt/sources.list
echo

echo "---------------------------------------------"
echo Checking lftp installed:
echo "---------------------------------------------"
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

echo "---------------------------------------------"
echo "Checking crontab fix for node ${NODE}:"
echo "---------------------------------------------"
/home/pi/G2User/git-crontab-fix.sh
echo

echo "---------------------------------------------"
echo "Checking debug level for node ${NODE}:"
echo "---------------------------------------------"
/home/pi/G2User/check-dbg-level.sh
echo

echo "---------------------------------------------"
echo "Checking aliases:"
echo "---------------------------------------------"
sudo -u pi /home/pi/G2User/check-aliases.sh
echo

# Always replace the autostart script in case user has changed it
echo "---------------------------------------------"
echo Replacing autostart script
echo "---------------------------------------------"
sudo -u pi cp -p -v /home/pi/G2User/autostart /home/pi/.config/lxsession/LXDE-pi
echo

echo "---------------------------------------------"
echo autostart installed:
echo "---------------------------------------------"
cat /home/pi/.config/lxsession/LXDE-pi/autostart
echo

echo "---------------------------------------------"
echo G2DATA file info:
echo "---------------------------------------------"
file /home/pi/G2DATA
echo

echo "---------------------------------------------"
echo Contents of /home/pi/G2User:
echo "---------------------------------------------"
ls -al /home/pi/G2User
echo

echo "---------------------------------------------"
echo Contents of /home/pi/G2User/ondeck:
echo "---------------------------------------------"
ls -al /home/pi/G2User/ondeck
echo

echo "---------------------------------------------"
echo Contents of /etc/fstab:
echo "---------------------------------------------"
cat /etc/fstab
echo

echo "---------------------------------------------"
echo Checking G2DATA entry in /etc/fstab:
echo "---------------------------------------------"
grep G2DATA /etc/fstab
echo

echo "---------------------------------------------"
echo Checking disk usage:
echo "---------------------------------------------"
/usr/bin/df -lh
echo

echo "---------------------------------------------"
echo Checking external drives:
echo "---------------------------------------------"
/usr/bin/df | grep "/dev/sd"
echo

echo "---------------------------------------------"
echo Logging system config:
echo "---------------------------------------------"
echo Logging pi user crontab
crontab -u pi -l > /home/pi/PSWS/Sstat/crontab-pi.stat 2>&1
echo Logging root user crontab
crontab -l > /home/pi/PSWS/Sstat/crontab-root.stat 2>&1
echo Logging cmdline.txt
cp --remove-destination --no-preserve=mode /boot/cmdline.txt /home/pi/PSWS/Sstat/boot-cmdline-txt.stat
echo Logging config.txt
cp --remove-destination --no-preserve=mode /boot/config.txt /home/pi/PSWS/Sstat/boot-config-txt.stat
echo Logging meshagent status
systemctl status meshagent > /home/pi/PSWS/Sstat/mesh_agent_status.stat 2>&1
echo

echo "---------------------------------------------"
echo Checking for restart:
echo "---------------------------------------------"
grep -q "Already up to date" /home/pi/PSWS/Sstat/githubpull.stat
UCODE=$?
if [ $UCODE != 0 ]
then
    grep -q "[no restart]" /home/pi/PSWS/Sstat/githubpull.stat
    UCODE=$?
    if [ $UCODE != 0 ]
    then
        RFLAG=/home/pi/PSWS/Scmd/restartcon
        echo "Setting flag to update executables and restart G2console"
        touch $RFLAG
        echo "Launching task to patch file headers"
        python3 /home/pi/G2User/patch_headers.py > /home/pi/PSWS/Sstat/patch_headers.stat 2>&1 &
    else
        echo "Executables not affected, no restart required"
    fi
else
    echo "Already up to date, no restart required"
fi
echo

echo crontab 23:45 job done

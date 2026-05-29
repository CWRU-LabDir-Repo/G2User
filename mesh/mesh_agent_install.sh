#!/bin/bash
#
# Install meshagent.
# Force OS kernel to run in 32-bit mode.
#

date
echo $0

cd /home/pi/G2User/mesh

wget -O meshagent "https://meshcentral.hamsci.org/meshagents?id=ly1G3oztYf6NU1W8zZXm11rv%400nw3KZVPFuhiU6vG3q8V6bSkzIfGwDGtW78R0l2&installflags=0&meshinstall=25"
chmod +x meshagent
sudo ./meshagent -install

grep -q 'arm_64bit=0' /boot/config.txt
if [ $? == 0 ]
then
    echo "32-bit kernel mode already set"
else
    echo "Setting 32-bit kernel mode"
    sudo cp -a /boot/config.txt /boot/config.txt.64bit.bak
    echo 'arm_64bit=0' | sudo tee -a /boot/config.txt
    echo "Rebooting"
    sudo reboot now
fi


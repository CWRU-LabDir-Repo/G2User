#!/bin/bash -e
# The "-e" option will cause this script to exit on any error.
# Job to fix crontab entry for g2plot.sh
date
echo 'Grape 2 fix g2plot.sh crontab entry'

# work in Stemp
push=`pwd`
cd /home/pi/PSWS/Stemp

# save existing root crontab to a file
sudo crontab -l > crontab-root

# edit crontab file to remove the "/bin/python3 " string from the g2plot.sh entry
sed 's/\/bin\/python3 \/home\/pi\/G2User\/g2plot.sh/\/home\/pi\/G2User\/g2plot.sh/' < crontab-root > crontab-root-fixed

# replace crontab with the fixed file
sudo crontab crontab-root-fixed

# clean up
sudo rm -f crontab-root crontab-root-fixed
cd $push

echo 'Fixed g2plot.sh crontab entry'


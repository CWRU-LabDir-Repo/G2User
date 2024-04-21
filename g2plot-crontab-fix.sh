#!/bin/bash
# Job to fix crontab entries for g2plot.sh
# OK to run more than once.
# AB1XB 24-04-21

date
echo 'Grape 2 fix crontab entries for g2plot.sh'

# work in Stemp
push=`pwd`
cd /home/pi/PSWS/Stemp

# save existing pi and root crontabs to files
echo "getting existing crontab files"
crontab -u pi -l > crontab-pi
sudo crontab -l > crontab-root

# edit root crontab file to delete the 2 lines for the g2plot.sh entry
echo "editing crontab-root"
sed '/00:03 Creates plots/,/03 00 * * */d' crontab-root > crontab-root-fixed

# replace root crontab with the fixed file
echo "replacing crontab-root"
sudo crontab crontab-root-fixed

# search for an existing g2plot entry in the pi crontab so we add it only once
echo "searching for g2plot.sh in crontab-pi"
grep -q "g2plot.sh" crontab-pi
if [ $? == 1 ]
then
# entry not found, edit pi crontab file to add the 2 lines for the g2plot.sh entry
echo "editing crontab-pi"
sed '/# 23:30/i \
# 00:03 Creates plots of 3 radio files data\
03 00 * * * /home/pi/G2User/g2plot.sh >/home/pi/PSWS/Sstat/g2plot.stat 2>&1' crontab-pi > crontab-pi-fixed
# replace pi crontab with the fixed file
echo "replacing crontab-pi"
crontab -u pi crontab-pi-fixed
else
    echo "g2plot.sh already found in crontab-pi"
fi

# clean up
sudo rm -f crontab-pi crontab-pi-fixed
sudo rm -f crontab-root crontab-root-fixed
cd $push

echo 'Fixed crontab entries for g2plot.sh'

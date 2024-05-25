#!/bin/bash
# Job to fix N0001024 crontab entries for g2plot.sh
# OK to run more than once.
# AB1XB 24-05-25

date
echo 'Grape 2 fix N0001024 crontab entries for g2plot.sh'

# verify node
NODE=`cat /home/pi/PSWS/Sinfo/NodeNum.txt`
if [ $NODE != "N0001024" ]
then
    echo "This is not node ${NODE}, exiting"
    exit 0
fi

# work in Stemp
push=`pwd`
cd /home/pi/PSWS/Stemp

# save existing pi and root crontabs to files
echo "getting existing crontab files"
crontab -u pi -l > crontab-pi
sudo crontab -l > crontab-root

# edit root crontab file to delete the extra comment
echo "editing crontab-root"
sed '/00:03 Creates plots/d' crontab-root > crontab-root-fixed

# replace root crontab with the fixed file
echo "replacing crontab-root"
sudo crontab crontab-root-fixed

# search for error entry in the pi crontab so we replace it only once
echo "searching for error in crontab-pi"
grep -q "11" crontab-pi
if [ $? == 0 ]
then
# entry found, edit pi crontab file to replace all entries
echo "found error in crontab-pi, now fixing"
sed '/# 23:30/,/03 00 * * */d' crontab-pi > crontab-pi-fixed
sed -i -e '$a \
# 00:03 Creates plots of 3 radio files data\
03 00 * * * /home/pi/G2User/g2plot.sh >/home/pi/PSWS/Sstat/g2plot.stat 2>&1\
# 23:30 do daily git pull from /G2User/ repo to update local system\
30 23 * * * cd /home/pi/G2User/; git pull  >/home/pi/PSWS/Sstat/githubpull.stat 2>&1' crontab-pi-fixed
# replace pi crontab with the fixed file
echo "replacing crontab-pi"
crontab -u pi crontab-pi-fixed
else
    echo "crontab-pi is already fixed"
fi

# clean up
sudo rm -f crontab-pi crontab-pi-fixed
sudo rm -f crontab-root crontab-root-fixed
cd $push

echo 'Fixed N0001024 crontab entries for g2plot.sh'

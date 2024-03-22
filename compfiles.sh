#!/bin/bash -e
# 00:10 crontab job to compress all files to be xferred to WWVARC repo
date
echo 'Grape 2 compress files shell script'
cd /home/pi/G2DATA/Sxfer

DATE=`date +%Y-%m-%d --date="1 day ago"`
NODE=`cat /home/pi/PSWS/Sinfo/NodeNum.txt`
PATTERN=${DATE}T000000Z_${NODE}

# zip all daily files for transfer
time /usr/bin/zip -m ${PATTERN} ${PATTERN}*

# gzip daily dc log file for long term storage
/usr/bin/gzip /home/pi/G2DATA/Slogs/${PATTERN}_DC.log

echo Compress files script ended


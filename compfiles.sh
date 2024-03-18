#!/bin/bash -e
# 00:10 crontab job to compress all files to be xferred to WWVARC repo 
date
echo 'Grape 2 compress files shell script'
cd /home/pi/G2DATA/Sxfer

DATE=`date +%Y-%m-%d --date="1 day ago"`
NODE=`cat /home/pi/PSWS/Sinfo/NodeNum.txt`
ZIPFILE=${DATE}T000000Z_${NODE}

time /usr/bin/zip -m ${ZIPFILE} *

echo Compress files script ended


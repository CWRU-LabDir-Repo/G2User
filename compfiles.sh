#!/bin/bash
# 00:10 crontab job to compress all files to be xferred to WWVARC repo
date
echo 'Grape 2 compress files shell script'
cd /home/pi/G2DATA/Sxfer

DATE=`date +%Y-%m-%d --date="1 day ago"`
NODE=`cat /home/pi/PSWS/Sinfo/NodeNum.txt`
PATTERN=${DATE}T000000Z_${NODE}

# gzip daily dc log file for long term storage
/usr/bin/gzip /home/pi/G2DATA/Slogs/${PATTERN}_DC.log

# zip all daily csv files for transfer
time /usr/bin/zip -m ${PATTERN} ${PATTERN}*.csv ${PATTERN}*.preswap

# zip all daily log files for transfer
# compfiles.stat will be truncated because we are currently redirecting to it.
time /usr/bin/zip ${PATTERN}_logs ${PATTERN}*.log /home/pi/PSWS/Sstat/*.stat
/usr/bin/rm -f ${PATTERN}*.log

echo Compress files script ended


#!/bin/bash
# 00:10 crontab job to compress all files to be xferred to WWVARC repo
date
echo 'Grape 2 compress files shell script'
cd /home/pi/G2DATA/Sxfer

if [[ "$1" == "" ]]
then
    DDIFF="1 day ago"
else
    DDIFF="$1"
fi
DATE=`date +%Y-%m-%d --date="$DDIFF"`
NODE=`cat /home/pi/PSWS/Sinfo/NodeNum.txt`
PATTERN=${DATE}T000000Z_${NODE}

# Compress the daily log files for short term storage in Slogs.
/usr/bin/gzip /home/pi/G2DATA/Slogs/${PATTERN}_DC.log
/usr/bin/gzip /home/pi/G2DATA/Slogs/${PATTERN}_console.log
/usr/bin/gzip /home/pi/G2DATA/Slogs/${PATTERN}_magdata.log

# Compress the daily data files copied to the Sxfer directory by files2xfer.py.
/usr/bin/zip -m ${PATTERN} ${PATTERN}*.csv

# Compress the daily log files copied to the Sxfer directory by files2xfer.py.
# Note: compfiles.stat will be truncated because we are currently redirecting to it.
/usr/bin/zip ${PATTERN}_logs ${PATTERN}*.log /home/pi/PSWS/Sstat/*.stat
/usr/bin/rm -f ${PATTERN}*.log

echo Compress files script ended


#!/bin/bash
# 00:10 crontab job to compress log files to be xferred to PSWS repo
#
# Note: redirect output to a temporary file, complogs.txt, which will be renamed complogs.stat
# and added to the zip file after script (almost) completes.

# Work in G2DATA/Sxfer
cd /home/pi/G2DATA/Sxfer

# Temporary name for this script's log
LOG=complogs.txt

date > $LOG 2>&1
echo 'Grape 2 compress logs script' >> $LOG 2>&1

if [[ "$1" == "" ]]
then
    DDIFF="1 day ago"
else
    DDIFF="$1"
fi
DATE=`date +%Y-%m-%d --date="$DDIFF"`
NODE=`cat /home/pi/PSWS/Sinfo/NodeNum.txt`
PATTERN=${DATE}T000000Z_${NODE}

# Copy the log files in PSWS/Sstat to Sxfer directory
/usr/bin/cp -pv /home/pi/PSWS/Sstat/*.stat . >> $LOG 2>&1

# Compress the log files copied to the Sxfer directory by files2xfer.py and the above comand
/usr/bin/zip ${PATTERN}_logs.zip ${PATTERN}*.log *.stat >> $LOG 2>&1

# Remove the logs that are now in the logs.zip file
/usr/bin/rm -f ${PATTERN}*.log >> $LOG 2>&1
/usr/bin/rm -f *.stat >> $LOG 2>&1

# Remove the original logs
/usr/bin/rm -f /home/pi/G2DATA/Slogs/${PATTERN}*.log >> $LOG 2>&1

# Rename log file output from this script and add it to the logs.zip file
/usr/bin/mv $LOG complogs.stat
/usr/bin/zip ${PATTERN}_logs.zip complogs.stat
/usr/bin/mv complogs.stat /home/pi/PSWS/Sstat

# Copy logs.zip file back into G2DATA/Slogs for short-term storage
/usr/bin/cp -pv ${PATTERN}_logs.zip /home/pi/G2DATA/Slogs

echo Compress logs script ended


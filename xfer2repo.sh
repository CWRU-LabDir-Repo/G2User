#!/bin/bash
# xfer2repo.sh - bash script to transfer the daily created data files from a Grape1 PSWS to the main repo
# 1-29-2022 Ver 1.00 by KD8CGH / N8OBJ
# 2-23-2022 Ver 1.01 N8OBJ Changed repo stuff again
# 3-30-2022 Ver 1.02 N8OBJ added 'verbosity'
# 2-24-2024 Ver 1.03 N8OBJ added new /G2DATA/Sxfer directory

ls -1 /home/pi/G2DATA/Sxfer/ > /home/pi/PSWS/Stemp/sflist
awk '{print "/home/pi/G2DATA/Sxfer/" $0}' /home/pi/PSWS/Stemp/sflist > /home/pi/PSWS/Stemp/go2repo
echo 'Files to send to Repo:'
cat /home/pi/PSWS/Stemp/go2repo
echo 'Attempting xfer to repo...'
if (< /home/pi/PSWS/Stemp/go2repo xargs -I %  curl -v -u "grape@wwvarc.org:5F3gjdEKEt" -T "{%}" ftp://208.109.41.230/);
then
    echo 'Files transferred ok - removing them from ~/G2DATA/Sxfer/'; rm /home/pi/G2DATA/Sxfer/*;
else
    echo 'File xfer failed - leaving files in ~/G2DATA/SXfer/ for next try tomorrow';
fi

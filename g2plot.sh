#!/bin/bash
date
echo 'Grape 2 plot files shell script '
/bin/find /home/pi/G2DATA/SdataR* -type f -name "$(date -d '1 day ago' +'%Y-%m-%d')*" | /bin/python3 /home/pi/G2User/g2plot.py >/home/pi/PSWS/Sstat/g2plot.stat 2>&1

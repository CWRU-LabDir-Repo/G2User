#!/bin/bash
cd /home/pi/G2User/
echo 'Manual update of /G2User/ from cmd line'
git pull > /home/pi/PSWS/Sstat/urG2User.stat 2>&1
date

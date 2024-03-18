#!/bin/bash
date
cd /home/pi/G2User/
echo 'Manual update of /G2User/ from cmd line'
git pull
ls -al ondeck/
mv ondeck/* .

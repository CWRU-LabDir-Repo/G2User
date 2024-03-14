#!/bin/bash
date
cd /home/pi/G2User/
echo 'Manual update of /G2User/ from cmd line'
git pull
mv ondeck/* .

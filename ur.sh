#!/bin/bash
date
cd /home/pi/G2User/
echo 'Manual update of /G2User/ from cmd line'
git fetch
git reset --hard HEAD
git merge '@{u}'
ls -al ondeck/
sudo mv ondeck/* .

#!/bin/bash
# pull image of read-only repo
date
cd /home/pi/G2User/
git fetch
git reset --hard HEAD
git merge '@{u}'

#!/bin/bash
# pull image of read-only repo
date
cd /home/pi/G2User/
git fetch
git reset --hard HEAD
git merge '@{u}'

# restore file modification times
git restore-mtime
code=$?
if [ $code != 0 ]
then
    echo "git-restore-mtime not installed, installing now"
    sudo apt install git-restore-mtime
    git restore-mtime
fi


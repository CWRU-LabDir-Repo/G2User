#!/bin/bash
# git-crontab-fix.sh
# Replace the pi user's crontab git pull commands with git fetch/reset/merge commands.

# read pi crontab into a file
crontab -u pi -l > crontab-pi

# Search for tag in the crontab file
echo "Searching for tag in crontab-pi"
grep -q "30 23" crontab-pi
if [ $? == 0 ]
then
    # Search for entry in the crontab so we replace it only once
    echo "Tag found, searching for entry"
    grep -q "git fetch" crontab-pi
    if [ $? == 0 ]
    then
        echo "Entry already replaced, no action taken"
    else
        echo "Now changing entry"
        # Delete 2 lines
        sed '/# 23:30/,/30 23 * * */d' crontab-pi > crontab-pi-fixed
        # Add 2 lines
        sed -i -e '$a \
# 23:30 do daily git pull from /G2User/ repo to update local system\
30 23 * * * cd /home/pi/G2User/; git fetch; git reset --hard HEAD; git merge "@{u}" > /home/pi/PSWS/Sstat/githubpull.stat 2>&1' crontab-pi-fixed
        # Replace crontab with the fixed file
        echo "Now replacing crontab"
        crontab -u pi crontab-pi-fixed
        rm -f crontab-pi-fixed
    fi
else
    echo "Tag not found"
fi

rm -f crontab-pi

exit 0

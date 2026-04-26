#!/bin/bash
# git-crontab-fix.sh
# Replace the pi user's crontab git pull or git fetch/reset/merge commands with githubpull.sh

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
    fetch_code=$?
    grep -q "git reset" crontab-pi
    reset_code=$?
    if [[ $fetch_code == 0 || $reset_code == 0 ]]
    then
        echo "Now changing entry"
        # Delete 2 lines
        sed '/# 23:30/,/30 23 * * */d' crontab-pi > crontab-pi-fixed
        # Add 2 lines
        sed -i -e '$a \
# 23:30 do daily git pull from /G2User/ repo to update local system\
30 23 * * * /home/pi/G2User/githubpull.sh > /home/pi/PSWS/Sstat/githubpull.stat 2>&1' crontab-pi-fixed
        # Replace crontab with the fixed file
        echo "Now replacing crontab"
        crontab -u pi crontab-pi-fixed
        rm -f crontab-pi-fixed
        echo "Pi user crontab entry will now call githubpull.sh"
    else
        echo "Pi user crontab git command already replaced, no action taken"
    fi
else
    echo "Tag not found"
fi

rm -f crontab-pi

exit 0

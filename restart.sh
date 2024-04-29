#!/bin/bash
# Restart G2console for specified node

date
echo restart.sh started
RESTART_NODE=$1
NODE=`cat /home/pi/PSWS/Sinfo/NodeNum.txt`
if [ $NODE == $RESTART_NODE ]
then
    echo G2console will restart for node $RESTART_NODE
    echo Terminating G2console...
    sudo killall datactrlr
    sleep 1
    echo Updating G2User...
    /home/pi/G2User/ur.sh > /home/pi/PSWS/Sstat/ur.stat 2>&1
    sleep 1
    echo Restarting G2console...
    export DISPLAY=:0
    export XAUTHORITY=/home/pi/.Xauthority
    lxterminal -t G2console --geometry=59x39 -e python3 /home/pi/G2User/G2console.py -r
fi

echo restart.sh ended


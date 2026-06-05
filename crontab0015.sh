#!/bin/bash
# 00:15 crontab job for root 

date
echo Crontab 00:15 job
echo

NODE=`cat /home/pi/PSWS/Sinfo/NodeNum.txt`

# Install meshagent for selected nodes
#if [ $NODE == "N0001020" ]
#then
#    echo "Installing meshagent for Node ${NODE}"
#    cd /home/pi/G2User/mesh
#    sudo ./mesh_agent_install.sh > /home/pi/PSWS/Sstat/mesh_agent_install.stat 2>&1
#fi

# Disable magdata for selected node and restart console
#if [ $NODE == "N0001026" ]
#then
#    echo "Disabling magnetometer data and restarting console for Node ${NODE}"
#    cd /home/pi/PSWS/Scmd
#    mv -v magtmp _magtmp
#    touch restartcon
#fi

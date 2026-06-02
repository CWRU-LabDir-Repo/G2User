#!/bin/bash
# 00:15 crontab job for root 

date
echo Crontab 00:15 job
echo

# Install meshagent for selected nodes
NODE=`cat /home/pi/PSWS/Sinfo/NodeNum.txt`
if [ $NODE == "N0001022" ]
then
    echo "Installing meshagent for Node ${NODE}"
    cd /home/pi/G2User/mesh
    sudo ./mesh_agent_install.sh > /home/pi/PSWS/Sstat/mesh_agent_install.stat 2>&1
fi



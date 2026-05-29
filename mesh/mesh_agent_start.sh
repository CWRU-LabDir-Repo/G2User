#!/bin/bash
#
# Start meshagent.
#

date
echo $0

cd /home/pi/G2User/mesh

echo "Starting meshagent"
sudo systemctl start meshagent


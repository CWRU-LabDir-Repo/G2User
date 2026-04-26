#!/bin/bash

CONF=/home/pi/PSWS/Sinfo/PICOSetFrq.txt
NODE=`cat /home/pi/PSWS/Sinfo/NodeNum.txt`
grep -q XR2 $CONF
if [ $? == 0 ]
then
    echo "Changing RasPi debug level from 2 to 1 for node ${NODE}"
    echo "Editing ${CONF}"
    sed -i -e 's/XR2/XR1/g' ${CONF}
else
    echo "Debug level OK"
fi


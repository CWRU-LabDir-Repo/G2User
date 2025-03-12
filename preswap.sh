#!/bin/bash
#
# preswap.sh
#
# Prepare the Grape2 system for swapping the external hard-disk drive.
# Must run under sudo.
#
# This program attempts to set up the HDD swap as safely as possible.
# Preserving the 4TB of raw Grape2 data is critical.
# If any error occurs, the program prints an error message and terminates.
# It must not be run again until the error is resolved.
# The file /home/pi/PSWS/Scmd/noswap must be deleted to run this program again.
#
# To improve boot-time reliability, the program also changes the method of mounting the G2DATA directory.
# Instead of using a filesystem entry in /etc/fstab, the new method relies on G2DATA to be
# auto-mounted under the /media/pi directory when the Desktop logs in.
# /media/pi/G2DATA is then attached to a new symbolic link, /home/pi/G2DATA,
# the original Grape2 data root directory name.
#
# Author: Bill Blackwell AB1XB 2025-02-22
#

# Configuration
PGM=$(basename -- "$0")
G2DATA=/home/pi/G2DATA
DEVICE=/dev/sda1
FSTAB=/etc/fstab
DATE=`date`
FILEDATE=`date +%Y-%m-%d`
FILEDIRS="SdataR1 SdataR2 SdataR3 Smagtmp"
NOSWAP=/home/pi/PSWS/Scmd/noswap

# Print error message and terminate.
errexit ()
{
    echo ""
    echo "Error: $1"
    echo ""
    echo "***** $PGM failed! *****"
    echo ""
    echo Do not proceed with hard drive removal!
    echo Please report errors to: hamsci-grape@googlegroups.com
    echo and wait for instructions.
    echo ""
    exit 1
}

# Print banner
echo $PGM: Prepare the Grape2 system for swapping the external hard-disk drive
echo $DATE
echo ""
echo This program should be run as Step 1 of the Grape 2 Drive HDD Swap Procedure.
echo ""
read -p "Enter y to continue (default) or n to exit (Y/n): " ans
case "$ans" in
n|N)
    echo $PGM exiting
    exit 0
    ;;
y|Y|*)
    echo $PGM continuing
    ;;
esac

# Block program running more than once
if [ -f $NOSWAP ]
then
    errexit "$PGM cannot be run more than once; please get help from HamSCI."
fi
touch $NOSWAP

# Terminate the console/data controller
echo Terminating G2console...
killall datactrlr
sleep 1

# Run the data upload scripts.
# Copy current day's files to Sxfer directory using inline commands because files2xfer.py won't work for current files.
# Also give files a special extension to differentiate them from the same day's new files to be uploaded after the HDD swap.
echo "Copying today's data files to transfer directory..."
for DIR in $FILEDIRS
do
    FILEPATH=`ls ${G2DATA}/${DIR}/${FILEDATE}*`
    if [ $? == 0 ]
    then
        FILENAME=$(basename -- "$FILEPATH")
        cp -p ${FILEPATH} ${G2DATA}/Sxfer/${FILENAME}.preswap
        echo Copied ${FILEPATH}
    fi
done

echo Compressing files...
/home/pi/G2User/compfiles.sh > /home/pi/PSWS/Sstat/compfiles.stat 2>&1
sleep 1

echo Transferring files to repository...
/home/pi/G2User/xfer2repo.sh > /home/pi/PSWS/Sstat/xfer2repo.stat 2>&1
sleep 1

# Unmount device
mount -l | grep $DEVICE
if [ $? == 0 ]
then
    echo Unmounting $DEVICE...
    sudo umount -v $DEVICE
    if [ $? == 0 ]
    then
        echo Unmount successful
    else
        errexit "Unmount failed"
    fi
    sleep 1

# Verify device is unmounted
    mount -l | grep $DEVICE
    if [ $? == 0 ]
    then
        errexit "$DEVICE is still mounted"
    else
        echo "$DEVICE is no longer mounted"
    fi
    sleep 1
fi

# Remove the G2DATA directory
echo Removing $G2DATA directory
rm -f $G2DATA/nd
rm -dv $G2DATA
if [ $? != 0 ]
then
    errexit "Removing $G2DATA failed"
fi

# Disable the G2DATA filesystem mount in /etc/fstab; comment it out
grep "LABEL=G2DATA" $FSTAB
if [ $? == 0 ]
then
    sed -i '/LABEL=G2DATA/s/^/#/' $FSTAB
    if [ $? == 0 ]
    then
        echo Successfully disabled G2DATA mount in $FSTAB
    else
        errexit "Failed to disable G2DATA filesystem mount in $FSTAB"
    fi
else
    echo Contents of ${FSTAB}:
    cat $FSTAB
    errexit "Failed to find 'LABEL=G2DATA' in $FSTAB, error disabling filesystem mount"
fi

# Create the symbolic link.
ln -s /media/pi/G2DATA $G2DATA
if [ $? == 0 ]
then
    echo Successfully created symbolic link $G2DATA
else
    errexit "Failed to create symbolic link $G2DATA"
fi

# Success. Print messages.
echo ""
echo $PGM completed successfully.
echo ""
echo Please continue with Step 2 of the Grape 2 Drive HDD Swap Procedure.
echo ""

exit 0


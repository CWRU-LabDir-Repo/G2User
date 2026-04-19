#!/bin/bash
#
# Start the G2console, or restart it after applying updates.
# Verify the G2DATA directory is correctly mounted before starting console.
#

#LOG=/home/pi/PSWS/Sstat/g2cstart.stat
G2C=G2console
G2CARG=$1
SCMD=/home/pi/PSWS/Scmd
G2User=/home/pi/G2User
G2DATA=/home/pi/G2DATA
G2MOUNT=/media/pi/G2DATA
RESTART_FILE=$SCMD/restartcon

# Print stdout and stderr to both the screen and a log file
# (this works, but keeps stdout hostage when console is started, so can't use this in its current form.
#exec > >(tee -ia $LOG) 2>&1

# Verify G2DATA directory is defined correctly.
# Then allow time for G2DATA mount to complete before console is started.
MOUNTOK=false
if [ ! -L "$G2DATA" ]
then
    echo "Error: $G2DATA is not a symbolic link:"
    ls -al $G2DATA
else
    seconds=5
    while [ $seconds -gt 0 ]
    do
        if [ -e "$G2DATA" ]
        then
            TARGET=`readlink -f "$G2DATA"`
            if [ "$TARGET" == "$G2MOUNT" ]
            then
                MOUNTOK=true
                break
            else
                echo "Error: Link target $TARGET is not $G2MOUNT"
            fi
        else
            echo "$G2C waiting for $G2MOUNT...$seconds"
            sleep 1
            : $((seconds--))
        fi
    done
    if [ $seconds == 0 ]
    then
        echo "Error: Timeout waiting for $G2MOUNT auto-mount"
    fi
fi

if [ $MOUNTOK == false ]
then
    echo "$G2C will not start due to above error."
    echo "Please correct the condition and login again."
#    echo "This error is logged in $LOG"
    read -p "Press Enter to exit: " var
    exit 1
fi

# Start G2console
STARTCON=true
while $STARTCON
do
    echo "`date +%Y-%m-%dT%H:%M:%S` $G2C starting"
    /usr/bin/python3 /home/pi/G2User/G2console.py $G2CARG
    code=$?
    if [[ $code == 5 || $code == 6 ]]
    then
        # Apply updates and restart the console.
        echo "`date +%Y-%m-%dT%H:%M:%S` $G2C stopped for updates"
        echo "Applying Grape 2 updates..."
        # wait for executables to stop
        sleep 4
        for FILE in `ls $G2User/ondeck`
        do
            cp -p $G2User/ondeck/${FILE} $G2User
            cpcode=$?
            if [ $cpcode == 0 ]
            then
                echo "Updated ${FILE}"
            else
                echo "Error: Update failed for ${FILE}"
#                read -p "Press Enter to continue: " var
            fi
        done
        rm -f $RESTART_FILE     # G2console deletes it but we will make sure it's gone
        # Restart the console, maintaining the mode the console was previously in,
        # ie. exit code 5 is Run mode, exit code 6 is Standby mode.
        if [ $code == 5 ]
        then
            G2CARG='-r'         # Console will restart in Run mode
        else
            G2CARG=''           # Console will restart in Standby mode
        fi
        echo "Restarting $G2C..."
        sleep 4
        echo
    else
        # All other exit codes terminate the while loop
        echo "`date +%Y-%m-%dT%H:%M:%S` $G2C stopped"
        STARTCON=false
    fi
done

exit $code


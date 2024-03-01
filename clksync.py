#!/usr/bin/env python3
# ### -*- coding: utf-8 -*-

# Written by John C Gibbons N8OBJ
# 05-09-2021 V1.00 - Started Clock sync time logging to file clksync.log
# 08-08-2021 V1.01 - fixed clksync filename pointer (to clksyncfile)

import RPi.GPIO as GPIO
import time
import shutil
import sys
import os


print ('Running clksync.py Ver 1.02')

########################################################################
# Variable inits

TSync = 0
now = time.localtime()
lsthr = now[3]
lstmin = now[4]
lstsec = now[5]
oldsec = lstsec
oldmin = lstmin
oldhr = lsthr
########################################################################
########################################################################
# set up GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
#
# GPIO24 controls the Blue SYNC LED On Ver 1.00 of the Stratum 1 GPS Clock Board (Pin 18)
#GPIO.setup(24, GPIO.OUT)

# GPIO25 controls the Blue SYNC LED On Ver 1.01 of the Stratum 1 GPS Clock Board (Pin 22)
GPIO.setup(25, GPIO.OUT)


#GPIO.output(24,0)  # Sync LED Off Ver 1.00 of the Stratum 1 GPS Clock Board

GPIO.output(25,0)  # Sync LED Off Ver 1.01 of the Stratum 1 GPS Clock Board
#print ('SYNC LED Off')
########################################################################

# Failsafe loop for clock sync
TooLong = 900   #900 seconds to sync the clock max
#TooLong = 7   #7 seconds for diag mod
numsec = 0

while (TSync == 0):
    # get current system time
    now = time.localtime()
    lsthr = now[3]
    lstmin = now[4]
    lstsec = now[5]

    #TSync = 1   #fake clk sync
    #TSync = 2    #fake clk abort sync

    # test for seconds skip
    if (oldsec != lstsec):
        #print ('OldSec = ', oldsec, 'LstSec = ', lstsec) 
        if ((((oldsec+1) == lstsec)) | ((oldsec == 59) & (lstsec == 00))):
            # second moved forward 1 sec - updaate info
            oldsec = lstsec # update second trackers
            numsec = numsec +1  # inc number of secs waiting to sync
        else:
            # non 1 sec jump in time - must have synced up!
            TSync = 1

    # test for minutes skip
    if (oldmin != lstmin):
        #print (' OldMin = ', oldmin, 'LstMin = ', lstmin)
        if ((((oldmin+1) == lstmin)) | ((oldmin == 59) & (lstmin == 00))):
            # second moved forward 1 sec - updaate info
            oldmin = lstmin
        else:
            # non 1 sec jump in time - must have synced up!
            TSync = 1

    # test for hours skip
    if (oldhr != lsthr):
        #print ('  OldHr = ', oldhr, 'LstHr = ', lsthr)
        if ((((oldhr+1) == lsthr)) | ((oldhr == 23) & (lsthr == 00))):
            # second moved forward 1 sec - updaate info
            oldhr = lsthr
        else:
            # non 1 sec jump in time - must have synced up!
            TSync = 1

    # test the time out timer so we don't stay in here forever
    if (numsec >= TooLong):
        # Been looping here too long - abort the check
        TSync = 2

########################################################################
# System clock has synced - display time now
# Timing loop synchronizer to system clock
# if the first digit (lpcnt) never gets beyond 1 then the loop
# is taking too long and the seconds are not syncing as they shpuld

now = time.localtime()
yr = now[0]
mth = now[1]
day =now[2]
hr = now[3]
min = now[4]
sec = now[5]

# Determine Active Time Zone Name
is_DST = time.localtime().tm_isdst
TZName = time.tzname[is_DST]

# Clock has synced - indicate so to the system
#print ('Synced in {:03d} Seconds - Clock Sync Time: {:02d}/{:02d}/{:04d} - {:02d}:{:02d}:{:02d} {:3s}\n' .format(numsec,mth, day, yr, hr, min, sec, TZName))
#save result appended to clksync.log file

clksyncfile = '/home/pi/clksync.log'

if (TSync == 1):   # clock has successfully synced - log it
    # save sync time to file
    print ('Synced in {:03d} Seconds - Clock Sync Time: {:02d}/{:02d}/{:04d} - {:02d}:{:02d}:{:02d} {:3s}\n' .format(numsec,mth, day, yr, hr, min, sec, TZName))
    CSF = open(clksyncfile,'a')
    CSF.write('Synced in {:03d} Seconds - Clock Sync Time: {:02d}/{:02d}/{:04d} - {:02d}:{:02d}:{:02d} {:3s}\n' .format(numsec,mth, day, yr, hr, min, sec, TZName))
    CSF.close # close the file
    CSF.flush() # flush the buffer (I'm impatient!)
    # turn on SYNC LED
    #GPIO.output(24,1)  # Sync LED On Ver 1.00 of the Stratum 1 GPS Clock Board
    GPIO.output(25,1)  # Sync LED On Ver 1.01 of the Stratum 1 GPS Clock Board
    print ('Good Time SYNC - SYNC LED On')

if (TSync == 2):   #  clock sysnc sequence has aborted  - log it
    # save sync time to file
    print ('After {:03d} Seconds - Aborting Clock Sync - System Time: {:02d}/{:02d}/{:04d} - {:02d}:{:02d}:{:02d} {:3s}\n' .format(numsec,mth, day, yr, hr, min, sec, TZName))
    CSF = open(clksyncfile,'a')
    CSF.write('After {:03d} Seconds - Aborting Clock Sync - System Time: {:02d}/{:02d}/{:04d} - {:02d}:{:02d}:{:02d} {:3s}\n' .format(numsec,mth, day, yr, hr, min, sec, TZName))
    CSF.close # close the file
    CSF.flush() # flush the buffer (I'm impatient!)

shutil.chown(clksyncfile, user='pi', group='pi')  # set the owner to pi (only in python3)
os.chmod(clksyncfile, mode=0o664)   # set the permissions to 664 (only in python3)

print ('clksync.py V1.02 exiting gracefully')

sys.exit(0)

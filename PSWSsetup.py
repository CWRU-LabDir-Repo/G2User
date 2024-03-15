#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
07-21-20 Ver 1.00 Create PSWS directory Structure
         Populate the Station Information in the /PSWS/Sinfo directory
11-25-20  Ver 1.01 Added a feqw small tweaks JC Gibbons
12-04-20  Ver 1.03 Fixed default Gridsquare if no Lat/Long/Elev file exists
01-29-21  Ver 1.04 Added Sxfer directory in file structure
02-05-22  Ver 2.00 Added Smagtmp directory structure for Grape2
09-13-23  Ver 2.01 Started support for Grape 2 operation
09-15-23  Ver 2.02 Finished first release of Grape 2 utility
09-16-23  Ver 2.03 Added column labels to radio and magtmp data files in last line header info
09-18-23  Ver 2.04 Fixed 1st pass thru callsign, antenna errors in header info
10-10-23  Ver 2.05 Fixed extra \n on callsign and CityState entry in 4 info files, Changed GPSDO
10-25-23  Ver 2.06 Added RFGain to Displayed System Information
10-29-23  Ver 2.07 Changed A2DCLK rate to 16 MHz then back to 8 MHz
12-07-23  Ver 2.08 VP added to PICOSetFreq Command file
12-15-23  Ver 2.09 Added XP1 and XR1 to PICOSetFreq Command file; kept prev Radio freq as default
12-16-23  Ver 2.10 Moved NBF flag file to /PSWS/Scmd/ directory
12-22-23  Ver 2.11 Moved /G2DATA to /home/pi/G2DATA/ - also created /G2DATA/logs/ directory
12-22-23  Ver 2.12 Moved Sxfer directory to hard drive - /home/pi/G2DATA/Sxfer/, changed to /G2DATA/Slogs/
01-07-24  Ver 2.13 Saved zeros calibration file in header of rawdata capture file for reference
01-09-24  Ver 2.14 Removed the \n from the end of the zeros.dat file (Bill actually removed it...)
01-10-24  Ver 2.15 Fixed OS to Bullseye, fixed DefZeros bug, fixed Lat, Lon, Elv inconsistencies
01-18-24  Ver 2.16 Added auto Lat, Lon, Elv from GPS vis /dev/ttys0 port on RasPi (not owned by GPS Daemon yet)
02-04-24  Ver 2.17 Changed to F400 again, Def to use new GPS setting, Added board Serial Numbers, 
                   FW rev numbers to Header info, check fix/pdop numbers for GPS save
02-05-24  Ver 2.18 Added Zero Cal to sequence of tasks to complete, added FW version of PSWSsetup to header files
                   Added system date/time to GPS fix acquisition into header files
02-29-24  Ver 2.19 Add autodetect of Magnetometer - changed header labels for Vp to Vrms
03-05-24  Ver 2.20 Finished autodetect of Magnetometer, semaphore file creation, G2DATA setup, added magdata ver to header files
03-06-24  Ver 2.21 Fixed format of Lat / Long numbers, magdata to ver 0.0.2
03-07-24  Ver 2.22 Fixed running datactrlr from ~/G2User/ issue
03-08-24  Ver 2.23 Fixed another running datactrlr from ~/G2User/ issue
03-14-24  Ver 2.24 Added reading FW version of magdata, setting file system params of G2DATA drive (check for mounting as well)
@author JCGibbons N8OBJ
"""

# Define Software version of this code (so you don't have to search for it in the code!)
SWVersion = '2.24'

import os
from os import path
import csv
import maidenhead as mh
import subprocess
from subprocess import Popen, PIPE
from datetime import datetime
import sys
sys.path.append('.')
import os.path
import pigpio
from smbus2 import SMBus

# Setup GPS port operation
from serial import Serial
from pynmeagps import NMEAReader

GPS_port = '/dev/ttyS0'
GPS_baud_rate = 115200

# ~ points to users home directory - usually /home/pi/
homepath = os.path.expanduser('~')

PSWSDir = homepath + "/PSWS"
InfoDir = PSWSDir + '/Sinfo/'
CmdDir = PSWSDir + "/Scmd/"
TempDir = PSWSDir + "/Stemp/"
StatDir = PSWSDir + "/Sstat/"
CodeDir = PSWSDir + "/Scode/"
# external HD mounted into /hmoe/pi/G2DATA/
XferDir = homepath + "/G2DATA/Sxfer/"
RawdataDir = homepath + '/G2DATA/Srawdata/'
DataDirR1 = homepath + "/G2DATA/SdataR1/"
DataDirR2 = homepath + "/G2DATA/SdataR2/"
DataDirR3 = homepath + "/G2DATA/SdataR3/"
MagTmpDir = homepath + "/G2DATA/Smagtmp/"
PlotDir = homepath + "/G2DATA/Splot/"
LogDir = homepath + "/G2DATA/Slogs/"

################################################################
################################################################

print('\n\nGrape 2 Personal Space Weather Station (PSWS) Setup Program Ver '  + SWVersion)
print('********************************************************************\n\n')
################################################################
################################################################

# Check for main base Directory
print('Checking / Creating PSWS Directory Structure\n')
print('Home Path = ' + homepath)

################################################################
################################################################
# make sure /home/pi/G2DATA SSD drive is mounted
# if it is mounted the following file will not exist
G2DATAndPath = '/home/pi/G2DATA/nd'

G2DATAPath = '/home/pi/G2DATA/'

if (path.exists(G2DATAndPath)):
    print('G2DATA EXT Storage Drive not Mounted - exiting setup')
    sys.exit(0)
# if fileis covered up by mount, G2DATA is mounted
else:
    print('G2DATA is mounted - proceeding with Setup')
    print('Setting up system params for mounted /G2DATA/ drive')
    #    print("Owner id of the file:", os.stat(homepath).st_uid)
    #    print("Group id of the file:", os.stat(homepath).st_gid)
    userid = os.stat(homepath).st_uid
    groupid = os.stat(homepath).st_gid
    # set uid, gid  to be same as home directory
    os.system(f"sudo chown pi:pi {G2DATAPath}")
    os.system(f"sudo chmod 774 {G2DATAPath}")

#sys.exit(0)
################################################################
################################################################

################################################################
# make sure PSWS path exists - if not, create it with correct permissions
if (path.exists(PSWSDir)):
    print('Base Dir PSWS exists ' + PSWSDir)
else:
    print('PSWS Not there - Creating path ' + PSWSDir)
    os.mkdir(PSWSDir)           # create the directory
    os.chmod(PSWSDir, mode=0o774)   # set the permissions to 764

# Check for the subdirectories
################################################################
# make sure Sinfo path exists - if not, create it with correct permissions
if (path.exists(InfoDir)):
    print('Sinfo exists ' + InfoDir)
else:
    print('Not there - making path ' + InfoDir)
    os.mkdir(InfoDir)           # create the directory
    os.chmod(InfoDir, mode=0o764)   # set the permissions to 764

################################################################
# make sure Scmd path exists - if not, create it with correct permissions
if (path.exists(CmdDir)):
    print('Scmd exists ' + CmdDir)
else:
    print('Not there - making path ' + CmdDir)
    os.mkdir(CmdDir)           # create the directory
    os.chmod(CmdDir, mode=0o774)   # set the permissions to 764

################################################################
# make sure Stemp path exists - if not, create it with correct permissions
if (path.exists(TempDir)):
    print('Stemp exists ' + TempDir)
else:
    print('Not there - making path ' + TempDir)
    os.mkdir(TempDir)           # create the directory
    os.chmod(TempDir, mode=0o764)   # set the permissions to 764

################################################################
# make sure Sstat path exists - if not, create it with correct permissions
if (path.exists(StatDir)):
    print('Sstat exists ' + StatDir)
else:
    print('Not there - making path ' + StatDir)
    os.mkdir(StatDir)           # create the directory
    os.chmod(StatDir, mode=0o764)   # set the permissions to 764

################################################################
# make sure Scode path exists - if not, create it with correct permissions
if (path.exists(CodeDir)):
    print('Scode exists ' + CodeDir)
else:
    print('Not there - making path ' + CodeDir)
    os.mkdir(CodeDir)           # create the directory
    os.chmod(CodeDir, mode=0o774)   # set the permissions to 764

################################################################
################################################################
# Start working on external HD mounted in /home/pi/G2DATA/
################################################################
################################################################
# make sure Sxfer path exists - if not, create it with correct permissions
if (path.exists(XferDir)):
    print('Sxfer exists ' + XferDir)
else:
    print('Not there - making path ' + XferDir)
    os.mkdir(XferDir)           # create the directory
    os.chmod(XferDir, mode=0o764)   # set the permissions to 764

################################################################
# make sure Rawdata path exists - if not, create it with correct permissions
if (path.exists(RawdataDir)):
    print('Srawdata exists ' + RawdataDir)
else:
    print('Not there - making path ' + RawdataDir)
    os.mkdir(RawdataDir)           # create the directory
    os.chmod(RawdataDir, mode=0o764)   # set the permissions to 764

################################################################
# make sure Splot path exists - if not, create it with correct permissions
if (path.exists(PlotDir)):
    print('Splot exists ' + PlotDir)
else:
    print('Not there - making path ' + PlotDir)
    os.mkdir(PlotDir)           # create the directory
    os.chmod(PlotDir, mode=0o764)   # set the permissions to 764

################################################################
# make sure Sdata Radio 1 path exists - if not, create it with correct permissions
if (path.exists(DataDirR1)):
    print('SdataR1 exists ' + DataDirR1)
else:
    print('Not there - making path ' + DataDirR1)
    os.mkdir(DataDirR1)           # create the directory
    os.chmod(DataDirR1, mode=0o764)   # set the permissions to 764

################################################################
# make sure Sdata Radio 2 path exists - if not, create it with correct permissions
if (path.exists(DataDirR2)):
    print('SdataR2 exists ' + DataDirR2)
else:
    print('Not there - making path ' + DataDirR2)
    os.mkdir(DataDirR2)           # create the directory
    os.chmod(DataDirR2, mode=0o764)   # set the permissions to 764

################################################################
# make sure Sdata Radio 1 path exists - if not, create it with correct permissions
if (path.exists(DataDirR3)):
    print('SdataR1 exists ' + DataDirR3)
else:
    print('Not there - making path ' + DataDirR3)
    os.mkdir(DataDirR3)           # create the directory
    os.chmod(DataDirR3, mode=0o764)   # set the permissions to 764

################################################################
# make sure Smagtmp path exists - if not, create it with correct permissions
if (path.exists(MagTmpDir)):
    print('Smagtmp exists ' + MagTmpDir)
else:
    print('Not there - making path ' + MagTmpDir)
    os.mkdir(MagTmpDir)           # create the directory
    os.chmod(MagTmpDir, mode=0o764)   # set the permissions to 764

################################################################
# make sure logs path exists - if not, create it with correct permissions
if (path.exists(LogDir)):
    print('Slogs exists ' + LogDir)
else:
    print('Not there - making path ' + LogDir)
    os.mkdir(LogDir)           # create the directory
    os.chmod(LogDir, mode=0o764)   # set the permissions to 764

################################################################
################################################################
# All dirctories exist or were created -now populate the station information
print('\nNow checking all system Metadata Information')

################################################################
################################################################
# All dirctories exist - now check for info
################################################################
################################################################

################################################################
# Check for Serial Number Info
################################################################
SerNumPath = InfoDir + "SerNum.txt"

if (path.exists(SerNumPath)):
    with open(SerNumPath, 'r') as SerNumFile: # file there - open it
        SerNum = SerNumFile.readline()  # read file contents
        SerNumFile.close()   # close file
        print('\nCurrent RFDeckSN, LogicCtrlrSN = '+ SerNum)  # display it

else:
    print('\nGrape 2 Board Serial Numbers not found - Please Enter')
    lthSN=0
    while(lthSN !=8):
        SerNum = input('RFDeckSN,LogicCtrlrSN -> SN Format: [100,1000]: ')
        lthSN = len(SerNum)
    with open(SerNumPath, 'w') as SerNumFile:
        SerNumFile.write(SerNum) #write default Freq Std
        SerNumFile.close()
        os.chmod(SerNumPath, mode=0o764)   # set the permissions to 764
    print('Saved RFDeckSN, LogicCtrlrSN Board Serial Numbers = ' + SerNum + '\n')

# print('Board SN string = '+ SerNum)

################################################################
# Get FW version Number Info for Header file
################################################################

fwinput_filename = "qDatactrlr.txt"
fwoutput_filename = "outDatactrlr.txt"

print('Query PICO controller for FW Versions...')

# Create q.txt with the character 'q' followed by line-feed
with open(fwinput_filename, "w") as fwfile:
    fwfile.write("q\n")

# Start the data controller and redirect input from q.txt, output to out.txt
subprocess.run(
    ["sudo", "/home/pi/G2User/datactrlr"],
    stdin=open(fwinput_filename, "r"),
    stdout=open(fwoutput_filename, "w"),
)

# run magdata -v to get version numberand append to previos data file
print('run magdata to get version number')
magdata = subprocess.Popen(
    ["sudo", "/home/pi/G2User/magdata", "-v"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
magdata_outs, magdata_errs = magdata.communicate()

# Read and parse out.txt to find the datactrlr version and Picorun version
with open(fwoutput_filename, "r") as fwfile:
    lines = fwfile.readlines()

# Delete q.txt and out.txt
os.remove(fwinput_filename)
os.remove(fwoutput_filename)

datactrlr_version = None
picorun_version = None
magdata_version = magdata_outs.strip().split()[-1]

for line in reversed(lines):
    if "data controller" in line.lower():
        datactrlr_version = line.strip().split("v")[-1]
        break
    elif "picorun version" in line.lower():
        picorun_version = line.strip().split(" ")[-1]

    elif "fail" in line.lower():
        print(line)

# Print the versions
print('\nCurrent Firmware Revs:')
print(f"Data Controller Version: {datactrlr_version}")
print(f"Picorun Version: {picorun_version}")
print(f"magdata Version: {magdata_version}")

################################################################
# Perform Zero cal of A/D Channels
################################################################

print("\nPerforming A/D Zero's calibration...")

# from subprocess import Popen, PIPE

print("Starting PICO datactrlr...")
datactrlr = Popen(["sudo", "/home/pi/G2User/datactrlr"], stdin=PIPE, stdout=PIPE, stderr=PIPE)

print("Executing the Z command...")
stdout, stderr = datactrlr.communicate(b"z\nq\n")
# print("Data Controller Output:", stdout.decode())

print("A/D Zero's calibration completed")

################################################################
# Check for existance of RM3100 Magnetometer on I^2C bus(1)
################################################################

print("\nLooking for RM3100 Magnetometer on I^2C SMBus(1)")

MagTmpPath="/home/pi/PSWS/Scmd/magtmp"
HexMagAddr="20"
VERSION_EXPECTED = 0x22
I2C_BUS = 1
RM3100_ADDRESS = 0x20
RM3100Addr = '0x20'
RM3100I2C_REVID = 0x36
i2cDeviceHandle = 0

bus = SMBus(1)
print('Attempting to read I^2C SMBus(1) at base address',RM3100Addr, 'Looking for REVID of RM3100')
# attempt to read the address on I^2C bus
try:
    rv = bus.read_byte_data(RM3100_ADDRESS, RM3100I2C_REVID)
except Exception as e:
   print('Error reading I2C bus for RM3100: ', str(e))
   rv = 00

# got good read of register - check value
if(rv == VERSION_EXPECTED):
    # I^2C bus read worked at specified address and value retrieved is correct
    print('Received correct REVID of 0x22 -- RM3100 is present on I^2C bus')
    bus.close()
    print('RM3100 found - turning on magdata collection')
    # create semaphore flag file /home/pi/PSWS/Scmd/magtmp and turn on data collection
    with open(MagTmpPath, 'w') as MagTmpFile:
        MagTmpFile.write(HexMagAddr) #write base address of Magnetometer
        MagTmpFile.close()
    os.chmod(MagTmpPath, mode=0o764)   # set the permissions to 764

else:
    # got error reading bus, not Magnetometer - shut off data collection
    print("RM3100 not found - turning off magdata collection")
    # remove semaphore flag file /home/pi/PSWS/Scmd/magtmp
    if os.path.exists(MagTmpPath):
        #print("Delating semaphore file magtmp")
        os.remove(MagTmpPath) # turn off magtmp data collection
# exit(0)

################################################################
# check for existance of node number
################################################################
NodePath = InfoDir + "NodeNum.txt"

if (path.exists(NodePath)):
    with open(NodePath, 'r') as NodeFile: # file there - open it
        OrigSnode = NodeFile.readline()  # read file contents
        NodeFile.close()   # close file
        if len(OrigSnode) >8:  #look for <lf> char
            Snode = OrigSnode[:-1] # Strip of <LF>
        print('\nCurrent Node Assignment = '+ OrigSnode + '\n')  # display it
        Nfound = 1 #indicate file exist and displey contents
else:
    print('\nNode file not found- creating default\n')
    with open(NodePath, 'w') as NodeFile:
        #Snode = 'N0000000/n' # create default Node Number
        Snode = 'N0000000' # create default Node Number
        NodeFile.write(Snode) #write default node
        NodeFile.close()
    os.chmod(NodePath, mode=0o764)   # set the permissions to 764
    OrigSnode = Snode;
    #Snode = Snode[:-1] # Strip of <LF>
    print('Created Node Number = ', Snode, '/n')
    Nfound = 0
Done = 0
while Done == 0:
    print('Enter New Node Number [format N1234567]')
    NewNN = input('or <Enter> to keep this one > ')
    changeNN = 0
    nochng = 0
    if NewNN == '':
        print('Keeping existing Node Number as ' + OrigSnode)
        NewNN = OrigSnode
        Done = 1
        nochng = 1
    else:
        # check to see if entry makes sense
        # firtst check length for correct # of chars
        nnlth = len(NewNN)
        if  nnlth == 8:
            print('Correct Length of '+ str(nnlth) + ' for ' + NewNN)
            changeNN = changeNN + 1
        else:
            print('Wrong Length of ' + str(nnlth) + ' for '+ NewNN)
        #print('Node Number Entered as ' + NewNN)

    #Check for leading N
        if NewNN[:1] == 'N':
            print('Correct header letter - ' + NewNN)
            changeNN = changeNN + 1
        else:
            print('Incorrect header letter - ' + NewNN)


    changeNN = changeNN + 1  # allow any char sequence in node number 7 digit field

    if(changeNN == 3 ): # 0 for keep old number or failed test, 1 or 2 for failed tests, 3 for valid entry
        with open(NodePath, 'w') as NodeFile:
            #NodeFile.write(NewNN + '\n') #write new node number
            NodeFile.write(NewNN) #write new node number
            NodeFile.close()
        os.chmod(NodePath, mode=0o764)   # set the permissions to 764
        Done = 1
        print('New Node of '+ NewNN + ' saved\n')
    else:
        print('Node Number - no change made\n')
        NewNN = OrigSnode

################################################################
# Check for CallSign info
################################################################
CallSgnPath = InfoDir + "CallSign.txt"

if (path.exists(CallSgnPath)):
    with open(CallSgnPath, 'r') as CallSgnFile: # file there - open it
        CallSign = CallSgnFile.readline()  # read file contents
        CallSgnFile.close()   # close file
        print('Current CallSign = '+ CallSign + '\n')  # display it

else:
    print('CallSign file not found- creating default')
    with open(CallSgnPath, 'w') as CallSgnFile:
        CallSign = 'NoCall' # create default callsign
        CallSgnFile.write(CallSign) #write default callsign
        CallSgnFile.close()
    os.chmod(CallSgnPath, mode=0o764)   # set the permissions to 764
    print('Created default CallSign =', CallSign)
CSchng = 0
Done = 0
while Done == 0:
    print('Enter New CallSign')
    NewCallS = input('or <Enter> to keep this one > ')
    if NewCallS == '':
        print('Keeping existing CallSign as ' + CallSign)
        NewCallS = CallSign
        Done = 1
    else:
        # check to see if entry makes sense
        # firtst check length for correct # of chars
        cslth = len(NewCallS)
        if  cslth >= 3:
            print('Correct min Length of '+ str(cslth) + ' for ' + NewCallS)
            Done =  1
            CSchng = 1
        else:
            print('Wrong min Length of ' + str(cslth) + ' for '+ NewCallS)

if(CSchng == 1 ): # 0 for keep old number or failed test, 1 for valid entry
    with open(CallSgnPath, 'w') as CallSgnFile:
        CallSgnFile.write(NewCallS) #write new callsign
        CallSgnFile.close()
    os.chmod(CallSgnPath, mode=0o764)   # set the permissions to 764
    print('New CallSign '+ NewCallS + ' saved\n')
    NewCallS = NewCallS # for final printout formatting
    CallSign = NewCallS # save as this on first pass as well
else:
    print('CallSign - no change made\n')

################################################################
# Get Lat, Lon, Elv info from GPS and check for reported accuracy
################################################################

print('Query UBLOX GPS for Lat, Lon, Elv, Fix, PDOP...')

gps_data = {"lat":None, "lon":None, "elev":None, "pdop":None, "fix":None}
missing_data = set(gps_data.keys())
GPS_fix=''
GPS_pdop=''
GPS_lat=''
GPS_lon=''
GPS_elv=''

with Serial(GPS_port, GPS_baud_rate, timeout=3) as stream:
    nmr = NMEAReader(stream)
    while missing_data:
        _, parsed_data = nmr.read()
        if parsed_data.msgID == "GSA":
            gps_data["fix"] = parsed_data.navMode
            gps_data["pdop"] = parsed_data.PDOP
            GPS_fix = parsed_data.navMode
            GPS_pdop = parsed_data.PDOP
            missing_data.discard("fix")
            missing_data.discard("pdop")
        elif parsed_data.msgID == "GGA":
            gps_data["lat"] = parsed_data.lat
            gps_data["lon"] = parsed_data.lon
            gps_data["elev"] = parsed_data.alt
            GPS_lat = parsed_data.lat
            GPS_lon = parsed_data.lon
            GPS_elv = parsed_data.alt
            missing_data.discard("lat")
            missing_data.discard("lon")
            missing_data.discard("elev")

# indicate to user if values should be used

BADfix = 0

if (GPS_pdop >= 4):
    PDOPOK = '  PDOP is Lousy - Not recommended to use this GPS location'
    BADfix = 1
else:
    PDOPOK = '  PDOP Good -  OK to use this GPS Location'

if (GPS_fix != 3):
    FIXOK = '  GPS Fix is not 3D - Not recommended to use this GPS location'
    BADfix = 1
else:
    FIXOK = '  GPS Fix is Good -  OK to use this GPS Location'

# print(gps_data)
print('\n\nUBLOX GPS reports:\n')
print('Lat = ', GPS_lat)
print('Lon = ', GPS_lon)
print('Elv = ', GPS_elv)
print('PDOP = ', GPS_pdop, PDOPOK)
print('Fix = ', GPS_fix, FIXOK)
print('\nNote:  If PDOP > 4.0 or Fix < 3 you should not use this GPS Location\n')

# exit(0)

################################################################
# check for existance of Lat Lon Elev
################################################################
LLEPath = InfoDir + "LatLonElv.txt"
FixPDOPPath = InfoDir + "FixPDOP.txt"
GSPath = InfoDir + "GridSqr.txt"
GPSDTPath = InfoDir + "GPSDateTime.txt"

NewLLE = 's'  #indicate no change to LLE file

# Now try to read GPSDateTime file
if (path.exists(GPSDTPath)):
    with open(GPSDTPath, 'r') as GPSDTFile:
        GPSDateTime = GPSDTFile.readline()
        GPSDTFile.close()
else:
    GPSDateTime = 'none'

print('\nCurrent Saved GPS Acquisition Date/Time = ' + GPSDateTime)

# Now try to read Grid Square to file
if (path.exists(GSPath)):
    with open(GSPath, 'r') as GSFile:
        GridSqr = GSFile.readline()
        GSFile.close()
else:
    GridSqr = 'none'

print('Current Saved Calculated GridSquare = ' + GridSqr)

# try to read existing LLE data
if (path.exists(LLEPath)):
    with open(LLEPath, 'r') as LLEFile: # file there - open it
        LatLonElv = LLEFile.readline()  # read file contents
        LLEFile.close()   # close file
else:
    LatLonElv = 'none' # create default LatLonElv

print('Current Saved Lat, Lon, Elv Assignment = '+ LatLonElv)  # display it

# try to read existing FixPDOP data
if (path.exists(FixPDOPPath)):
    with open(FixPDOPPath, 'r') as FixPDOPFile: # file there - open it
        FixPDOP = FixPDOPFile.readline()  # read file contents
        FixPDOPFile.close()   # close file
else:
    FixPDOP = 'none'  # create bad fix numbers

print('Currently Saved GPS Fix,PDOP = ' + FixPDOP + '\n')

# print('Old existing GPS Fix,PDOP = ' + FixPDOP)

if (BADfix == 0):
    print('Save current settings or use new GPS acquired settings?')
    NewLLE = input('s = save existing, n = use new GPS data (<Enter> = s): ')
    if (NewLLE == ''):
        NewLLE = 's'
# else:
if (BADfix == 1):
    print('Current GPS Fix, PDOP = ' + FixPDOP)
    print('GPS fix is not reliable - try again later...')
    NewLLE = 's'  # indicate no change to GPS LatLonElv
# print('NewLLE = ' + NewLLE)

################################################################
# Check if need to update Lat, Lon, Elev and Gridsquare

# if told to save new GPS info
if (NewLLE == 'n'):
    #get system date and time
    GPSDateTime = str(datetime.now())

    #Now write new GPSDateTime to file
    with open(GPSDTPath, 'w') as GPSDTFile:
        GPSDTFile.write(GPSDateTime)
        GPSDTFile.close()
        os.chmod(GPSDTPath, mode=0o764)   # set the permissions to 664
    print('\nNew Saved GPS Date/Time = ' + GPSDateTime)

    GridSqr =  mh.to_maiden(GPS_lat, GPS_lon) # create gridsquare from Lat /Long info

    #Now write new Grid Square to file
    with open(GSPath, 'w') as GSFile:
        GSFile.write(GridSqr)
        GSFile.close()
        os.chmod(GSPath, mode=0o764)   # set the permissions to 664
    print('New Saved Calculated GridSquare = ' + GridSqr)

    #Now write Lat Long Elv to a new file
    with open(LLEPath, 'w') as LLEFile:
        # create new Lat Long Elv Numbers
        # Lat = 4.6 digits and Long = 3.6 digits
        #LatLonElv = str(GPS_lat) + ',' + str(GPS_lon) + ',' + str(GPS_elv)
        LatLonElv = f"{GPS_lat:.6f}".rjust(11) + "," + f"{GPS_lon:.6f}".rjust(10) + f",{GPS_elv}"
        LLEFile.write(LatLonElv) #write default LAt Long Elev
        LLEFile.close()
        os.chmod(LLEPath, mode=0o764)   # set the permissions to 764
    print('New Saved GPS Lat,Lon,Elv = ' + LatLonElv )

    #Now write GPS Fix,PDOP to a new file
    with open(FixPDOPPath, 'w') as FixPDOPFile:
        FixPDOP = str(GPS_fix) + ',' + str(GPS_pdop)
        FixPDOPFile.write(FixPDOP) #write used Fix,PDOP
        FixPDOPFile.close()
        os.chmod(FixPDOPPath, mode=0o764)   # set the permissions to 764
    print('New Saved GPS Fix,PDOP = ' + FixPDOP )

# if told to keep existing data the same
if (NewLLE == 's'):
    # read stored GPSDateTime
    if (path.exists(GPSDTPath)):
        with open(GPSDTPath, 'r') as GPSDTFile: # file there - open it
            GPSDateTime = GPSDTFile.readline()  # read file contents
            GPSDTFile.close()   # close file
        print('\nNo change - Current Saved GPS Date/Time = '+ GPSDateTime)  # display it

    # read stored Gridsquare
    if (path.exists(GSPath)):
        with open(GSPath, 'r') as GSFile: # file there - open it
            GridSqr = GSFile.readline()  # read file contents
            GSFile.close()   # close file
        print('No change - Current Saved GridSquare = '+ GridSqr)  # display it

    # Read current LLE
    if (path.exists(LLEPath)):
        with open(LLEPath, 'r') as LLEFile: # file there - open it
            LatLonElv = LLEFile.readline()  # read file contents
            LLEFile.close()   # close file
        print('No change - Current Saved Lat,Lon,Elv = '+ LatLonElv)  # display it

    # Read current FixPDOP
    if (path.exists(FixPDOPPath)):
        with open(FixPDOPPath, 'r') as FixPDOPFile: # file there - open it
            FixPDOP = FixPDOPFile.readline()  # read file contents
            FixPDOPFile.close()   # close file
        print('No Change - Current Saved GPS Fix,PDOP = ' + FixPDOP + '\n')  # display it

################################################################
# Check for City State info
################################################################
CSPath = InfoDir + "CityState.txt"

if (path.exists(CSPath)):
    with open(CSPath, 'r') as CSFile: # file there - open it
        CityState = CSFile.readline()  # read file contents
        CSFile.close()   # close file
        print('\nCurrent Saved City State = '+ CityState + '\n')  # display it

else:
    print('\nCityState file not found- creating default')
    with open(CSPath, 'w') as CSFile:
        CityState = 'NOCity NOState' # create default City State
        CSFile.write(CityState) #write default City State
        CSFile.close()
    os.chmod(CSPath, mode=0o764)   # set the permissions to 764
    print('Created default City State = ', CityState)
CSchng = 0
Done = 0
while Done == 0:
    print('Enter New City State [format City State - NO commas]')
    NewCS = input('or <Enter> to keep this one > ')
    if NewCS == '':
        print('Keeping existing City State as ' + CityState)
        NewCS = CityState
        Done = 1
    else:
        # check to see if entry makes sense
        # firtst check length for correct # of chars
        cslth = len(NewCS)
        if  cslth >= 4:
            print('Correct min Length of '+ str(cslth) + ' for ' + NewCS)
            Done =  1
            CSchng = 1
        else:
            print('Wrong min Length of ' + str(cslth) + ' for '+ NewCS)

if(CSchng == 1 ): # 0 for keep old number or failed test, 1 for valid entry
    with open(CSPath, 'w') as CSFile:
        CSFile.write(NewCS) #write new node number
        CSFile.close()
    os.chmod(CSPath, mode=0o764)   # set the permissions to 764
    print('New City State of '+ NewCS + ' saved\n')
else:
    print('City State - no change made\n')

################################################################
# Check for FreqRef info
################################################################
FreqStdPath = InfoDir + "FreqStd.txt"

# if (path.exists(FreqStdPath)):
#    with open(FreqStdPath, 'r') as FrqStdFile: # file there - open it
#        FreqStd = FrqStdFile.readline()  # read file contents
#        FrqStdFile.close()   # close file
#        print('\nCurrent Saved Frequency Standard = '+ FreqStd)  # display it

# else:
# print('\nFrequency Standard file not found - creating default')
with open(FreqStdPath, 'w') as FrqStdFile:
    FreqStd = 'LB GPSDO' # create default freq std
    FrqStdFile.write(FreqStd) #write default Freq Std
    FrqStdFile.close()
os.chmod(FreqStdPath, mode=0o764)   # set the permissions to 764
print('Setting Frequency Standard =', FreqStd)

################################################################
# check for RFGain jumper setting
################################################################
RFGPath = InfoDir + "RFGain.txt"

## if first time to run create defaulet OrigRFGain = 1
if (path.exists(RFGPath)):
    with open(RFGPath, 'r') as RFGFile: # file there - open it
        OrigRFGain = RFGFile.readline()  # read file contents
        RFGFile.close()   # close file
        print('\nFound Current RFGain = '+ OrigRFGain + '\n')  # display it
else:
    print('\n RFGain.txt file not found - create initial default RFGain = 1\n')
    with open(RFGPath, 'w') as RFGFile:
        OrigRFGain = '1' # create default RF Gain Setting = 1
        RFGFile.write(OrigRFGain) #write default RFGain
        RFGFile.close()
        os.chmod(RFGPath, mode=0o764)   # set the permissions to 764
        print('Created Default RFGain = '+ OrigRFGain + '/n')

Done = 0
RFGChanged = 0
while (Done == 0):
    print('Current RFGain = ' + OrigRFGain + '\n\n')
    print('Enter New RF Gain Junmper Setting of 1, 2.5, 4, 10\n')
    NewRFGain = input('or <Enter> to keep current value > ')
    if NewRFGain == '':
        print('Keeping current RFGain = ' + OrigRFGain)
        RFGain = OrigRFGain
        Done = 1
        RFGChanged = 0
    else:
        # check to see if NewRFGain entry makes sense
	# entry is valid - save results
        RFGain = NewRFGain
        RFGChanged = 1
        ## Check if valid gain number
        if ((NewRFGain == "1") | (NewRFGain == "2.5") | (NewRFGain == "4") | (NewRFGain == "10")):
            Done = 1

# new entry makes sense - save old gain setting in RFGain.old
#  keeping orig file attributes and save new entry in RFGain.txt
# move RFGain.txt --> RFGain.old saving file attributges
if (RFGChanged == 1):
    RFGain = NewRFGain
else:
    RFGain = OrigRFGain

with open(RFGPath, 'w') as RFGFile:
    RFGFile.write(RFGain) #write new RFGain number
    RFGFile.close()
    os.chmod(RFGPath, mode=0o764)   # set the permissions to 764

if (RFGChanged == 1):
    print('New RFGain = '+ RFGain + ' saved\n')
else:
    print('No RFGain change made\n')

################################################################
# Get Radio info
################################################################
RadioPath = InfoDir + "Radio.txt"

# if (path.exists(RadioPath)):
#    with open(RadioPath, 'r') as RadioFile: # file there - open it
#        Radio = RadioFile.readline()  # read file contents
#        RadioFile.close()   # close file
#        print('\nCurrent Saved Radio = '+ Radio)  # display it

# else:
#    print('\nRadio file not found- creating default')
with open(RadioPath, 'w') as RadioFile:
    Radio = 'Grape 2' # create default Radio Type
    RadioFile.write(Radio) #write default Radio type
    RadioFile.close()
os.chmod(RadioPath, mode=0o764)   # set the permissions to 764
print('Setting Radio =', Radio)

################################################################
# Get Radio 1 ID info
################################################################
RID1Path = InfoDir + "RadioID1.txt"
# if (path.exists(RID1Path)):
#    with open(RID1Path, 'r') as RadioID1File: # file there - open it
#        RadioID1 = RadioID1File.readline()  # read file contents
#        RadioID1File.close()   # close file
#        print('\nCurrent Saved Radio 1 ID = '+ RadioID1)  # display it

# else:
#    print('\nRadioID1 file not found- creating default')
with open(RID1Path, 'w') as RadioID1File:
    RadioID1 = 'G2R1' # create default Radio 1 ID
    RadioID1File.write(RadioID1) #write default Radio 1 ID
    RadioID1File.close()
os.chmod(RID1Path, mode=0o764)   # set the permissions to 764
print('Setting Radio 1 ID =', RadioID1)

################################################################
# Get Radio 2 ID info
################################################################
RID2Path = InfoDir + "RadioID2.txt"
# if (path.exists(RID2Path)):
#    with open(RID2Path, 'r') as RadioID2File: # file there - open it
#        RadioID2 = RadioID2File.readline()  # read file contents
#        RadioID2File.close()   # close file
#        print('\nCurrent Saved Radio 2 ID = '+ RadioID2)  # display it

# else:
#    print('\nRadioID1 file not found- creating default')
with open(RID2Path, 'w') as RadioID2File:
    RadioID2 = 'G2R2' # create default Radio 2 ID
    RadioID2File.write(RadioID2) #write default Radio 2 ID
    RadioID2File.close()
os.chmod(RID2Path, mode=0o764)   # set the permissions to 764
print('Setting Radio 2 ID =', RadioID2)

################################################################
# Get Radio 3 ID info
################################################################
RID3Path = InfoDir + "RadioID3.txt"
# if (path.exists(RID3Path)):
#    with open(RID3Path, 'r') as RadioID3File: # file there - open it
#        RadioID3 = RadioID3File.readline()  # read file contents
#        RadioID3File.close()   # close file
#        print('\nCurrent Saved Radio 3 ID = '+ RadioID3)  # display it

# else:
#   print('\nRadioID3 file not found- creating default')

with open(RID3Path, 'w') as RadioID3File:
    RadioID3 = 'G2R3' # create default Radio ID
    RadioID3File.write(RadioID3) #write default Radio 3 ID
    RadioID3File.close()
os.chmod(RID3Path, mode=0o764)   # set the permissions to 764
print('Setting Radio 3 ID =', RadioID3)

################################################################
# Get Antenna info
################################################################
AntPath = InfoDir + "Antenna.txt"
if (path.exists(AntPath)):
    with open(AntPath, 'r') as AntFile: # file there - open it
        ANT = AntFile.readline()  # read file contents
        AntFile.close()   # close file
        print('\nCurrent Saved Antenna = '+ ANT + '\n')  # display it

else:
    print('\nAntenna file not found- creating default')
    with open(AntPath, 'w') as AntFile:
        ANT = 'Wire Antenna' # create default Antenna
    print('Created default Antenna =', ANT)
CSchng = 0
Done = 0
while Done == 0:
    print('Enter New Antenna [Model Make]')
    NewAnt = input('or <Enter> to keep this one > ')
    if NewAnt == '':
        print('Keeping existing Antenna as ' + ANT)
        NewAnt = ANT
        Done = 1
    else:
        # check to see if entry makes sense
        # firtst check length for correct # of chars
        Antlth = len(NewAnt)
        if  Antlth >= 3:
            print('Correct min Length of '+ str(Antlth) + ' for ' + NewAnt)
            Done =  1
            CSchng = 1
        else:
            print('Wrong min Length of ' + str(Antlth) + ' for '+ NewAnt)

if(CSchng == 1 ): # 0 for keep old number or failed test, 1 for valid entry
    with open(AntPath, 'w') as AntFile:
        AntFile.write(NewAnt) #write new antenna
        AntFile.close()
    os.chmod(AntPath, mode=0o764)   # set the permissions to 764
    ANT = NewAnt  # save entered value on change
    print('New Antenna '+ NewAnt + ' saved\n')
else:
    print('Antenna - no change made')

################################################################
# Get System info
################################################################
SysInfoPath = InfoDir + "System.txt"
if (path.exists(SysInfoPath)):
    with open(SysInfoPath, 'r') as SysInfoFile: # file there - open it
        SysInf = SysInfoFile.readline()  # read file contents
        SysInfoFile.close()   # close file
        print('\nCurrent System Info = '+ SysInf + '\n')  # display it

else:
    print('\nSystem Info file not found- creating default')
    with open(SysInfoPath, 'w') as SysInfoFile:
        SysInf = 'RasPi4B/8GB, RasPi OS Bullseye 6.1.21' # create default system
        SysInfoFile.write(SysInf) #write default system
        SysInfoFile.close()
    os.chmod(SysInfoPath, mode=0o764)   # set the permissions to 764
    print('Created default System Info =', SysInf)
CSchng = 0
Done = 0
while Done == 0:
    print('Enter New System Info [format: CPU, OS, Radio]')
    NewSysInf = input('or <Enter> to keep this one > ')
    if NewSysInf == '':
        NewSysInf = SysInf
        print('Keeping existing System Info as ' + NewSysInf)
        Done = 1
    else:
        # check to see if entry makes sense
        # firtst check length for correct # of chars
        SysInflth = len(NewSysInf)
        if  SysInflth >= 4:
            print('Correct min Length of '+ str(SysInflth) + ' for ' + NewSysInf)
            Done =  1
            CSchng = 1
        else:
            print('Wrong min Length of ' + str(SysInflth) + ' for '+ NewSysInf)

if(CSchng == 1 ): # 0 for keep old number or failed test, 1 for valid entry
    with open(SysInfoPath, 'w') as SysInfoFile:
        SysInfoFile.write(NewSysInf) #write new sysinfo
        SysInfoFile.close()
    os.chmod(SysInfoPath, mode=0o764)   # set the permissions to 764
    print('New System Info of '+ NewSysInf + ' saved\n')
    NewSysInf = NewSysInf + '\n'  # for final printout formatting
else:
    print('System Info - no change made')


################################################################
# Get remaining autogenerated infor for final listing of station info
################################################################

# Get autogenerated GridSquare
GSPath = InfoDir + "GridSqr.txt"
if (path.exists(AntPath)):
    with open(GSPath, 'r') as GSFile: # file there - open it
        GridSqr = GSFile.readline()  # read file contents
        GSFile.close()   # close file
################################################################


################################################################
################################################################
# determine if any of 3 Beacon settings changed

BcnFreqChng = 0

#
################################################################
################################################################
# @@@@

################################################################
# Check for existing Beacon1 setting
################################################################
B1Path = InfoDir + "Beacon1.txt"

## if first time to run create default Beacon1
if (path.exists(B1Path)):
    with open(B1Path, 'r') as B1File: # file there - open it
        OrigB1 = B1File.readline()  # read file contents
        B1File.close()   # close file
        print('\nFound Current Beacon1 = ' + OrigB1 + '\n')  # display it
        B1Chng = 0
else:
    print('\n Beacon1.txt file not found - create initial default Beacon1 = None\n')
    with open(B1Path, 'w') as B1File:
        OrigB1 = 'None' # create default Beacon1
        B1File.write(OrigB1) #write default Beacon1.txt
        B1File.close()
        os.chmod(B1Path, mode=0o764)   # set the permissions to 764
        print('Created Default Beacon1 = ' + OrigB1 + '\n')
        BcnFreqChng = 1
        B1Chng = 1

################################################################
# Get New Beacon 1 setting
################################################################

print('\nEnter Desired Beacon 1 Frequency [0 = None, 1 = CHU 3.33 MHz, 2 = WWV 5 MHz]')
B1Done = 0
while (B1Done == 0):
    NewB1 = input('Enter 0 or 1 or 2 or <Enter> to keep same setting > ')
    if (NewB1 == ''):
        Beacon1 = OrigB1
        if (Beacon1 == 'None'):
            B1FreqSet = 'F10'
        if (Beacon1 == 'CHU3'):
            B1FreqSet = 'F11'
        if (Beacon1 == 'WWV5'):
            B1FreqSet = 'F12'
        B1Done = 1
        B1Chng = 0
        #print('Beacon 1 kept as ' + Beacon1)

    if (NewB1 == '0'):
        Beacon1 = 'None'
        B1FreqSet = 'F10'
        B1Done = 1
        B1Chng = 1
        BcnFreqChng = 1
        print('Beacon 1 is now ' + Beacon1)

    if (NewB1 == '1'):
        Beacon1 = 'CHU3'
        B1FreqSet = 'F11'
        B1Done = 1
        B1Chng = 1
        BcnFreqChng = 1
        print('Beacon 1 is now ' + Beacon1)

    if (NewB1 == '2'):
        Beacon1 = 'WWV5'
        B1FreqSet = 'F12'
        B1Done = 1
        B1Chng = 1
        BcnFreqChng = 1
        print('Beacon 1 is now ' + Beacon1)

if(B1Chng == 1): # 0 for keep old value, 1 for new entry
    with open(B1Path, 'w') as B1File:
        B1File.write(Beacon1) #write new Beacon1
        B1File.close()
    os.chmod(B1Path, mode=0o764)   # set the permissions to 764
    print('xSaved Beacon1.txt = ' + Beacon1 + '\n')

else:
    print('Beacon1 = ' + Beacon1 + ' - no change made')

# exit(0)
################################################################
# Check for existing Beacon2 setting
################################################################
B2Path = InfoDir + "Beacon2.txt"

## if first time to run create default Beacon2
if (path.exists(B2Path)):
    with open(B2Path, 'r') as B2File: # file there - open it
        OrigB2 = B2File.readline()  # read file contents
        B2File.close()   # close file
        print('\nFound Current Beacon2 = '+ OrigB2 + '\n')  # display it
        B2Chng = 0
else:
    print('\n Beacon2.txt file not found - create initial default Beacon2 = None\n')
    with open(B2Path, 'w') as B2File:
        OrigB2 = 'None' # create default Beacon2
        B2File.write(OrigB2) #write default Beacon2.txt
        B2File.close()
        os.chmod(B2Path, mode=0o764)   # set the permissions to 764
        print('Created Default Beacon2 = '+ OrigB2 + '\n')
        BcnFreqChng = 1
        B2Chng = 1

################################################################
# Get New Beacon 2 setting
################################################################

print('\nEnter Desired Beacon 2 Frequency [0 = None, 1 = CHU 7.85 MHz, 2 = WWV 10 MHz]')
B2Done = 0
while (B2Done == 0):
    NewB2 = input('Enter 0 or 1 or 2 or <Enter> to keep same setting > ')
    if (NewB2 == ''):
        Beacon2 = OrigB2
        if (Beacon2 == 'None'):
            B2FreqSet = 'F20'
        if (Beacon2 == 'CHU7'):
            B2FreqSet = 'F21'
        if (Beacon2 == 'WWV10'):
            B2FreqSet = 'F22'
        B2Done = 1
        B2Chng = 0
        #print('Beacon 2 kept as ' + Beacon2)

    if (NewB2 == '0'):
        Beacon2 = 'None'
        B2FreqSet = 'F20'
        B2Done = 1
        B2Chng = 1
        BcnFreqChng = 1
        print('Beacon 2 is now ' + Beacon2)

    if (NewB2 == '1'):
        Beacon2 = 'CHU7'
        B2FreqSet = 'F21'
        B2Done = 1
        B2Chng = 1
        BcnFreqChng = 1
        print('Beacon 2 is now ' + Beacon2)

    if (NewB2 == '2'):
        Beacon2 = 'WWV10'
        B2FreqSet = 'F22'
        B2Done = 1
        B2Chng = 1
        BcnFreqChng = 1
        print('Beacon 2 is now ' + Beacon2)

if(B2Chng == 1): # 0 for keep old value, 1 for new entry
    with open(B2Path, 'w') as B2File:
        B2File.write(Beacon2) #write new Beacon2
        B2File.close()
    os.chmod(B2Path, mode=0o764)   # set the permissions to 764
    print('Saved Beacon2.txt = ' + Beacon2 + '\n')

else:
    print('Beacon2 = ' + Beacon2 + ' - no change made')


################################################################
# Check for existing Beacon3 setting
################################################################
B3Path = InfoDir + "Beacon3.txt"

## if first time to run create default Beacon3
if (path.exists(B3Path)):
    with open(B3Path, 'r') as B3File: # file there - open it
        OrigB3 = B3File.readline()  # read file contents
        B3File.close()   # close file
        print('\nFound Current Beacon3 = '+ OrigB3 + '\n')  # display it
        B3Chng = 0
else:
    print('\n Beacon3.txt file not found - create initial default Beacon3 = None\n')
    with open(B3Path, 'w') as B3File:
        OrigB3 = 'None' # create default Beacon3
        B3File.write(OrigB3) #write default Beacon3.txt
        B3File.close()
        os.chmod(B3Path, mode=0o764)   # set the permissions to 764
        print('Created Default Beacon3 = '+ OrigB3 + '\n')
        BcnFreqChng = 1
        B3Chng = 1

################################################################
# Get New Beacon 3 setting
################################################################

print('\nEnter Desired Beacon 3 Frequency [0 = None, 1 = CHU 14.67 MHz, 2 = WWV 15 MHz]')
B3Done = 0
while (B3Done == 0):
    NewB3 = input('Enter 0 or 1 or 2 or <Enter> to keep same setting > ')
    if (NewB3 == ''):
        Beacon3 = OrigB3
        if (Beacon3 == 'None'):
            B3FreqSet = 'F30'
        if (Beacon3 == 'CHU14'):
            B3FreqSet = 'F31'
        if (Beacon3 == 'WWV15'):
            B3FreqSet = 'F32'
        B3Done = 1
        B3Chng = 0
        #print('Beacon 3 kept as ' + Beacon3)

    if (NewB3 == '0'):
        Beacon3 = 'None'
        B3FreqSet = 'F30'
        B3Done = 1
        B3Chng = 1
        BcnFreqChng = 1
        print('Beacon 3 is now ' + Beacon3)

    if (NewB3 == '1'):
        Beacon3 = 'CHU14'
        B3FreqSet = 'F31'
        B3Done = 1
        B3Chng = 1
        BcnFreqChng = 1
        print('Beacon 3 is now ' + Beacon3)

    if (NewB3 == '2'):
        Beacon3 = 'WWV15'
        B3FreqSet = 'F32'
        B3Done = 1
        B3Chng = 1
        BcnFreqChng = 1
        print('Beacon 3 is now ' + Beacon3)

if(B3Chng == 1): # 0 for keep old value, 1 for new entry
    with open(B3Path, 'w') as B3File:
        B3File.write(Beacon3) #write new Beacon3
        B3File.close()
    os.chmod(B3Path, mode=0o764)   # set the permissions to 764
    print('Saved Beacon3.txt = ' + Beacon3 + '\n')

else:
    print('Beacon3 = ' + Beacon3 + ' - no change made')

################################################################
################################################################
# If any beacon freq changed indicate to OS that the
# existing hours file needs to be deleted and start a
# new one by creating the file NBF as ~/PSWS/Sinfo/NBF

BCPath = CmdDir + "NBF"

if(BcnFreqChng == 1 ): # lookd for flag of freq change
    with open(BCPath, 'w') as BCFile:
        BCFile.write('New Beacon Freq - Delete this hours Srawdata file!') #write new beacon freq flag file
        BCFile.close()
    os.chmod(BCPath, mode=0o764)   # set the permissions to 764
    print('\nIndicated Beacon Freq Changed - Created ' + BCPath + 'to delete existing hour Srawdata file\n')

else:
    print('\nNo Beacon Freq change made - keeping existing hours data\n')

################################################################
################################################################
# Save PICO freq settinga
PICOSetPath = InfoDir + "PICOSetFrq.txt"
# save selected settings
with open(PICOSetPath, 'w') as PICOSetFile:
    PICOSetFile.write('T0A\n') #write PICO Line terminator
    PICOSetFile.write('I2C\n') #write PICO seperation char
    PICOSetFile.write('CDH\n') #write PICO Data in Hexadecimal
    PICOSetFile.write('CCH\n') #write PICO checksum in Hexadecimal
    PICOSetFile.write('F05003E8\n') #write PICO engine control freqs 8 MHz A2DCLK
#    PICOSetFile.write('F0A007D0\n') #write PICO engine control freqs 16 MHz A2DCLK
    PICOSetFile.write(B1FreqSet + '\n') #write PICO Freq Radio 1
    PICOSetFile.write(B2FreqSet + '\n') #write PICO Freq Radio 2
    PICOSetFile.write(B3FreqSet + '\n') #write PICO Freq Radio 3
    PICOSetFile.write('F400\n') #write PICO test Freq off
#    PICOSetFile.write('F408\n') #write PICO test Freq = 5.000000 MHz - WWV5
    PICOSetFile.write('VP\n') #write VP command to report picorun version string
    # Added for debug support 
#    PICOSetFile.write('XP0\n') #write PICO diag mode off
    PICOSetFile.write('XP1\n') #write PICO diag mode on
#    PICOSetFile.write('XR0\n') #write RasPi diag mode 1/2 off
#    PICOSetFile.write('XR1\n') #write RasPi diag mode 1 on
    PICOSetFile.write('XR2\n') #write RasPi diag mode 2 on
    PICOSetFile.close()
os.chmod(PICOSetPath, mode=0o764)   # set the permissions to 764
print('\nCreating PICO Initialization File = ' + PICOSetPath + '\n')

################################################################
# Check for existing zeros cal data file
################################################################
ZeroPath = InfoDir + "zeros.dat"

## if first time to run create default
if (path.exists(ZeroPath)):
    with open(ZeroPath, 'r') as ZeroFile: # file there - open it
        Zeros = ZeroFile.readline()  # read file contents
        ZeroFile.close()   # close file
        print('\nFound zero.dat file  = '+ Zeros + '\n')  # display it
        ZeroChng = 0
else:
    print('\nzeros.dat file not found - creating default\n')
    with open(ZeroPath, 'w') as ZeroFile:
        DefZeros = '7fff,7fff,7fff' # create default Beacon3
        ZeroFile.write(DefZeros) #write default A/D zeros
        ZeroFile.close()
        Zeros = DefZeros   # set to created default values
        os.chmod(ZeroPath, mode=0o764)   # set the permissions to 764
        print('Created Default zeros.dat = '+ DefZeros + '\n')

################################################################
################################################################
# Create header files for usage every day

# LatLonElv = Lat + ',' + Long + ',' + Elev

# print('\n Final Metadata for this station:\n')

print('########################################################');
print('# MetaData for Grape Gen 2 Station');
print('#')
print('# Station Node Number      ' + NewNN)
print('# Callsign                 ' + CallSign)
print('# Grid Square              ' + GridSqr)
print('# Lat, Lon, Elv            ' + LatLonElv)
print('# GPS Fix,PDOP             ' + FixPDOP)
print('# GPS Acquisition on       ' + GPSDateTime)
print('# City State               ' + NewCS)
print('# Radio                    ' + Radio)
print('# RFGain                   ' + RFGain)
print('# Radio1ID                 ' + RadioID1)
print('# Radio2ID                 ' + RadioID2)
print('# Radio3ID                 ' + RadioID3)
print('# Antenna                  ' + NewAnt)
print('# Frequency Standard       ' + FreqStd)
print('# System Info              ' + NewSysInf)
print('# RFDeckSN, LogicCtrlrSN   ' + SerNum)
print(f"# Data Controller Version  {datactrlr_version}")
print(f"# Picorun Version          {picorun_version}")
print(f"# magdata Version          {magdata_version}")
print('# PSWSsetup Version        ' + SWVersion)
print('#')
print('# Beacon 1 Now Decoded     ' + Beacon1)
print('# Beacon 2 Now Decoded     ' + Beacon2)
print('# Beacon 3 Now Decoded     ' + Beacon3)
print('#')
print('# A/D Zero Cal Data        ' + Zeros)
print('#')
print('#########################################################')

################################################################
################################################################
# Create Raw Data Header File Info and save to PSWSinfo.txt
################################################################
PSWSInfoPath = InfoDir + "PSWSinfo.txt"

with open(PSWSInfoPath, 'w') as PSWSInfoFile:
    PSWSInfoFile.write('######################################################\n') #write data line
    PSWSInfoFile.write('# MetaData for Grape Gen 2 Station\n') #write data line
    PSWSInfoFile.write('#\n') #write data line
    PSWSInfoFile.write('# Station Node Number      ' + NewNN + '\n') #write data line
    PSWSInfoFile.write('# Callsign                 ' + CallSign + '\n') #write data line
    PSWSInfoFile.write('# Grid Square              ' + GridSqr + '\n') #write data line
    PSWSInfoFile.write('# Lat, Lon, Elv            ' + LatLonElv + '\n') #write data line
    PSWSInfoFile.write('# GPS Fix,PDOP             ' + FixPDOP + '\n') # write data line
    PSWSInfoFile.write('# GPS Acquisition on       ' + GPSDateTime + '\n') # write data line
    PSWSInfoFile.write('# City State               ' + NewCS + '\n') #write data line
    PSWSInfoFile.write('# Radio                    ' + Radio + '\n') #write data line
    PSWSInfoFile.write('# RFGain                   ' + RFGain + '\n') #write data line
    PSWSInfoFile.write('# RadioID1                 ' + RadioID1 + '\n') #write data line
    PSWSInfoFile.write('# RadioID2                 ' + RadioID2 + '\n') #write data line
    PSWSInfoFile.write('# RadioID3                 ' + RadioID3 + '\n') #write data line
    PSWSInfoFile.write('# Antenna                  ' + ANT + '\n') #write data line
    PSWSInfoFile.write('# Frequency Standard       ' + FreqStd + '\n') #write data line
    PSWSInfoFile.write('# System Info              ' + SysInf + '\n') #write data line
    PSWSInfoFile.write('# RFDeckSN, LogicCtrlrSN   ' + SerNum + '\n') #write data line
    PSWSInfoFile.write(f"# Data Controller Version  {datactrlr_version}" + '\n')
    PSWSInfoFile.write(f"# Picorun Version          {picorun_version}" + '\n')
    PSWSInfoFile.write(f"# magdata Version          {magdata_version}" + '\n')
    PSWSInfoFile.write('# PSWSsetup Version        ' + SWVersion + '\n')
    PSWSInfoFile.write('#\n') #write data line
    PSWSInfoFile.write('# Beacon 1 Now Decoded     ' + Beacon1 + '\n') #write data line
    PSWSInfoFile.write('# Beacon 2 Now Decoded     ' + Beacon2 + '\n') #write data line
    PSWSInfoFile.write('# Beacon 3 Now Decoded     ' + Beacon3 + '\n') #write data line
    PSWSInfoFile.write('#\n') #write data line
    PSWSInfoFile.write('# A/D Zero Cal Data        ' + Zeros + '\n') #write cal zeros data line
    PSWSInfoFile.write('#\n') #write data line
    PSWSInfoFile.write('######################################################\n') #write data line
# save file and update permissions
    PSWSInfoFile.close()

os.chmod(PSWSInfoPath, mode=0o764)   # set the permissions to 764

print("\nSaved file = "  + PSWSInfoPath)
# exit(0)

################################################################
# Create Radio 1 Data Header File Info and save to Radio1Header.txt
################################################################
R1HdrPth = InfoDir + "Radio1Header.txt"

with open(R1HdrPth, 'w') as R1HdrFile:
    R1HdrFile.write('######################################################\n') #write data line
    R1HdrFile.write('# MetaData for Grape Gen 2 Station\n') #write data line
    R1HdrFile.write('#\n') #write data line
    R1HdrFile.write('# Station Node Number      ' + NewNN + '\n') #write data line
    R1HdrFile.write('# Callsign                 ' + CallSign + '\n') #write data line
    R1HdrFile.write('# Grid Square              ' + GridSqr + '\n') #write data line
    R1HdrFile.write('# Lat, Lon, Elv            ' + LatLonElv + '\n') #write data line
    R1HdrFile.write('# GPS Fix,PDOP             ' + FixPDOP + '\n') # write data line
    R1HdrFile.write('# GPS Acquisition on       ' + GPSDateTime + '\n') # write data line
    R1HdrFile.write('# City State               ' + NewCS + '\n') #write data line
    R1HdrFile.write('# Radio                    ' + Radio + '\n') #write data line
    R1HdrFile.write('# RFGain                   ' + RFGain + '\n') #write data line
    R1HdrFile.write('# RadioID1                 ' + RadioID1 + '\n') #write data line
    R1HdrFile.write('# Antenna                  ' + ANT + '\n') #write data line
    R1HdrFile.write('# Frequency Standard       ' + FreqStd + '\n') #write data line
    R1HdrFile.write('# System Info              ' + SysInf + '\n') #write data line
    R1HdrFile.write('# RFDeckSN, LogicCtrlrSN   ' + SerNum + '\n') #write data line
    R1HdrFile.write(f"# Data Controller Version  {datactrlr_version}" + '\n')
    R1HdrFile.write(f"# Picorun Version          {picorun_version}" + '\n')
    R1HdrFile.write(f"# magdata Version          {magdata_version}" + '\n')
    R1HdrFile.write('# PSWSsetup Version        ' + SWVersion + '\n')
    R1HdrFile.write('#\n') #write data line
    R1HdrFile.write('# Beacon 1 Now Decoded     ' + Beacon1 + '\n') #write data line
    R1HdrFile.write('#\n') #write data line
    R1HdrFile.write('######################################################\n') #write data line
    R1HdrFile.write('UTC,Freq,Vrms\n') #write column info line
    R1HdrFile.close() # save file and update permissions

os.chmod(R1HdrPth, mode=0o764)   # set the permissions to 764
print("Saved file = " + R1HdrPth)
# exit(0)
################################################################
# Create Radio 2 Data Header File Info and save to Radio1Header.txt
################################################################
R2HdrPth = InfoDir + "Radio2Header.txt"

with open(R2HdrPth, 'w') as R2HdrFile:
    R2HdrFile.write('######################################################\n') #write data line
    R2HdrFile.write('# MetaData for Grape Gen 2 Station\n') #write data line
    R2HdrFile.write('#\n') #write data line
    R2HdrFile.write('# Station Node Number      ' + NewNN + '\n') #write data line
    R2HdrFile.write('# Callsign                 ' + CallSign + '\n') #write data line
    R2HdrFile.write('# Grid Square              ' + GridSqr + '\n') #write data line
    R2HdrFile.write('# Lat, Lon, Elv            ' + LatLonElv + '\n') #write data line
    R2HdrFile.write('# GPS Fix,PDOP             ' + FixPDOP + '\n') # write data line
    R2HdrFile.write('# GPS Acquisition on       ' + GPSDateTime + '\n') # write data line
    R2HdrFile.write('# City State               ' + NewCS + '\n') #write data line
    R2HdrFile.write('# Radio                    ' + Radio + '\n') #write data line
    R2HdrFile.write('# RFGain                   ' + RFGain + '\n') #write data line
    R2HdrFile.write('# RadioID2                 ' + RadioID2 + '\n') #write data line
    R2HdrFile.write('# Antenna                  ' + ANT + '\n') #write data line
    R2HdrFile.write('# Frequency Standard       ' + FreqStd + '\n') #write data line
    R2HdrFile.write('# System Info              ' + SysInf + '\n') #write data line
    R2HdrFile.write('# RFDeckSN, LogicCtrlrSN   ' + SerNum + '\n') #write data line
    R2HdrFile.write(f"# Data Controller Version  {datactrlr_version}" + '\n')
    R2HdrFile.write(f"# Picorun Version          {picorun_version}" + '\n')
    R2HdrFile.write(f"# magdata Version          {magdata_version}" + '\n')
    R2HdrFile.write('# PSWSsetup Version        ' + SWVersion + '\n')
    R2HdrFile.write('#\n') #write data line
    R2HdrFile.write('# Beacon 2 Now Decoded     ' + Beacon2 + '\n') #write data line
    R2HdrFile.write('#\n') #write data line
    R2HdrFile.write('######################################################\n') #write data line
    R2HdrFile.write('UTC,Freq,Vrms\n') #write column info line
    R2HdrFile.close() # save file and update permissions
os.chmod(R2HdrPth, mode=0o764)   # set the permissions to 764
print('Saved file = ' + R2HdrPth)
# exit(0)
################################################################
# Create Radio 3 Data Header File Info and save to Radio1Header.txt
################################################################
R3HdrPth = InfoDir + "Radio3Header.txt"

with open(R3HdrPth, 'w') as R3HdrFile:
    R3HdrFile.write('######################################################\n') #write data line
    R3HdrFile.write('# MetaData for Grape Gen 2 Station\n') #write data line
    R3HdrFile.write('#\n') #write data line
    R3HdrFile.write('# Station Node Number      ' + NewNN + '\n') #write data line
    R3HdrFile.write('# Callsign                 ' + CallSign + '\n') #write data line
    R3HdrFile.write('# Grid Square              ' + GridSqr + '\n') #write data line
    R3HdrFile.write('# Lat, Lon, Elv            ' + LatLonElv + '\n') #write data line
    R3HdrFile.write('# GPS Fix,PDOP             ' + FixPDOP + '\n') # write data line
    R3HdrFile.write('# GPS Acquisition on       ' + GPSDateTime + '\n') # write data line
    R3HdrFile.write('# City State               ' + NewCS + '\n') #write data line
    R3HdrFile.write('# Radio                    ' + Radio + '\n') #write data line
    R3HdrFile.write('# RFGain                   ' + RFGain + '\n') #write data line
    R3HdrFile.write('# RadioID3                 ' + RadioID3 + '\n') #write data line
    R3HdrFile.write('# Antenna                  ' + ANT + '\n') #write data line
    R3HdrFile.write('# Frequency Standard       ' + FreqStd + '\n') #write data line
    R3HdrFile.write('# System Info              ' + SysInf + '\n') #write data line
    R3HdrFile.write('# RFDeckSN, LogicCtrlrSN   ' + SerNum + '\n') #write data line
    R3HdrFile.write(f"# Data Controller Version  {datactrlr_version}" + '\n')
    R3HdrFile.write(f"# Picorun Version          {picorun_version}" + '\n')
    R3HdrFile.write(f"# magdata Version          {magdata_version}" + '\n')
    R3HdrFile.write('# PSWSsetup Version        ' + SWVersion + '\n')
    R3HdrFile.write('#\n') #write data line
    R3HdrFile.write('# Beacon 3 Now Decoded     ' + Beacon3 + '\n') #write data line
    R3HdrFile.write('#\n') #write data line
    R3HdrFile.write('######################################################\n') #write data line
    R3HdrFile.write('UTC,Freq,Vrms\n') #write column info line
    R3HdrFile.close() # save file and update permissions

os.chmod(R3HdrPth, mode=0o764)   # set the permissions to 764
print('Saved file = ' + R3HdrPth)
# exit(0)
################################################################
# Create Magnetometer Header File Info and save to MAGTMPHeader.txt
################################################################
MAGTMPHdrPth = InfoDir + "MAGTMPHeader.txt"

with open(MAGTMPHdrPth, 'w') as MAGTMPHdrFile:
    MAGTMPHdrFile.write('######################################################\n') #write data line
    MAGTMPHdrFile.write('# MetaData for Grape Gen 2 Station\n') #write data line
    MAGTMPHdrFile.write('#\n') #write data line
    MAGTMPHdrFile.write('# Station Node Number      ' + NewNN + '\n') #write data line
    MAGTMPHdrFile.write('# Callsign                 ' + CallSign + '\n') #write data line
    MAGTMPHdrFile.write('# Grid Square              ' + GridSqr + '\n') #write data line
    MAGTMPHdrFile.write('# Lat, Lon, Elv            ' + LatLonElv + '\n') #write data line
    MAGTMPHdrFile.write('# GPS Fix,PDOP             ' + FixPDOP + '\n') # write data line
    MAGTMPHdrFile.write('# GPS Acquisition on       ' + GPSDateTime + '\n') # write data line
    MAGTMPHdrFile.write('# City State               ' + NewCS + '\n') #write data line
    MAGTMPHdrFile.write('# Radio                    ' + Radio + '\n') #write data line
    MAGTMPHdrFile.write('# Magnetometer             ' + "RM3100" + '\n') #write data line
    MAGTMPHdrFile.write('# Temp Sensors             ' + "MCP9808" + '\n') #write data line
    MAGTMPHdrFile.write('# System Info              ' + SysInf + '\n') #write data line
    MAGTMPHdrFile.write('# RFDeckSN, LogicCtrlrSN   ' + SerNum + '\n') #write data line
    MAGTMPHdrFile.write(f"# Data Controller Version  {datactrlr_version}" + '\n')
    MAGTMPHdrFile.write(f"# Picorun Version          {picorun_version}" + '\n')
    MAGTMPHdrFile.write(f"# magdata Version          {magdata_version}" + '\n')
    MAGTMPHdrFile.write('# PSWSsetup Version        ' + SWVersion + '\n')
    MAGTMPHdrFile.write('#\n') #write data line
    MAGTMPHdrFile.write('######################################################\n') #write data line
    MAGTMPHdrFile.write('UTC,SysTemp C,RemoteTemp C,Mx(nT),My(nT),Mz(nT)\n') #write column info line
    MAGTMPHdrFile.close() # save file and update permissions

os.chmod(MAGTMPHdrPth, mode=0o764)   # set the permissions to 764
print('Saved file = ' + MAGTMPHdrPth)
# aya.exit(0)
################################################################
################################################################
################################################################
# All done - indicate so to user
print('\nPSWS file structure / System Info Program Exiting Gracefully')
sys.exit(0)
################################################################
################################################################
################################################################

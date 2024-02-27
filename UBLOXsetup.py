#!/usr/bin/env python3

"""
Author: Cuong Nguyen

Python tool to set the baudrate of the UBLOX 
Date        Version     Author  Comments
01-26-24    Ver 1.00    KC3UAX  Initial commit


Python tool to set the timepulse of the UBLOX
Date        Version     Author  Comments
01-30-24    Ver 1.00    KC3UAX  Initial commit
01-31-24    Ver 2.00    KC3UAX  Added polling TIMEPULSE(1) config

Composite tool to recover from UBLOX hardware reset
Author: JC Gibbons
Date        Version     Author  Comments
02-11-24    Ver 1.00    N8OBJ   Initial start of UBLOX Utility program
02-14-24    Ver 2.00    KC3UAX  Added message to save all configs

"""
# import the GPIO and time package
import RPi.GPIO as GPIO
import time
from serial import Serial
from pyubx2 import SET, POLL, UBXMessage, UBXReader

# Do a hardware reset of the UBLOX NEO-8MT GPS module
# send 1.0 second reset (low) pulse to UBLOX rcvr on GPIO26

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
# Set up UBLOX Reset Out pin
GPIO.setup(26, GPIO.OUT) # GPSRST Output

print('UBLOX NEO-8MT Initialization Program Ver 1.0\n')

print('Asserting UBLOX Reset -> 0')
GPIO.output(26,0) # Assert Reset LOW

time.sleep(1.0)

print('Releasing UBLOX Reset -> 1')
GPIO.output(26,1) # Release GPSRESET

# GPIO.cleanup()
time.sleep(1.0)
print ('waiting 1.0 sec...\n')

# setup UBLOX baud rate from 9600 Baud to 115.2 KBaud
desired_baudrate = 115200
portID = 1 # Port ID of UART
message = UBXMessage(
        "CFG",
        "CFG-PRT",
        SET,
        portID=portID,
        charLen=3,  # 8 data bits
        parity=4,  # none
        nStopBits=0,  # 1 stop bit
        baudRate=desired_baudrate,
        inUBX=1,
        inNMEA=1,
        inRTCM=1,
        inRTCM3=0,
        outUBX=1,
        outNMEA=1,
        outRTCM3=0,
    )

port = "/dev/ttyS0"
baudrate = 9600
timeout = 0.1

with Serial(port, baudrate, timeout=timeout) as serial:
    print("Now Setting the UBLOX Baudrate to 115.2 KBaud...")
    serial.write(message.serialize())
    print('Command sent...\n')

# wait 1 more second
time.sleep(1.0)
print ('waiting 1.0 sec...\n')

## setup UBLOX pulse settings
# message0 = UBXMessage("CFG", "CFG-TP5", POLL, payload=b"\x00")
message1 = UBXMessage("CFG", "CFG-TP5", POLL, payload=b"\x01")

# Message to Save all Settings to Battery Backed RAM, and flash
saveMessage = UBXMessage(
    "CFG",
    "CFG-CFG",
    SET,
    saveMask=b"\x1f\x1f\x00\x00",  # save everything
    devBBR=1,  # save to battery-backed RAM
    devFlash=1,  # save to flash
)

port = "/dev/ttyS0"
timeout = 0.1
baudrate = 115200

with Serial(port, baudrate, timeout=timeout) as serial:
    ubr = UBXReader(serial)

    # print("Polling @115.2 KB for TIMEPULSE setting from the UBLOX GPS module...")
    # serial.write(message0.serialize())
    # print("Command sent...\n")
    # (raw_data, parsed_data) = ubr.read()
    # print('Retrieved data:\n',parsed_data)

    print("\nPolling for TIMEPULSE2 setting from the UBLOX GPS module...")
    serial.write(message1.serialize())
    print("Command sent...\n")
    (raw_data, parsed_data) = ubr.read()
    print('Retrieved data:\n',parsed_data)

    print("\nSaving all current configurations...")
    serial.write(saveMessage.serialize())
    print("Command sent...\n")
    (raw_data, parsed_data) = ubr.read()
    print('Retrieved data:\n',parsed_data)


print('Initialization Completed\n\n')

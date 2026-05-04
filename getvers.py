#
# getvers.py
#
# Get current Grape 2 version numbers
#

import os
import subprocess
from subprocess import Popen, PIPE
from datetime import datetime

date = datetime.now().strftime("%m/%d/%Y %H:%M:%S")

# Run datactrlr and parse the results to get version numbers
datactrlr = subprocess.Popen(['sudo', '/home/pi/G2User/datactrlr'], stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True)
stdout, stderr = datactrlr.communicate("q\n")
for line in stdout.splitlines():
    if "data controller" in line.lower():
        datactrlr_version = line.strip().split("v")[-1]
    elif "picorun version" in line.lower():
        picorun_version = line.strip().split(" ")[-1]
    elif "fail" in line.lower():
        print(line)

# Run magdata -v to get version number
magdata = subprocess.Popen( ["sudo", "/home/pi/G2User/magdata", "-v"], stdout=PIPE, stderr=PIPE, text=True)
magdata_out, magdata_err = magdata.communicate()
magdata_version = magdata_out.strip().split()[-1]

# Run G2console.py -v to get version number
console = subprocess.Popen( ["python3", "/home/pi/G2User/G2console.py", "-v"], stdout=PIPE, stderr=PIPE, text=True)
console_out, console_err = console.communicate()
console_version = console_out.strip().split("v")[-1]

# Print the versions
print(f"{date} Current Grape2 Versions")
print(f"G2console:       {console_version}")
print(f"DataController:  {datactrlr_version}")
print(f"Picorun:         {picorun_version}")
print(f"Magdata:         {magdata_version}")



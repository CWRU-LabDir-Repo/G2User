# G2uploader.py
#
# Upload Grape 2 data files to the PSWS repository.
#
# Original author:  Bill Engelke AB4EJ
# Grape 1&2 mods:   Bill Blackwell AB1XB
#
# This script (G2uploader.py) is run by a cron job once daily at 00:nn UTC, where "nn"
# is the station node number.
#
# The uploader uploads all files in the G2DATA/Sxfer directory to the PSWS repository.
# It deletes files in the Sxfer directory that were successfully uploaded.
#
# Note:
# -----
# The sftp command used in this script requires the PSWS host key to be installed in the user's $HOME/.ssh/known_hosts file.
# Since the Grape 2 uploader runs under sudo privileges, the key must be installed in the root user's known_hosts file.
# The key is also installed in the pi user's known_hosts file for convenience of the pi user.
# To install the keys, run the following two commands:
#
#   sudo sftp [station-id]@pswsnetwork.eng.ua.edu
#   sftp [station-id]@pswsnetwork.eng.ua.edu
#
# [station-id] is the value of 'thestationid' in /home/pi/PSWS/Sinfo/uploader.config.
# When prompted for password, enter the value of 'token_value' in the same file.
#
# In each case sftp will respond:
#
#   The authenticity of host 'pswsnetwork.eng.ua.edu ([psws ip address])' can't be established.
#   ECDSA key fingerprint is [psws fingerprint].
#   Are you sure you want to continue connecting (yes/no/[fingerprint])?
#
# Enter 'yes' to this prompt and the key will be installed.
#


import os
from datetime import datetime, timezone
import time
import configparser
import glob

# Counters
n_ok = 0
n_err = 0

def DR_pending():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M')

def log_time():
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

def upload_file(source_path, obs, instrumentID, targetDir, triggerPfx):
    if instrumentID != "" and triggerPfx != "":
        triggerDir = triggerPfx + obs + "_#" + instrumentID + "_#" + DR_pending()
    else:
        triggerDir = ""
    command = "lftp " \
        + "-e '" \
        + "set net:limit-rate " + throttle + "; " \
        + "cd " + targetDir + "; " \
        + "put " + source_path + obs + "; " \
        + "chmod 775 " + obs + "; "
    if triggerDir != "":
        command = command \
        + "cd .. ; " \
        + "mkdir " + triggerDir + "; " \
        + "chmod 775 " + triggerDir + "; "
    command = command \
        + "exit" \
        + "' " \
        + "-u " + theStationID + "," + theToken + " " \
        + "sftp://" + central_host + " "

#    print('Upload command = "' + command + '"', flush=True)
#    return 0
    print("Starting upload...", flush=True)
    return os.system(command)

def upload_file_set(source_path, template, instrumentID, targetDir, triggerPfx):
    global n_ok
    global n_err
    files = glob.glob(source_path + template)
    files.sort()
    for file_path in files:
        file_name = os.path.basename(file_path)

        print("Will attempt to upload observation " + file_name, flush=True)
        scode = upload_file(source_path, file_name, instrumentID, targetDir, triggerPfx)
        if scode == 0:
            n_ok += 1
            print("Upload succeeded", flush=True)
            # Remove file if upload succeeded
            os.remove(source_path + file_name)
        else:
            n_err += 1
            print("Upload failed", flush=True)

print("Upload started: " + log_time(), flush=True)

# Read settings
parser = configparser.ConfigParser(allow_no_value=True)
parser.read('/home/pi/PSWS/Sinfo/uploader.config')

# Get global profile settings
theStationID   = parser['profile']['theStationID']
theToken       = parser['profile']['token_value']  # Do not share this or post publicly
central_host   = parser['profile']['central_host']

# Get spectrum settings
throttle       = parser['spectrum_settings']['throttle']
source_path    = parser['spectrum_settings']['spectrum_storage'] + "/"
instrumentID   = parser['spectrum_settings']['instrumentID']
targetDir      = parser['spectrum_settings']['targetDir']

# Upload spectrum data
upload_file_set(source_path, "*_G2R*_FRQ_*.csv", instrumentID, targetDir, "g")

# Upload spectrum plots
upload_file_set(source_path, "*_WWV*_graph.png", instrumentID, "plots", "")

# Get optional magnetometer settings
mag_present = False
try:
    instrumentID   = parser['mag_settings']['instrumentID']
    targetDir      = parser['mag_settings']['targetDir']
    mag_present = True
except:
    pass

# Catch exceptions in upload_file_set() separately from above
if mag_present:
    # Upload mag data
    upload_file_set(source_path, "*_MAGTMP.csv", instrumentID, targetDir, "m")

    # Upload mag plots
    upload_file_set(source_path, "*_MAGTMP_*.png", instrumentID, "plots", "")

# Upload logs
upload_file_set(source_path, "*logs.zip", "", "logs", "")

# Print stats
print("Number of file uploads succeeded: " + str(n_ok) + ", failed: " + str(n_err), flush=True)
if n_err > 0:
    print("Failed uploads will be tried again tomorrow", flush=True)
print("Upload ended: " + log_time(), flush=True)


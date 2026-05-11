#
# patch_headers.py
#
# Patch header files to update current version numbers posted in versions.stat.
# The header files are prepended to log files and data files.
#
# Author: AB1XB
#

import os
import sys
import time
import shutil
from datetime import datetime

def read_version_file(ver_path):
    global new_console_ver, new_dc_ver, new_pico_ver, new_mag_ver
    versions = []
    with open(ver_path, 'r') as vfile:
        vline = vfile.read()
        vtokens = vline.split()
        for i, vtoken in enumerate(vtokens):
            if vtoken == "G2console":
                versions.append(["G2console Version", vtokens[i+1]])
            elif vtoken == "datactrlr":
                versions.append(["Data Controller Version", vtokens[i+1]])
            elif vtoken == "picorun":
                versions.append(["Picorun Version", vtokens[i+1]])
            elif vtoken == "magdata":
                versions.append(["magdata Version", vtokens[i+1]])
    vfile.close()
    return versions

def patch_line_version(line, version_label, newver):
    if version_label in line:

        # Split into max 2 parts at the search string
        parts = line.split(version_label, 1)

        if len(parts) > 1:
            # Take the remaining text, strip leading spaces, and grab the first word
            oldver = parts[1].strip().split()[0]
            print(f"{version_label} previous: {oldver} current: {newver}")

            if oldver != newver:
                return 2, line.replace(oldver, newver)
            else:
                return 1, None

    return 0, None

def patch_lines(lines, versions):
    patched = False
    for v, (label, ver) in enumerate(versions):
        found = False
        for i, line in enumerate(lines):
            status, newline = patch_line_version(line, label, ver)
            if status > 0:
                found = True
            if newline is not None:
                if status == 2:
                    lines[i] = newline
                    patched = True
                    break
        if not found:
            print(f"{label} not found")
            # re-enumerate the list and find the first line containing "Version"
            for i, line in enumerate(lines):
                if "Version" in line:
                    # insert the newline before this line
                    newline = f"# {label:<25}{ver:<20}\n"
                    lines.insert(i, newline)
                    patched = True
                    break
    return patched

def patch_file(path_name, file_name, versions):
    try:
        infile = os.path.join(path_name, file_name)
        print(f"Patching file {infile}")
        with open(infile, 'r') as file:
            lines = file.readlines()
            patched = patch_lines(lines, versions)
            file.close()

            if patched:
                # write the new file
                outfile = os.path.join(path_name, f"tmp{file_name}")
                print(f"Updating file {infile}")
                with open(outfile, 'w') as file2:
                    for line in lines:
                        file2.write(line)
                file2.close()
                os.rename(outfile, infile)
                shutil.chown(infile, user='pi', group='pi')

    except Exception as ex:
        print("Exception in patch_file(): " + str(ex))
        raise


# main

try:

    print(datetime.now().strftime("%m/%d/%Y %H:%M:%S ") + "patch_headers.py")
    print("sleep 60 seconds to give console time to write versions.stat...")
    time.sleep(60.0)
    versions = read_version_file("/home/pi/PSWS/Sstat/versions.stat")

    path = '/home/pi/PSWS/Sinfo'
    patch_file(path, 'PSWSinfo.txt', versions)
    patch_file(path, 'MAGTMPHeader.txt', versions)
    patch_file(path, 'Radio1Header.txt', versions)
    patch_file(path, 'Radio2Header.txt', versions)
    patch_file(path, 'Radio3Header.txt', versions)

except Exception as ex:
    print("Terminating program due to exception: " + str(ex))
    sys.exit(1)


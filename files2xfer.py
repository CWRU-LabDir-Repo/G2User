"""
Author: Cuong Nguyen

Python tool to copy yesterday's files to xfer
and store the radio filenames for plot generation

Date        Version     Author  Comments
02-29-24    Ver 1.00    KC3UAX  Initial commit

"""
import os
import shutil
from datetime import datetime, timedelta


radio_files = []


def copy_radio_files(date_str, dest_dir):
    global radio_files
    directories = [
        "/home/pi/G2DATA/SdataR1/",
        "/home/pi/G2DATA/SdataR2/",
        "/home/pi/G2DATA/SdataR3/",
    ]
    # Copy files from each directory to /G2DATA/Sxfer/
    for directory in directories:
        for file_name in os.listdir(directory):
            if date_str in file_name:
                source_path = os.path.join(directory, file_name)
                dest_path = os.path.join(dest_dir, file_name)
                shutil.copyfile(source_path, dest_path)
                print(f"Copied {file_name} to {dest_dir}")
                radio_files.append(source_path)


def copy_mag_files(date_str, dest_dir):
    semaphore_file = "/home/pi/PSWS/Scmd/magtmp"
    directory = "/home/pi/G2DATA/Smagtmp/"
    if os.path.exists(semaphore_file):
        # Copy magnetometer file to /G2DATA/Sxfer/
        for file_name in os.listdir(directory):
            if date_str in file_name:
                source_path = os.path.join(directory, file_name)
                dest_path = os.path.join(dest_dir, file_name)
                shutil.copyfile(source_path, dest_path)
                print(f"Copied {file_name} to {dest_dir}")


def copy_log_files(date_str, dest_dir):
    directory = "/home/pi/G2DATA/Slogs/"
    # Copy log file to /G2DATA/Sxfer/
    for file_name in os.listdir(directory):
        if date_str in file_name:
            source_path = os.path.join(directory, file_name)
            dest_path = os.path.join(dest_dir, file_name)
            shutil.copyfile(source_path, dest_path)
            print(f"Copied {file_name} to {dest_dir}")


def copy_yesterday_files():
    # Calculate yesterday's date
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    xfer_dir = "/home/pi/G2DATA/Sxfer/"

    copy_mag_files(yesterday_str, xfer_dir)
    copy_radio_files(yesterday_str, xfer_dir)
    copy_log_files(yesterday_str, xfer_dir)


def write_filenames():
    global radio_files
    dest_file = "/home/pi/PSWS/Scmd/f2t.txt"
    with open(dest_file, "w") as f:
        for radio_file in radio_files:
            f.write(radio_file + "\n")
            print(f"Written {radio_file} to {dest_file}")


if __name__ == "__main__":
    copy_yesterday_files()
    write_filenames()

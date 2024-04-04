#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon July 1 2020
Full Beacon (WWV / CHU) plotting of 2 input fomats
added hours ticks, removed time from UTC dat in header, added zero ref line for doppler freq shift, Elv now Elev  7-31=20 JCG
added autoplot capability 11/21/20 jgibbons
added autoxfer, autoplot on/off capability, fixed .png filename format problem  (RadioID <-> GridSqr) 1-29-2021
@authors dkazdan jgibbons cnguyen

Date        Version     Author      Comments
03-14-24    Ver 1.00    jgibbons    Initial commit
03-15-24    Ver 2.00    KC3UAX      Continue adapting script for G2
03-15-24    Ver 3.00    KC3UAX      Fixed timestring conversion, ylim, and saving files in the appropriate directories
03-24-24    Ver 3.01    KC3UAX      Accepts filenames from either stdin or command parameters
03-24-24    Ver 3.02    KC3UAX      Fixes frequency line, removes colons in output filenames
03-28-24    Ver 3.03    KC3UAX      Fixes dopper shift calculation
03-28-24    Ver 3.04    KC3UAX      Change power axis label and range. Enable vertical grid.
04-04-24    Ver 3.05    KC3UAX      dBV -> dBVrms
04-04-24    Ver 3.06    KC3UAX      fix vertical grid. add options
04-04-24    Ver 3.07    KC3UAX      added a version option
"""
import os
import sys
import numpy as np
import pandas as pd
from scipy import signal
import matplotlib.pyplot as plt
import argparse

version = '3.07'


# ~ points to users home directory - usually /home/pi/
home_path = os.path.expanduser("~") + "/G2DATA/"

# saved plot directrory
plot_dir = home_path + "Splot/"

# transfer directory  (files to be sent to server node)
xfer_dir = home_path + "Sxfer/"

beacon_frequencies = {
    "WWV2p5": ("2.5 MHz", "WWV"),
    "WWV5": ("5 MHz", "WWV"),
    "WWV10": ("10 MHz", "WWV"),
    "WWV15": ("15 MHz", "WWV"),
    "WWV20": ("20 MHz", "WWV"),
    "WWV25": ("25 MHz", "WWV"),
    "CHU3": ("3.330 MHz", "CHU"),
    "CHU7": ("7.850 MHz", "CHU"),
    "CHU14": ("14.670 MHz", "CHU"),
    "Unknown": ("0", "Unknown Beacon"),
}


def time_string_to_decimals(time_string):  # returns float decimal hours
    time_string = time_string[11:-1]  # Hack off date 'YYYY-MM-DDT' and ending 'Z'
    fields = time_string.split(":")
    hours = float(fields[0]) if len(fields) > 0 else 0.0
    minutes = float(fields[1]) / 60.0 if len(fields) > 0 else 0.0
    seconds = float(fields[2]) / 3600.0 if len(fields) > 0 else 0.0
    return hours + minutes + seconds


def read_file(data_file: str):
    metadata = {}
    with open(data_file, "r") as file:
        header = file.readline().strip().split(",")
        metadata["UTCDTZ"] = header[1]
        metadata["UTC_DT"] = header[1][:10]
        metadata["Node"] = header[2]
        metadata["GridSqr"] = header[3]
        metadata["Lat"] = header[4]
        metadata["Long"] = header[5]
        metadata["Elev"] = header[6]
        metadata["CityState"] = header[7]
        metadata["RadioID"] = header[8]
        metadata["Beacon"] = header[9]
        metadata["UTCDTZ"] = metadata["UTCDTZ"].replace(":", "")
        data = pd.read_csv(file, comment="#")
    return data, metadata


def process_data(data: pd.DataFrame):
    SQRT2 = np.sqrt(2)
    data["UTC"] = data["UTC"].apply(lambda x: time_string_to_decimals(x))
    data["Power_dB"] = 20 * np.log(data["Vrms"] / SQRT2)

    print("Vrms min: ", data["Vrms"].min(), "; Vrms max: ", data["Vrms"].max())
    print("dB min: ", data["Power_dB"].min(), "; dB max: ", data["Power_dB"].max())


def create_filter(data: pd.DataFrame, beacon_freq):
    # %% Create an order 3 lowpass butterworth filter.
    # This is a digital filter (analog=False)
    # Filtering at .01 to .004 times the Nyquist rate seems "about right."
    # The filtering argument (Wn, the second argument to butter()) of.01
    # represents filtering at .05 Hz, or 20 second weighted averaging.
    # That corresponds with the 20 second symmetric averaging window used in the 1 October 2019
    # Excel spreadsheet for the Festival of Frequency Measurement data.
    FILTERBREAK = 0.005  # filter breakpoint in Nyquist rates. N. rate here is 1/sec, so this is in Hz.
    FILTERORDER = 6
    b, a = signal.butter(FILTERORDER, FILTERBREAK, analog=False, btype="low")

    # Use the just-created filter coefficients for a noncausal filtering (filtfilt is forward-backward noncausal)
    filt_doppler = signal.filtfilt(b, a, data["Freq"] - beacon_freq)
    print("Doppler min: ", filt_doppler.min(), "; Doppler max: ", filt_doppler.max())
    print(f"Beacon Frequency: {beacon_freq}")

    filt_power = signal.filtfilt(b, a, data["Power_dB"])
    return filt_doppler, filt_power


def plot_data(data, filt_doppler, filt_power, metadata):
    ##%% modified from "Double-y axis plot,
    ## http://kitchingroup.cheme.cmu.edu/blog/2013/09/13/Plotting-two-datasets-with-very-different-scales/

    # set up x-axis with time
    fig = plt.figure(figsize=(19, 10))  # inches x, y with 72 dots per inch
    ax1 = fig.add_subplot(111)
    ax1.plot(data["UTC"], filt_doppler, "k")  # color k for black
    ax1.set_xlabel("UTC Hour")
    ax1.set_ylabel("Doppler shift, Hz")
    ax1.set_xlim(0, 24)  # UTC day
    ax1.set_xticks(range(25), minor=False)
    ax1.set_ylim([-1.5, 1.5])  # -1.5 to 1.5 Hz for Doppler shift
    if args.grid:
        print("Grid enabled")
        ax1.grid(axis="x")
    # plot a zero freq reference line for 0.000 Hz Doppler shift
    plt.axhline(y=0, color="gray", lw=1)
    # set up axis 2 in red
    ax2 = ax1.twinx()
    ax2.plot(data["UTC"], filt_power, "r-")  # NOTE: Set for filtered version
    ax2.set_ylabel("dBVrms", color="r")
    ax2.set_ylim(-160, 0)  # Try these as defaults to keep graphs similar.
    for tl in ax2.get_yticklabels():
        tl.set_color("r")

    freq, label = beacon_frequencies[metadata["Beacon"]]
    print(f"Final Plot for Decoded {freq} {label} Beacon")
    beacon_label = f"{label} {freq}"

    # plt.grid(axis="x")
    plt.title(
        beacon_label
        + " Doppler Shift Plot\nNode:  "
        + metadata["Node"]
        + "     Gridsquare:  "
        + metadata["GridSqr"]
        + "\nLat= "
        + metadata["Lat"]
        + "    Long= "
        + metadata["Long"]
        + "    Elev= "
        + metadata["Elev"]
        + " m\n"
        + metadata["UTC_DT"]
        + "  UTC"
    )


def create_plot_file(data_file: str):
    data, metadata = read_file(data_file)

    print("Ready to start processing records")
    process_data(data)

    filt_doppler, filt_power = create_filter(
        data, float(beacon_frequencies[metadata["Beacon"]][0].split()[0]) * 10**6
    )
    plot_data(data, filt_doppler, filt_power, metadata)

    graph_file = (
        metadata["UTCDTZ"]
        + "_"
        + metadata["Node"]
        + "_"
        + metadata["RadioID"]
        + "_"
        + metadata["GridSqr"]
        + "_"
        + metadata["Beacon"]
        + "_graph.png"
    )
    plot_graph_file = plot_dir + graph_file
    xfer_graph_file = xfer_dir + graph_file

    # create plot
    plt.savefig(plot_graph_file, dpi=250, orientation="landscape")
    plt.savefig(xfer_graph_file, dpi=250, orientation="landscape")

    print(
        "Plot File: " + graph_file + "\n"
    )  # indicate plot file name for crontab printout


if __name__ == "__main__":
    # Create the argument parser
    parser = argparse.ArgumentParser(description='Grape 2 Plot Generator')

    # Add the argument
    parser.add_argument('-v', '--version', action='version', version=f'%(prog)s v{version}', help='show g2plot version')
    parser.add_argument('filenames', help='input file', type=str, nargs="*", default=sys.stdin)
    parser.add_argument('-g', "--grid", help='enable vertical grid', nargs="?", const=True, default=False)

    # Parse the arguments
    args = parser.parse_args()
    
    for file in args.filenames:
        print('Input file:', file)
        create_plot_file(file.strip())

    print("Exiting python combined processing program gracefully")
    sys.exit(0)

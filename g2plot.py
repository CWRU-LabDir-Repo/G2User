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
04-15-24    Ver 3.09    KC3UAX      grid enable option now can be specified either before or after filenames, and require no argument
04-16-24    Ver 3.10    KC3UAX      added -x option to enable creating plots in the xfer directory
04-22-24    Ver 3.11    KC3UAX      fixed multi-dimensional indexing end-of-support
04-24-24    Ver 4.0     KC3UAX      Added magtmp plot generator and suppress DeprecationWarning (PyArrow)
04-25-24    Ver 4.1     KC3UAX      Fixed bugs, improved performance, and added filtering to mag data
04-29-24    Ver 4.2     KC3UAX      Added rolling average and remote temp
05-22-24    Ver 5.0     KC3UAX      Added plotting 3 mag components separately
05-23-24    Ver 5.1     KC3UAX      Modifed magnetometer plots: font size, added mean to legend
"""
import os
import sys
import numpy as np
import pandas as pd
import warnings
from scipy import signal
import matplotlib
import matplotlib.pyplot as plt
import argparse

warnings.filterwarnings("ignore", category=DeprecationWarning)
# configure non-interactive backend to speed plot saving
matplotlib.use("Agg")
plt.rcParams["font.size"] = 13

version = "5.1"


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
        metadata["UTCDTZ"] = header[1].replace(":", "")
        metadata["UTC_DT"] = header[1][:10]
        metadata["Node"] = header[2]
        metadata["GridSqr"] = header[3]
        metadata["Lat"] = header[4]
        metadata["Long"] = header[5]
        metadata["Elev"] = header[6]
        metadata["CityState"] = header[7]
        if "MAGTMP" not in data_file:
            metadata["RadioID"] = header[8]
            metadata["Beacon"] = header[9]
        data = pd.read_csv(file, comment="#")
    return data, metadata


def process_data(data: pd.DataFrame):
    data["UTC"] = data["UTC"].apply(lambda x: time_string_to_decimals(x))
    if any("Mx" in col for col in data.columns):
        # if any column contains Mag (for Magnetometer)
        data["B(nT)"] = (
              (data["Mx(uT)"]*1000) ** 2
            + (data["My(uT)"]*1000) ** 2
            + (data["Mz(uT)"]*1000) ** 2
        ) ** 0.5
        print("Raw B(nT) min: ", data["B(nT)"].min(), "; Raw B(nT) max: ", data["B(nT)"].max())
    else:
        SQRT2 = np.sqrt(2)
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


def plot_radio_data(data, filt_doppler, filt_power, metadata):
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


def plot_component_mag_data(data: pd.DataFrame, metadata):
    xmean = data["Mx(uT)"].mean()
    ymean = data["My(uT)"].mean()
    zmean = data["Mz(uT)"].mean()
    x_centered = (data["Mx(uT)"] - xmean).rolling(60).mean()*1000
    y_centered = (data["My(uT)"] - ymean).rolling(60).mean()*1000
    z_centered = (data["Mz(uT)"] - zmean).rolling(60).mean()*1000
    print(
        "∆Bx(nT) min: ",
        x_centered.min(),
        "; ∆Bx(nT) max: ",
        x_centered.max(),
    )
    print(
        "∆By(nT) min: ",
        y_centered.min(),
        "; ∆By(nT) max: ",
        y_centered.max(),
    )
    print(
        "∆Bz(nT) min: ",
        z_centered.min(),
        "; ∆Bz(nT) max: ",
        z_centered.max(),
    )    
    
    # set up x-axis with time
    fig = plt.figure(figsize=(19, 10))  # inches x, y with 72 dots per inch
    ax1 = fig.add_subplot(111)
    ax1.plot(data["UTC"], x_centered, "k", label=f"Bx (Mean: {round(xmean*1000)}nT)")  # color k for black
    ax1.plot(data["UTC"], y_centered, "r", label=f"By (Mean: {round(ymean*1000)}nT)")  # color k for black
    ax1.plot(data["UTC"], z_centered, "b", label=f"Bz (Mean: {round(zmean*1000)}nT)")  # color k for black
    ax1.legend() 
    ax1.set_xlabel("UTC Hour")
    ax1.set_ylabel("∆B(nT)")
    ax1.set_xlim(0, 24)  # UTC day
    ax1.set_xticks(range(25), minor=False)
    # ax.set_ylim([-1.5, 1.5])
    if args.grid:
        print("Grid enabled")
        ax1.grid(axis="x")

    plt.title(
        "Magnetometer Plot (Component)\nNode:  "
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

    graph_file = (
        metadata["UTCDTZ"]
        + "_"
        + metadata["Node"]
        + "_"
        + metadata["GridSqr"]
        + "_MAGTMP_COMPONENT.png"
    )
    plot_graph_file = plot_dir + graph_file
    xfer_graph_file = xfer_dir + graph_file

    print("Plot File: " + graph_file)  # indicate plot file name for crontab printout

    # create plot
    plt.savefig(plot_graph_file, dpi=100, orientation="landscape")
    print("Plot saved to", plot_dir)
    if args.xfer:
        plt.savefig(xfer_graph_file, dpi=100, orientation="landscape")
        print("Plot saved to", xfer_dir)

    print()


def plot_composite_mag_data(data: pd.DataFrame, metadata):
    composite_mag = data["B(nT)"].rolling(60).mean()
    print("Composite mag min: ", composite_mag.min(), "; Composite mag max: ", composite_mag.max())
    
    # set up x-axis with time
    fig = plt.figure(figsize=(19, 10))  # inches x, y with 72 dots per inch
    ax1 = fig.add_subplot(111)
    ax1.plot(data["UTC"], composite_mag, "k")  # color k for black
    ax1.set_xlabel("UTC Hour")
    ax1.set_ylabel("B(nT)")
    ax1.set_xlim(0, 24)  # UTC day
    ax1.set_xticks(range(25), minor=False)
    # ax.set_ylim([-1.5, 1.5])
    if args.grid:
        print("Grid enabled")
        ax1.grid(axis="x")

    ax2 = ax1.twinx()
    ax2.plot(
        data["UTC"], data["RemTmp C"].rolling(120).mean(), "r-"
    )  # NOTE: Set for filtered version
    ax2.set_ylabel("Remote Temperature (C)", color="r")
    # ax2.set_ylim(-160, 0)
    for tl in ax2.get_yticklabels():
        tl.set_color("r")

    plt.title(
        "Magnetometer Plot (Composite)\nNode:  "
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

    graph_file = (
        metadata["UTCDTZ"]
        + "_"
        + metadata["Node"]
        + "_"
        + metadata["GridSqr"]
        + "_MAGTMP_COMPOSITE.png"
    )
    plot_graph_file = plot_dir + graph_file
    xfer_graph_file = xfer_dir + graph_file

    print("Plot File: " + graph_file)  # indicate plot file name for crontab printout

    # create plot
    plt.savefig(plot_graph_file, dpi=100, orientation="landscape")
    print("Plot saved to", plot_dir)
    if args.xfer:
        plt.savefig(xfer_graph_file, dpi=100, orientation="landscape")
        print("Plot saved to", xfer_dir)


def create_radio_plot_file(data_file: str):
    data, metadata = read_file(data_file)

    print("Ready to start processing records")
    process_data(data)

    filt_doppler, filt_power = create_filter(
        data, float(beacon_frequencies[metadata["Beacon"]][0].split()[0]) * 10**6
    )
    plot_radio_data(data, filt_doppler, filt_power, metadata)

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

    print("Plot File: " + graph_file)  # indicate plot file name for crontab printout

    # create plot
    plt.savefig(plot_graph_file, dpi=100, orientation="landscape")
    print("Plot saved to", plot_dir)
    if args.xfer:
        plt.savefig(xfer_graph_file, dpi=100, orientation="landscape")
        print("Plot saved to", xfer_dir)


def create_mag_plot_file(data_file: str):
    data, metadata = read_file(data_file)

    print("Ready to start processing records")
    process_data(data)
    print()
    
    plot_composite_mag_data(data, metadata)
    print()
    plot_component_mag_data(data, metadata)


if __name__ == "__main__":
    # Create the argument parser
    parser = argparse.ArgumentParser(description="Grape 2 Plot Generator")

    # Add the argument
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s v{version}",
        help="show g2plot version",
    )
    parser.add_argument(
        "filenames", help="input file", type=str, nargs="*", default=sys.stdin
    )
    parser.add_argument(
        "-g", "--grid", help="enable vertical grid", action="store_true"
    )
    parser.add_argument(
        "-x",
        "--xfer",
        help="enable creating plots in the xfer directory to be uploaded to server",
        action="store_true",
    )

    # Parse the arguments
    args = parser.parse_args()

    for file in args.filenames:
        print("Input file:", file)
        if "MAGTMP" in file:
            create_mag_plot_file(file.strip())
        else:
            create_radio_plot_file(file.strip())

    print("Exiting python combined processing program gracefully")
    sys.exit(0)

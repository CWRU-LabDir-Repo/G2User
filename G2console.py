import os
import re
import json
import time
import psutil
import curses
import threading
import subprocess
from datetime import datetime
from collections import deque
from serial import Serial
from pynmeagps import NMEAReader
from gpsdclient import GPSDClient


# Constants for modes
MODE_DAILY = "daily"
MODE_HOURLY = "hourly"

def is_process_running(process_name):
    for process in psutil.process_iter(["pid", "name"]):
        if process.info["name"] == process_name:
            return True
    return False


class DailyMinMaxCollection:
    def __init__(self, max_elements=24):
        self.max_elements = max_elements
        self.collection = deque(maxlen=max_elements)

    def update_bounds(self, current_value, timestamp):
        if timestamp[11:15] == "0000" or len(self.collection) == 0:
            hour_data = {
                "max": current_value,
                "current": current_value,
                "min": current_value,
            }
            self.collection.append(hour_data)
        else:
            self.collection[-1]["current"] = current_value
            if current_value > self.collection[-1]["max"]:
                self.collection[-1]["max"] = current_value
            if current_value < self.collection[-1]["min"]:
                self.collection[-1]["min"] = current_value

    def get_daily_max(self, mode):
        if not self.collection:
            return None
        
        if mode == MODE_DAILY:
            return max(hour_data["max"] for hour_data in self.collection)
        else:
            return self.collection[-1]["max"]

    def get_daily_min(self, mode):
        if not self.collection:
            return None

        if mode == MODE_DAILY:
            return min(hour_data["min"] for hour_data in self.collection)
        else:
            return self.collection[-1]["min"]
        
    def get_current(self):
        if not self.collection:
            return None
        return self.collection[-1]["current"]

    def __repr__(self):
        return f"HourlyMinMaxCollection={list(self.collection)}"


freqs = [DailyMinMaxCollection() for _ in range(3)]
ampls = [DailyMinMaxCollection() for _ in range(3)]
mag = [DailyMinMaxCollection() for _ in range(3)]
last_data = ""
gps_data = {"lat": 0.0, "lon": 0.0, "elev": 0.0, "pdop": 0.0}
exited = False
mode = MODE_HOURLY

def saddstr(stdscr, y, x, string):
    max_y, max_x = stdscr.getmaxyx()
    if 0 <= y < max_y and 0 <= x < max_x:
        stdscr.addstr(y, x, string)


def data_reader():
    global last_data
    with open(pipe_path) as fifo:
        for line in fifo:
            if exited:
                break
            try:
                last_data = parse_json(line)
            except Exception as e:
                log.write("\n")
                log.write(datetime.now().strftime("%m/%d/%Y %H:%M:%S"))
                log.write(" -> ")
                log.write(str(e))
                log.write(",")
                log.write(line.replace("\0", ""))


def gps_reader():
    global gps_data, exited, log
    if not is_process_running("gpsd"):
        port = '/dev/ttyS0'
        baud_rate = 115200

        with Serial(port, baud_rate, timeout=3) as stream:
            nmr = NMEAReader(stream, quitonerror=0)
            while not exited:
                try:
                    _, parsed_data = nmr.read()
                    if parsed_data.msgID == "GSA":
                        gps_data["pdop"] = parsed_data.PDOP
                    elif parsed_data.msgID == "GGA":
                        gps_data["lat"] = parsed_data.lat
                        gps_data["lon"] = parsed_data.lon
                        gps_data["elev"] = parsed_data.alt
                    time.sleep(0.5)
                except Exception as e:
                    log.write("\n")
                    log.write(datetime.now().strftime("%m/%d/%Y %H:%M:%S"))
                    log.write(" -> ")
                    log.write(str(e))
    else:
        with GPSDClient() as client:
            while not exited:
                tpv_str = next(client.dict_stream(filter=["TPV"]))
                gps_data["lat"] = float(tpv_str.get("lat", "0.0"))
                gps_data["lon"] = float(tpv_str.get("lon", "0.0"))
                gps_data["elev"] = float(tpv_str.get("alt", "0.0"))
                sky_str = next(client.dict_stream(filter=["SKY"]))
                while sky_str.get("pdop", "n/a") == "n/a":
                    sky_str = next(client.dict_stream(filter=["SKY"]))
                gps_data["pdop"] = float(sky_str.get("pdop", "0.0"))


def parse_json(line):
    try:
        line = line.strip().replace("\0", "")
        data = json.loads(
            line,
            parse_float=lambda x: x,
            parse_int=lambda x: x,
            parse_constant=lambda x: x,
        )
        for i in range(3):
            current_ampl = float(data["radios"][i]["ampl"])
            ampls[i].update_bounds(current_ampl, data["ts"])
            current_freq = float(data["radios"][i]["freq"])
            freqs[i].update_bounds(current_freq, data["ts"])
        for i, axis in enumerate(["x", "y", "z"]):
            current_axis_val = float(data[axis])
            mag[i].update_bounds(current_axis_val, data["ts"])
        return data
    except json.JSONDecodeError as e:
        if len(line) > 10:
            log.write(repr(line))
            log.write("\n")
            log.flush()
            regex_pattern = r"(-?nan|-?inf)"
            replacement = "0.0"

            line = re.sub(regex_pattern, replacement, line)
            return json.loads(
                line,
                parse_float=lambda x: x,
                parse_int=lambda x: x,
                parse_constant=lambda x: x,
            )
        else:
            return ""


def print_title(stdscr):
    saddstr(stdscr, 0, 22, "Grape2 Console v9.2")
    nextrow = 1
    return nextrow


def print_version_widget(stdscr, row):
    saddstr(stdscr, row, 23, "Firmware Versions")
    versions = [("RasPi", "rver"), ("Pico", "pver")]
    for i, (label, key) in enumerate(versions):
        saddstr(stdscr, row + 1 + i, 26, label)
    return row + 3


def print_version(stdscr, row, data):
    versions = [("RasPi", "rver"), ("Pico", "pver")]
    for i, (label, key) in enumerate(versions):
        ver_string = data[key]
        elements = ver_string.split(".")
        elements[-1] = elements[-1].rjust(2, "0")
        saddstr(stdscr, row + 1 + i, 32, ".".join(elements))


def print_datetime_widget(stdscr, row):
    saddstr(stdscr, row + 1, 0, "GPS Date/Time")
    saddstr(stdscr, row + 2, 0, "Displayed Data")
    return row + 3


def print_gps_time(stdscr, row):
    sys_datetime = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    saddstr(stdscr, row, 22, sys_datetime)


def print_data_time(stdscr, row, data):
    dt_object = datetime.strptime(data["ts"][1:15], "%Y%m%d%H%M%S")
    gps_datetime = dt_object.strftime("%m/%d/%Y %H:%M:%S")
    saddstr(stdscr, row, 22, gps_datetime)


def print_datetime(stdscr, row, data):
    print_gps_time(stdscr, row + 1)
    print_data_time(stdscr, row + 2, data)


def print_gps_widget(stdscr, row):
    saddstr(stdscr, row + 1, 0, "UBLOX GPS")
    saddstr(stdscr, row + 1, 18, "Fix")
    saddstr(stdscr, row + 1, 27, "#Sats")
    saddstr(stdscr, row + 1, 36, "PDOP")
    saddstr(stdscr, row + 4, 17, "Latitude")
    saddstr(stdscr, row + 4, 32, "Longitude")
    saddstr(stdscr, row + 4, 45, "Elevation(M)")
    return row + 6

def print_gps(stdscr, row, data):
    lock_string = ""
    if data["ts"][15] == "U" or data["ts"][15] == "X":
        lock_string = "0"
    elif data["ts"][16] == "0" or data["ts"][16] == "1":
        lock_string = "0"
    else:
        lock_string = data["ts"][16] + "D"
    saddstr(stdscr, row + 2, 18, lock_string.ljust(2))
    saddstr(stdscr, row + 2, 28, str(int(data["ts"][17], 16)).ljust(2))
    saddstr(stdscr, row + 2, 36, str(gps_data["pdop"]))
    saddstr(stdscr, row + 5, 15, ("{0:.6f}".format(gps_data["lat"])).rjust(11))
    saddstr(stdscr, row + 5, 30, ("{0:.6f}".format(gps_data["lon"])).rjust(11))
    saddstr(stdscr, row + 5, 47, ("{0:.1f}".format(gps_data["elev"])).rjust(6))


def print_beacon_widget(stdscr, row):
    saddstr(stdscr, row + 1, 17, "Radio 1")
    saddstr(stdscr, row + 1, 32, "Radio 2")
    saddstr(stdscr, row + 1, 47, "Radio 3")
    saddstr(stdscr, row + 2, 0, "Beacon")
    return row + 3


def print_beacon(stdscr, row, data):
    for i in range(3):
        #BUG: line 234 TypeError: string indices must be integers
        saddstr(stdscr, row + 2, 18 + 15 * i, data["radios"][i]["beacon"].ljust(5))


def print_ampl_widget(stdscr, row):
    saddstr(stdscr, row + 1, 0, "Signal Level")
    saddstr(stdscr, row + 1, 18, "Vpeak")
    saddstr(stdscr, row + 1, 33, "Vpeak")
    saddstr(stdscr, row + 1, 48, "Vpeak")
    saddstr(stdscr, row + 3, 0, "Current")
    return row + 5


def print_ampl(stdscr, row):
    for i in range(3):
        if ampls[i].get_daily_max(mode) != None:
            max_str_value = "{0:.6f}".format(ampls[i].get_daily_max(mode))
        else:
            max_str_value = ""
        if ampls[i].get_daily_min(mode) != None:
            min_str_value = "{0:.6f}".format(ampls[i].get_daily_min(mode))
        else:
            min_str_value = ""
        if ampls[i].get_current() != None:
            curr_str_value = "{0:.6f}".format(ampls[i].get_current())
        else:
            curr_str_value = ""
        saddstr(stdscr, row + 2, 17 + 15 * i, max_str_value.rjust(8))
        saddstr(stdscr, row + 3, 17 + 15 * i, curr_str_value.rjust(8))
        saddstr(stdscr, row + 4, 17 + 15 * i, min_str_value.rjust(8))
    if mode == MODE_DAILY:
        saddstr(stdscr, row + 2, 0, "MAX 24 hr")
        saddstr(stdscr, row + 4, 0, "MIN 24 hr")
    else:
        saddstr(stdscr, row + 2, 0, "MAX 1 hr ")
        saddstr(stdscr, row + 4, 0, "MIN 1 hr ")


def print_freq_widget(stdscr, row):
    saddstr(stdscr, row + 1, 0, "Frequency")
    saddstr(stdscr, row + 1, 20, "Hz")
    saddstr(stdscr, row + 1, 35, "Hz")
    saddstr(stdscr, row + 1, 50, "Hz")
    saddstr(stdscr, row + 3, 0, "Current")
    return row + 5


def print_freq(stdscr, row):
    for i in range(3):
        if freqs[i].get_daily_max(mode) != None:
            max_str_value = "{0:.3f}".format(freqs[i].get_daily_max(mode))
        else:
            max_str_value = ""
        if freqs[i].get_daily_min(mode) != None:
            min_str_value = "{0:.3f}".format(freqs[i].get_daily_min(mode))
        else:
            min_str_value = ""
        if freqs[i].get_current() != None:
            curr_str_value = "{0:.3f}".format(freqs[i].get_current())
        else:
            curr_str_value = ""
        saddstr(stdscr, row + 2, 15 + 15 * i, max_str_value.rjust(12))
        saddstr(stdscr, row + 3, 15 + 15 * i, curr_str_value.rjust(12))
        saddstr(stdscr, row + 4, 15 + 15 * i, min_str_value.rjust(12))
    if mode == MODE_DAILY:
        saddstr(stdscr, row + 2, 0, "MAX 24 hr")
        saddstr(stdscr, row + 4, 0, "MIN 24 hr")
    else:
        saddstr(stdscr, row + 2, 0, "MAX 1 hr ")
        saddstr(stdscr, row + 4, 0, "MIN 1 hr ")
    # log.write("\n")
    # log.write(freqs.__repr__())


def print_temp_widget(stdscr, row):
    saddstr(stdscr, row + 1, 0, "Temp(C)")
    saddstr(stdscr, row + 1, 17, "Local")
    saddstr(stdscr, row + 1, 32, "Remote")
    return row + 3


def print_temp(stdscr, row, data):
    saddstr(stdscr, row + 2, 17, data["ltemp"].ljust(5))
    saddstr(stdscr, row + 2, 32, data["rtemp"].ljust(5))


def print_mag_widget(stdscr, row):
    saddstr(stdscr, row + 1, 0, "Magnetometer")
    saddstr(stdscr, row + 2, 0, "B Field")
    saddstr(stdscr, row + 2, 17, "X(uT)")
    saddstr(stdscr, row + 2, 32, "Y(uT)")
    saddstr(stdscr, row + 2, 47, "Z(uT)")
    saddstr(stdscr, row + 4, 0, "Current")
    return row + 6


def print_mag(stdscr, row):
    for i, axis in enumerate(["x", "y", "z"]):
        if mag[i].get_daily_max(mode) != None:
            max_str_value = "{0:.3f}".format(mag[i].get_daily_max(mode))
        else:
            max_str_value = ""
        if mag[i].get_daily_min(mode) != None:
            min_str_value = "{0:.3f}".format(mag[i].get_daily_min(mode))
        else:
            min_str_value = ""
        if mag[i].get_current() != None:
            curr_str_value = "{0:.3f}".format(mag[i].get_current())
        else:
            curr_str_value = ""
        saddstr(stdscr, row + 3, 16 + 15 * i, max_str_value.rjust(7))
        saddstr(stdscr, row + 4, 16 + 15 * i, curr_str_value.rjust(7))
        saddstr(stdscr, row + 5, 16 + 15 * i, min_str_value.rjust(7))
    if mode == MODE_DAILY:
        saddstr(stdscr, row + 3, 0, "MAX 24 hr")
        saddstr(stdscr, row + 5, 0, "MIN 24 hr")
    else:
        saddstr(stdscr, row + 3, 0, "MAX 1 hr ")
        saddstr(stdscr, row + 5, 0, "MIN 1 hr ")


def update_ui(stdscr):
    global mode, exited
    # TODO: do NOT terminate statmon on pipe close
    end_of_title = print_title(stdscr)
    end_of_version = print_version_widget(stdscr, end_of_title)
    end_of_datetime = print_datetime_widget(stdscr, end_of_version)
    end_of_gps = print_gps_widget(stdscr, end_of_datetime)
    end_of_beacon = print_beacon_widget(stdscr, end_of_gps)
    end_of_ampl = print_ampl_widget(stdscr, end_of_beacon)
    end_of_freq = print_freq_widget(stdscr, end_of_ampl)
    end_of_temp = print_temp_widget(stdscr, end_of_freq)
    end_of_mag = print_mag_widget(stdscr, end_of_temp)
    saddstr(stdscr, end_of_mag + 2, 6, "<ctrl-p> = toggle for 1Hr/24Hr Min/Max   ")

    program_name = "datactrlr"
    while not is_process_running(program_name):
        saddstr(stdscr, end_of_mag + 1, 6, "<r> = start Data Controller             ")
        stdscr.refresh()

        char = stdscr.getch()
        if char != curses.ERR and char == 114:  # statmon detected r
            saddstr(stdscr, end_of_mag + 1, 6, "Starting the Data Controller...          ")
            stdscr.refresh()

            dclog = "/home/pi/G2DATA/Slogs/dc.log"
            datactrlr = subprocess.Popen(
                ["sudo", "/home/pi/pico/Grape2/PICOCode/picorun/datactrlr"],
                stdin=subprocess.PIPE,
                stdout=open(dclog, "a"),
                stderr=subprocess.STDOUT,
            )

            datactrlr.stdin.write(b"r\n")
            datactrlr.stdin.flush()

            break

    if not "datactrlr" in locals():
        saddstr(
            stdscr,
            end_of_mag + 1,
            6,
            "Data Controller runs in another terminal",
        )
        stdscr.refresh()
    else:
        saddstr(
            stdscr,
            end_of_mag + 1,
            6,
            "<ctrl-x> = terminate Data Controller    ",
        )

    data_reader_thread = threading.Thread(target=data_reader)
    data_reader_thread.start()
    gps_reader_thread = threading.Thread(target=gps_reader)
    gps_reader_thread.start()
    try:
        while data_reader_thread.is_alive():
            if last_data != "":
                print_version(stdscr, end_of_title, last_data)
                print_datetime(stdscr, end_of_version, last_data)
                print_gps(stdscr, end_of_datetime, last_data)
                print_beacon(stdscr, end_of_gps, last_data)
                print_ampl(stdscr, end_of_beacon)
                print_freq(stdscr, end_of_ampl)
                print_temp(stdscr, end_of_freq, last_data)
                print_mag(stdscr, end_of_temp)
                stdscr.refresh()

                char = stdscr.getch()
                if "datactrlr" in locals():
                    if char != curses.ERR and char == 24:
                        datactrlr.stdin.write(b"\x1b")
                        datactrlr.stdin.flush()
                        saddstr(
                            stdscr,
                            end_of_mag + 1,
                            6,
                            "Stopping the Data Controller...           ",
                        )
                        stdscr.refresh()
                        datactrlr.stdin.write(b"q\n")
                        datactrlr.stdin.flush()
                if char != curses.ERR and char == 16: # Detected Ctrl+p
                    mode = MODE_DAILY if mode == MODE_HOURLY else MODE_HOURLY
                stdscr.refresh()
    except KeyboardInterrupt:
        saddstr(
            stdscr,
            end_of_mag + 1,
            6,
            "Terminating the Console...              ",
        )
        stdscr.refresh()
    finally:
        exited = True
    data_reader_thread.join()
    gps_reader_thread.join()


def main(stdscr):
    curses.curs_set(0)  # hide cursor
    curses.halfdelay(5)
    curses.init_pair(
        1, curses.COLOR_GREEN, curses.COLOR_BLACK
    )  # (color pair #, foreground, background)
    stdscr.attron(curses.color_pair(1))  # Set default color pair
    update_ui(stdscr)


if __name__ == "__main__":
    pipe_path = "/home/pi/PSWS/Sstat/datamon.fifo"
    log_path = "/home/pi/G2DATA/Slogs/"
    log_file = "statmon.log"
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    log = open(os.path.join(log_path, log_file), "a")

    curses.wrapper(main)

    log.close()

import argparse
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
from pynmeagps import NMEAReader, NMEAMessage
from gpsdclient import GPSDClient

version = "12.12"

# Constants for modes
MODE_DAILY = 0
MODE_HOURLY = 1


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
            if abs(current_value) > abs(self.collection[-1]["max"]):
                self.collection[-1]["max"] = current_value
            if abs(current_value) < abs(self.collection[-1]["min"]):
                self.collection[-1]["min"] = current_value

    def get_daily_max(self, mode):
        if not self.collection:
            return None

        if mode == MODE_DAILY:
            return max(
                (
                    (hour_data["max"], abs(hour_data["max"]))
                    for hour_data in self.collection
                ),
                key=lambda x: x[1],
            )[0]
        else:
            return self.collection[-1]["max"]

    def get_daily_min(self, mode):
        if not self.collection:
            return None

        if mode == MODE_DAILY:
            return min(
                (
                    (hour_data["min"], abs(hour_data["min"]))
                    for hour_data in self.collection
                ),
                key=lambda x: x[1],
            )[0]
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
gps_data = {
    "time": "00:00:00",
    "day": "00",
    "month": "00",
    "year": "0000",
    "lat": 0.0,
    "lon": 0.0,
    "elev": 0.0,
    "pdop": 0.0,
    "fix": "0",
    "nsats": 0,
}
exited = False
mode = MODE_DAILY


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
                log.write("BEGIN datar exception\n")
                log.write(datetime.now().strftime("%m/%d/%Y %H:%M:%S") + "\n")
                log.write(str(e) + "\n")
                log.write(line.replace("\0", "") + "\n")
                log.write("END datar exception\n")
                log.flush()


def count_sats(data):
    nsats = 0
    for index in range(1, 13):
        svid_field = f"svid_{index:02d}"
        value = getattr(data, svid_field)
        if isinstance(value, int):
            nsats += 1
    return nsats


def gps_reader():
    global gps_data, exited, log
    if not is_process_running("gpsd"):
        port = "/dev/ttyS0"
        baud_rate = 115200
        sat_count_flag = True  # if True, can nsats count is valid

        with Serial(port, baud_rate, timeout=None) as stream:
            nmr = NMEAReader(stream, quitonerror=0)
            while not exited:
                _, parsed_data = nmr.read()
                if not isinstance(parsed_data, NMEAMessage):
                    continue

                try:
                    if "D" in gps_data["fix"] and parsed_data.msgID == "GGA":
                        try:
                            gps_data["lat"] = float(parsed_data.lat)
                        except:
                            gps_data["lat"] = 0.0
                        try:
                            gps_data["lon"] = float(parsed_data.lon)
                        except:
                            gps_data["lon"] = 0.0
                        try:
                            gps_data["elev"] = float(parsed_data.alt)
                        except:
                            gps_data["elev"] = 0.0
                        sat_count_flag = True
                    elif parsed_data.msgID == "GSA":
                        try:
                            gps_data["pdop"] = float(parsed_data.PDOP)
                        except:
                            gps_data["pdop"] = 0.0
                        try:
                            gps_data["fix"] = (
                                "0"
                                if parsed_data.navMode == 1
                                else str(parsed_data.navMode) + "D"
                            )
                        except:
                            gps_data["fix"] = "0"

                        if not sat_count_flag:
                            continue
                        nsats = 0
                        while (
                            isinstance(parsed_data, NMEAMessage)
                            and parsed_data.msgID == "GSA"
                        ):
                            nsats += count_sats(parsed_data)
                            _, parsed_data = nmr.read()
                        if isinstance(parsed_data, NMEAMessage):
                            gps_data["nsats"] = nsats
                        else:
                            sat_count_flag = False
                    elif "D" in gps_data["fix"] and parsed_data.msgID == "ZDA":
                        try:
                            gps_data["time"] = parsed_data.time
                        except:
                            gps_data["time"] = "00:00:00"
                        try:
                            gps_data["year"] = str(parsed_data.year)
                        except:
                            gps_data["year"] = "0000"
                        try:
                            gps_data["month"] = str(parsed_data.month)
                        except:
                            gps_data["month"] = "00"
                        try:
                            gps_data["day"] = str(parsed_data.day)
                        except:
                            gps_data["day"] = "00"
                    else:
                        sat_count_flag = True
                except Exception as e:
                    log.write("BEGIN gpsr exception\n")
                    log.write(datetime.now().strftime("%m/%d/%Y %H:%M:%S") + "\n")
                    log.write(f'"{parsed_data}"\n')
                    log.write(str(e) + "\n")
                    log.write("END gpsr exception\n")
                    log.flush()

    else:
        # TEST: need more testing
        with GPSDClient() as client:
            fix_quality = 0
            while not exited:
                tpv_str = next(client.dict_stream(filter=["TPV"]))
                gps_data["lat"] = tpv_str.get("lat", 0.0)
                gps_data["lon"] = tpv_str.get("lon", 0.0)
                gps_data["elev"] = tpv_str.get("alt", 0.0)
                fix_quality = tpv_str.get("mode", 0)
                if fix_quality == 2 | fix_quality == 3:
                    gps_data["fix"] = str(fix_quality) + "D"
                else:
                    gps_data["fix"] = "0"
                sky_str = next(client.dict_stream(filter=["SKY"]))
                while sky_str.get("pdop", "n/a") == "n/a":
                    sky_str = next(client.dict_stream(filter=["SKY"]))
                gps_data["pdop"] = sky_str.get("pdop", 0.0)
                gps_data["nsats"] = sky_str.get("uSat", 0)


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
            log.write("BEGIN jsonparser exception\n")
            log.write(repr(line))
            regex_pattern = r"(-?nan|-?inf|null)"
            replacement = "0.0"

            line = re.sub(regex_pattern, replacement, line)
            log.write(repr(line))
            log.write("END jsonparser exception\n")
            log.flush()
            return json.loads(
                line,
                parse_float=lambda x: x,
                parse_int=lambda x: x,
                parse_constant=lambda x: x,
            )
        else:
            return ""


def print_title(stdscr):
    saddstr(stdscr, 0, 22, f"Grape2 Console {version}")
    saddstr(stdscr, 1, 24, "Node: ")
    with open("/home/pi/PSWS/Sinfo/NodeNum.txt") as file:
        saddstr(stdscr, 1, 30, file.readline().strip())
    nextrow = 2
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
    saddstr(stdscr, row + 1, 0, "GPS UTC Date/Time")
    return row + 2


def print_gps_time(stdscr, row):
    saddstr(
        stdscr,
        row + 1,
        22,
        f"{gps_data['month'].zfill(2)}/{gps_data['day'].zfill(2)}/{gps_data['year'].zfill(4)} {gps_data['time']}",
    )
    return row + 2


def print_gps_widget(stdscr, row):
    saddstr(stdscr, row + 1, 0, "UBLOX GPS")
    saddstr(stdscr, row + 1, 18, "Fix")
    saddstr(stdscr, row + 1, 27, "#Sats")
    saddstr(stdscr, row + 1, 36, "PDOP")
    saddstr(stdscr, row + 4, 0, "RF Gain")
    with open("/home/pi/PSWS/Sinfo/RFGain.txt") as file:
        saddstr(stdscr, row + 5, 2, file.readline().strip())
    saddstr(stdscr, row + 4, 17, "Latitude")
    saddstr(stdscr, row + 4, 32, "Longitude")
    saddstr(stdscr, row + 4, 45, "Elevation(m)")
    return row + 6


def print_gps(stdscr, row):
    saddstr(stdscr, row + 2, 18, gps_data["fix"].ljust(2))
    saddstr(stdscr, row + 2, 28, str(gps_data["nsats"]).ljust(2))
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
        # BUG: line 234 TypeError: string indices must be integers
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
        saddstr(stdscr, row + 3, 15 + 15 * i, max_str_value.rjust(8))
        saddstr(stdscr, row + 4, 15 + 15 * i, curr_str_value.rjust(8))
        saddstr(stdscr, row + 5, 15 + 15 * i, min_str_value.rjust(8))
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
    saddstr(
        stdscr, end_of_mag + 2, 6, "<ctrl-p> = toggle for 1Hr/24Hr Min/Max            "
    )

    program_name = "datactrlr"
    while not is_process_running(program_name):
        saddstr(
            stdscr,
            end_of_mag + 1,
            6,
            "<r> = start Data Controller                        ",
        )
        stdscr.refresh()

        char = stdscr.getch()
        if (char != curses.ERR and char == 114) or (args.autorun):  # statmon detected r
            saddstr(
                stdscr,
                end_of_mag + 1,
                6,
                "Starting the Data Controller...                ",
            )
            stdscr.refresh()

            datactrlr = subprocess.Popen(
                ["sudo", "/home/pi/G2User/datactrlr", "-l"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            datactrlr.stdin.write(b"r\n")
            datactrlr.stdin.flush()
            time.sleep(0.1)

    if not "datactrlr" in locals():
        saddstr(
            stdscr,
            end_of_mag + 1,
            6,
            "Data Controller is running in another terminal",
        )
        stdscr.refresh()
    else:
        saddstr(
            stdscr,
            end_of_mag + 1,
            6,
            "<ctrl-x> = terminate Data Controller              ",
        )

    data_reader_thread = threading.Thread(target=data_reader)
    data_reader_thread.start()
    gps_reader_thread = threading.Thread(target=gps_reader)
    gps_reader_thread.start()
    try:
        while data_reader_thread.is_alive():
            if last_data != "":
                print_version(stdscr, end_of_title, last_data)
                print_gps_time(stdscr, end_of_version)
                print_gps(stdscr, end_of_datetime)
                print_beacon(stdscr, end_of_gps, last_data)
                print_ampl(stdscr, end_of_beacon)
                print_freq(stdscr, end_of_ampl)
                print_temp(stdscr, end_of_freq, last_data)
                print_mag(stdscr, end_of_temp)
                stdscr.refresh()

                char = stdscr.getch()
                if char != curses.ERR and char == 24:
                    if "datactrlr" in locals():
                        saddstr(
                            stdscr,
                            end_of_mag + 1,
                            6,
                            "Stopping the Data Controller...                    ",
                        )
                        stdscr.refresh()
                        datactrlr.stdin.write(b"\x1b")
                        datactrlr.stdin.flush()
                        time.sleep(0.1)
                        datactrlr.stdin.write(b"q\n")
                        datactrlr.stdin.flush()
                        time.sleep(0.1)
                    else:
                        saddstr(
                            stdscr,
                            end_of_mag + 1,
                            6,
                            "Terminating the Console...                         ",
                        )
                        stdscr.refresh()
                        break
                if char != curses.ERR and char == 16:  # Detected Ctrl+p
                    mode = MODE_DAILY if mode == MODE_HOURLY else MODE_HOURLY
                stdscr.refresh()
    except KeyboardInterrupt:
        saddstr(
            stdscr,
            end_of_mag + 1,
            6,
            "Terminating the Console...                         ",
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
    # Create the argument parser
    parser = argparse.ArgumentParser(description="Grape 2 Console")

    # Add the argument
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s v{version}",
        help="show g2console version",
    )
    parser.add_argument("-r", "--autorun", help="enable autorun", action="store_true")

    # Parse the arguments
    args = parser.parse_args()

    pipe_path = "/home/pi/PSWS/Sstat/datamon.fifo"
    log_path = "/home/pi/G2DATA/Slogs/"
    log_file = "console.log"
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    log = open(os.path.join(log_path, log_file), "a")

    curses.wrapper(main)

    log.close()

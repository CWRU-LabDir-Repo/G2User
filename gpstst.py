import os
import time
import psutil
import curses
import threading
from datetime import datetime
from serial import Serial
from pynmeagps import NMEAReader, NMEAMessage
from gpsdclient import GPSDClient


gps_data = {
    "time": "00:00:00",
    "day": "00",
    "month": "00",
    "year": "0000",
    "lat": 0.0,
    "lon": 0.0,
    "elev": 0.0,
    "pdop": 0.0,
    "fix": "",
    "nsats": 0,
}
exited = False


def is_process_running(process_name):
    for process in psutil.process_iter(["pid", "name"]):
        if process.info["name"] == process_name:
            return True
    return False


def saddstr(stdscr, y, x, string):
    max_y, max_x = stdscr.getmaxyx()
    if 0 <= y < max_y and 0 <= x < max_x:
        stdscr.addstr(y, x, string)


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
                if parsed_data is None:
                    continue

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
    else:
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


def print_title(stdscr):
    saddstr(stdscr, 0, 19, "Grape2 GPS Diagnostic v1.1")
    nextrow = 1
    return nextrow

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


def update_ui(stdscr):
    global exited
    end_of_title = print_title(stdscr)
    end_of_datetime = print_datetime_widget(stdscr, end_of_title)
    end_of_gps = print_gps_widget(stdscr, end_of_datetime)

    gps_reader_thread = threading.Thread(target=gps_reader)
    gps_reader_thread.start()
    try:
        while gps_reader_thread.is_alive():
            print_gps_time(stdscr, end_of_title)
            print_gps(stdscr, end_of_datetime)
            stdscr.refresh()
            time.sleep(0.1)
    except KeyboardInterrupt:
        saddstr(
            stdscr,
            end_of_gps + 1,
            0,
            "Terminating the Diagnostic Tool...                   ",
        )
        stdscr.refresh()
    finally:
        exited = True
    gps_reader_thread.join()


def main(stdscr):
    curses.curs_set(0)  # hide cursor
    curses.init_pair(
        1, curses.COLOR_GREEN, curses.COLOR_BLACK
    )  # (color pair #, foreground, background)
    stdscr.attron(curses.color_pair(1))  # Set default color pair
    update_ui(stdscr)


if __name__ == "__main__":
    log_path = "/home/pi/G2DATA/Slogs/"
    log_file = "gpstst.log"
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    log = open(os.path.join(log_path, log_file), "a")

    curses.wrapper(main)

    log.close()

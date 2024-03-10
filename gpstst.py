import os
import time
import psutil
import curses
import threading
from datetime import datetime
from serial import Serial
from pynmeagps import NMEAReader
from gpsdclient import GPSDClient


gps_data = {"lat": 0.0, "lon": 0.0, "elev": 0.0, "pdop": 0.0, "fix": "", "numSVs": 0}
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


def gps_reader():
    global gps_data, exited, log
    if not is_process_running("gpsd"):
        port = "/dev/ttyS0"
        baud_rate = 115200

        with Serial(port, baud_rate, timeout=None) as stream:
            nmr = NMEAReader(stream, quitonerror=0)
            while not exited:
                try:
                    _, parsed_data = nmr.read()
                    if parsed_data.msgID == "GSA":
                        gps_data["pdop"] = parsed_data.PDOP
                        if parsed_data.navMode == 1:
                            gps_data["fix"] = "0"
                        else:
                            gps_data["fix"] = str(parsed_data.navMode) + "D"
                    elif parsed_data.msgID == "GGA":
                        gps_data["lat"] = parsed_data.lat
                        gps_data["lon"] = parsed_data.lon
                        gps_data["elev"] = parsed_data.alt
                    elif parsed_data.msgID == "GSV":
                        gps_data["numSVs"] = parsed_data.numSV
                    time.sleep(0.05)
                except Exception as e:
                    log.write("\n")
                    log.write(datetime.now().strftime("%m/%d/%Y %H:%M:%S"))
                    log.write(" -> ")
                    log.write(str(e))
                    log.flush()
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
                gps_data["numSVs"] = sky_str.get("uSat", 0)


def print_title(stdscr):
    saddstr(stdscr, 0, 19, "Grape2 GPS Diagnostic v0.0")
    nextrow = 1
    return nextrow

def print_datetime_widget(stdscr, row):
    saddstr(stdscr, row + 1, 0, "GPS Date/Time")
    return row + 2


def print_gps_time(stdscr, row):
    sys_datetime = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    saddstr(stdscr, row + 1, 22, sys_datetime)
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
    saddstr(stdscr, row + 2, 28, str(gps_data["numSVs"]).ljust(2))
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

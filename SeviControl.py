#!/usr/bin/python3

import json
import logging.handlers
import sys
import socket
import yaml
from queue import Queue
from time import sleep, strftime, localtime

from flask import Flask, request
from flask_cors import CORS

from commands import Commands
from connectorRS485 import ConnectorRS485
from connectorThread import ConnectorThread
from controlThread import ControlThread
from sleepThread import SleepThread
from cronCommands import CronCommands
from panelStatus import PanelStatus
from inMemoryLogHandler import InMemoryLogHandler
from modes import Modes

inMemoryHandler = InMemoryLogHandler(logging.INFO)
inMemoryHandler.setFormatter(logging.Formatter('%(levelname)s @ %(asctime)s-:-%(name)s: %(message)s'))
rotatingFileHandler = logging.handlers.RotatingFileHandler("seviControl.log", maxBytes=1024*1024*10, backupCount=5)
rotatingFileHandler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
rotatingFileHandler.setLevel(logging.DEBUG)

logger = logging.getLogger("")
logger.addHandler(inMemoryHandler)
logger.addHandler(rotatingFileHandler)

cfg = ...
with open('config.yaml') as yamlfile:
    cfg = yaml.load(yamlfile)

logic_board_in = Queue()
logic_board_out = Queue()
cmd_queue = Queue()
panel_in = Queue()
panel_out = Queue()
raw_bypass_queue = Queue()

logic_board_cnx = ConnectorRS485(device=cfg['controller']['device'], baudrate=cfg['controller']['baudrate'])
panel_cnx = ConnectorRS485(device=cfg['panel']['device'], baudrate=cfg['panel']['baudrate'])

# TODO: logic_bord_in is ignored... we should listen to any msgs that could appear
logic_board_thread = ConnectorThread(logic_board_cnx, logic_board_in, logic_board_out)
logic_board_thread.start()

panel_thread = ConnectorThread(panel_cnx, panel_in, panel_out)
panel_thread.start()

ctl_thread = ControlThread(logic_board_out, raw_bypass_queue, cmd_queue)
ctl_thread.start()

panel_status_thread = PanelStatus(panel_in, cmd_queue, raw_bypass_queue)
panel_status_thread.start()

cron_thread = CronCommands(cmd_queue)
cron_thread.start()

sleep_thread = SleepThread(cmd_queue)
sleep_thread.start()


def put_out_queue(msg_list):
    for msg in msg_list:
        logic_board_out.put(msg)


def console_mode():
    while 1:
        sleep(0.5)
        print("Modes: on, off, w1, w2, w3, w4, s1, s2, s3, s4, r, q")
        mode = input("Select mode: ")
        if mode == "on":
            put_out_queue(Commands.ON)
        elif mode == "off":
            put_out_queue(Commands.OFF)
        elif mode == "w1":
            cmd_queue.put(Modes.W1)
        elif mode == "w2":
            cmd_queue.put(Modes.W2)
        elif mode == "w3":
            cmd_queue.put(Modes.W3)
        elif mode == "w4":
            cmd_queue.put(Modes.W4)
        elif mode == "s1":
            cmd_queue.put(Modes.S1)
        elif mode == "s2":
            cmd_queue.put(Modes.S2)
        elif mode == "s3":
            cmd_queue.put(Modes.S3)
        elif mode == "s4":
            cmd_queue.put(Modes.S4)
        elif mode == "r":
            if not logic_board_in.empty():
                print(logic_board_in.get())
        elif mode == "q":
            import sys
            sys.exit()
        else:
            print("Unsupported mode...")


if len(sys.argv) > 1:
    if sys.argv[1] == "-a":
        put_out_queue(Commands.ON)
        cmd_queue.put(Modes.W1)
        while 1:
            sleep(0.5)
    elif sys.argv[1] == "-c":
        console_mode()

app = Flask("SeviControl")
app.logger.setLevel(logging.DEBUG)
CORS(app)


def get_hostname_by_addr(ip):
    hostname = socket.gethostbyaddr(ip)[0]
    if "." in hostname:
        hostname = hostname.split('.')[0]
    return hostname


@app.route("/setLevel")
def set_level():
    for key in request.args.keys():
        if key not in ["1", "2", "3", "4"]:
            return "Invalid parameter: "+key, 400
        else:
            mode_name = ctl_thread.current_mode.name
            if mode_name[1].isdigit():
                app.logger.info("Set level '%s' from '%s' (IP: %s)",
                                mode_name[:1]+key,
                                get_hostname_by_addr(request.environ['HTTP_X_FORWARDED_FOR']),
                                request.environ['HTTP_X_FORWARDED_FOR'])
                cmd_queue.put(Modes[mode_name[:1]+key])
                sleep_thread.reset()
    return "Ok", 200


@app.route("/setMode")
def set_mode():
    for key in request.args.keys():
        if key not in ['W', 'S']:
            return "Invalid parameter: "+key, 400
        else:
            mode_name = ctl_thread.current_mode.name
            if mode_name[0] in ['W', 'S']:
                app.logger.info("Set mode '%s' from '%s' (IP: %s)",
                                key+mode_name[1:],
                                get_hostname_by_addr(request.environ['HTTP_X_FORWARDED_FOR']),
                                request.environ['HTTP_X_FORWARDED_FOR'])
                cmd_queue.put(Modes[key+mode_name[1:]])
                sleep_thread.reset()
    return "Ok", 200


@app.route("/set")
def set_all():
    for key in request.args.keys():
        if key not in [name for name, member in Modes.__members__.items()]:
            return "Invalid parameter: "+key, 400
        else:
            app.logger.info("Set all '%s' from '%s' (IP: %s)",
                            key,
                            get_hostname_by_addr(request.environ['HTTP_X_FORWARDED_FOR']),
                            request.environ['HTTP_X_FORWARDED_FOR'])
            cmd_queue.put(Modes[key])
            sleep_thread.reset()
    return "Ok", 200


@app.route("/cronData")
def get_cron_data():
    cron_data = cron_thread.get_cron_data()
    for entry in cron_data:
        entry['days'] = ', '.join(entry['days'])
    return app.response_class(
        response=json.dumps(cron_data, indent=2),
        status=200,
        mimetype='application/json'
    )

@app.route("/delCronData")
def del_cron_data():
    for key in request.args.keys():
        if key not in ["ids"]:
            return "Invalid parameter: "+key, 400
        else:
            app.logger.info("Delete cron rule; ID '%s' from '%s' (IP: %s) ",
                            request.args[key],
                            get_hostname_by_addr(request.environ['HTTP_X_FORWARDED_FOR']),
                            request.environ['HTTP_X_FORWARDED_FOR'])
            cron_thread.del_cron_data(request.args[key].split(','))
    return "Ok", 200



@app.route("/logs")
def get_logs():
    logs = inMemoryHandler.get_logs()[::-1]
    slogs = [e.split('-:-') for e in logs]
    return app.response_class(
        response=json.dumps(slogs, indent=2),
        status=200,
        mimetype='application/json'
    )


@app.route("/status")
def status():
    resp = {"power": "Off", "mode": "-", "level": "-"}
    mode = ctl_thread.current_mode
    mode_name = mode.name
    if mode != Modes["OFF"]:
        if mode_name.startswith("W"):
            resp["power"] = "On"
            resp["mode"] = "Switching"
        elif mode_name.startswith("S"):
            resp["power"] = "On"
            resp["mode"] = "Rushing"

        if mode_name.endswith("1"):
            resp["level"] = "1"
        elif mode_name.endswith("2"):
            resp["level"] = "2"
        elif mode_name.endswith("3"):
            resp["level"] = "3"
        elif mode_name.endswith("4"):
            resp["level"] = "4"

    return app.response_class(
        response=json.dumps(resp, indent=2),
        status=200,
        mimetype='application/json'
    )

@app.route("/panelStatus")
def panel_status():
    resp = "not recognized yet"
    mode = panel_status_thread.last_detected_mode
    if mode:
        if mode.name.startswith("W"):
            resp = "Switching "
            resp += mode.name[-1]
        elif mode.name.startswith("S"):
            resp = "Rushing "
            resp += mode.name[-1]
        else:
            resp = mode.name

    return app.response_class(
        response=json.dumps(resp, indent=2),
        status=200,
        mimetype='application/json'
    )

@app.route("/getSleep")
def get_sleep():
    resp = "-"
    wakeup_time = sleep_thread.wakeup_time
    if wakeup_time:
        resp = strftime("%H:%M", localtime(wakeup_time))
    return app.response_class(
        response=json.dumps(resp, indent=2),
        status=200,
        mimetype='application/json'
    )

@app.route("/setSleep")
def set_sleep():
    for key in request.args.keys():
        if key not in ["duration"]:
            return "Invalid parameter: "+key, 400
        else:
            app.logger.info("Request for %ih sleep from '%s' (IP: %s) ",
                            int(request.args[key])/60/60,
                            get_hostname_by_addr(request.environ['HTTP_X_FORWARDED_FOR']),
                            request.environ['HTTP_X_FORWARDED_FOR'])
            sleep_thread.sleep(int(request.args[key]))
    return "Ok", 200



if __name__ == '__main__':
    app.run(host="0.0.0.0")

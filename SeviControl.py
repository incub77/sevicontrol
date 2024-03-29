#!/usr/bin/python3

import json
import logging.handlers
import socket
from queue import Queue
from time import strftime, localtime

import yaml
from flask import Flask, request
from flask_cors import CORS

from connectorFactory import ConnectorFactory
from connectorThread import ConnectorThread
from controlThread import ControlThread
from cronCommands import CronCommands
from fanout import Fanout
from inMemoryLogHandler import InMemoryLogHandler
from linker import Linker
from modes import Modes
from mqtt import Mqtt
from panelStatus import PanelStatus
from sleepThread import SleepThread

# open configuration file
cfg = ...
with open('config.yaml') as yamlfile:
    cfg = yaml.load(yamlfile, yaml.Loader)

# setup logging
inMemoryHandler = InMemoryLogHandler(logging.INFO)
inMemoryHandler.setFormatter(logging.Formatter('%(levelname)s @ %(asctime)s-:-%(name)s: %(message)s'))
rotatingFileHandler = logging.handlers.RotatingFileHandler("seviControl.log", maxBytes=1024*1024*10, backupCount=5)
rotatingFileHandler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
rotatingFileHandler.setLevel(logging.DEBUG)

logger = logging.getLogger("")
logger.addHandler(inMemoryHandler)
logger.addHandler(rotatingFileHandler)

# create queues for thread communication
logic_board_in = Queue()
logic_board_out = Queue()
cmd_queue = Queue()
panel_in = Queue()
panel_out = Queue()
raw_bypass_queue = Queue()
cmd_to_control_queue = Queue()
cmd_to_linker_queue = ...
cmd_to_mqtt_queue = ...

fanout_queues_list = [cmd_to_control_queue]
if 'link' in cfg and cfg['link']['url']:
    cmd_to_linker_queue = Queue()
    fanout_queues_list.append(cmd_to_linker_queue)

if 'mqtt' in cfg and cfg['mqtt']['url']:
    cmd_to_mqtt_queue = Queue()
    fanout_queues_list.append(cmd_to_mqtt_queue)

# wire threads and queues
# TODO: logic_bord_in is ignored... we should listen to any msgs that could appear
logic_board_thread = ConnectorThread(
    ConnectorFactory(device=cfg['controller']['device'], baudrate=cfg['controller']['baudrate']),
    logic_board_in,
    logic_board_out)
logic_board_thread.start()

panel_thread = ConnectorThread(
    ConnectorFactory(device=cfg['panel']['device'], baudrate=cfg['panel']['baudrate']),
    panel_in,
    panel_out)
panel_thread.start()

fanout_thread = Fanout(cmd_queue, fanout_queues_list)
fanout_thread.start()

ctl_thread = ControlThread(logic_board_out, raw_bypass_queue, cmd_to_control_queue)
ctl_thread.start()

if 'link' in cfg and cfg['link']['url']:
    linker_thread = Linker(cfg['link']['url'], cmd_to_linker_queue)
    linker_thread.start()

if 'mqtt' in cfg and cfg['mqtt']['url']:
    mqtt_thread = Mqtt(cfg['mqtt']['url'],
                       cfg['mqtt']['port'],
                       cfg['mqtt']['use_ssl'],
                       cfg['mqtt']['validate_cert'],
                       cfg['mqtt']['user'],
                       cfg['mqtt']['passwd'],
                       cmd_to_mqtt_queue,
                       cmd_queue)
    mqtt_thread.start()

panel_status_thread = PanelStatus(panel_in, cmd_queue, raw_bypass_queue)
panel_status_thread.start()

cron_thread = CronCommands(cmd_queue)
cron_thread.start()

sleep_thread = SleepThread(cmd_queue)
sleep_thread.start()

# webservice / flask
app = Flask("SeviControl")
app.logger.setLevel(logging.DEBUG)
CORS(app)


def get_hostname_by_addr(ip):
    try:
        hostname = socket.gethostbyaddr(ip)[0]
    except (socket.herror, socket.gaierror):
        hostname = "unknown"
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
    if mode != Modes["OFF"]:
        resp["power"] = "On"
        if mode.name.startswith("W"):
            resp["mode"] = "Switching"
        elif mode.name.startswith("S"):
            resp["mode"] = "Rushing"
        resp['level'] = mode.name[-1]

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


@app.route("/linkMode")
def link_mode_availalbe():
    resp = {"available": "false", "active": "false"}
    if "link" in cfg and cfg['link']['url']:
        resp['available'] = "true"
        if linker_thread.act:
            resp['active'] = "true"
    return app.response_class(
        response=json.dumps(resp, indent=2),
        status=200,
        mimetype='application/json'
    )


@app.route("/activateLink")
def link_active():
    for key in request.args.keys():
        if key not in ['true', 'false']:
            return "Invalid parameter: "+key, 400
        else:
            app.logger.info("Set Link to '%s' from '%s' (IP: %s) ",
                            'active' if key == 'true' else 'inactive',
                            get_hostname_by_addr(request.environ['HTTP_X_FORWARDED_FOR']),
                            request.environ['HTTP_X_FORWARDED_FOR'])
            linker_thread.active(True if key == 'true' else False)
    return "Ok", 200


if __name__ == '__main__':
    app.run(host="0.0.0.0")

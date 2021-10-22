from threading import Thread
from time import sleep
from queue import Empty
import logging
import paho.mqtt.client as mqtt_client
import json
from version import VERSION
from modes import Modes

STATE_TOPIC = 'sevicontrol/on/state'
COMMAND_TOPIC = 'sevicontrol/on/set'
OSCILLATION_STATE_TOPIC = 'sevicontrol/oscillation/state'
OSCILLATION_COMMAND_TOPIC = 'sevicontrol/oscillation/set'
PERCENTAGE_STATE_TOPIC = 'sevicontrol/speed/state'
PERCENTAGE_COMMAND_TOPIC = 'sevicontrol/speed/set'


DISCOVER_MSG = {"platform": "mqtt",
                "name": "Sevicontrol",
                "state_topic": STATE_TOPIC,
                "command_topic": COMMAND_TOPIC,
                "oscillation_state_topic": OSCILLATION_STATE_TOPIC,
                "oscillation_command_topic": OSCILLATION_COMMAND_TOPIC,
                "percentage_state_topic": PERCENTAGE_STATE_TOPIC,
                "percentage_command_topic": PERCENTAGE_COMMAND_TOPIC,
                "payload_on": "on",
                "payload_off": "off",
                "payload_oscillation_on": "on",
                "payload_oscillation_off": "off",
                "speed_range_min": 1,
                "speed_range_max": 4,
                "unique_id": "sevicontrol",
                "device": {"name": "Sevicontrol",
                           "model": "Sevicontrol ventilation system",
                           "manufacturer": "incub",
                           "identifiers": "sevicontrol",
                           "sw_version": str(VERSION)
                           }
                }

# noinspection PyUnusedLocal
class Mqtt(Thread):
    def __init__(self, url, port, use_ssl, validate_cert, user, passwd, in_queue, out_queue):
        super().__init__(daemon=True)
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.url = url
        self.port = port
        self.current_mode = Modes['OFF']
        self.log = logging.getLogger("MQTT-" + url)
        self.log.setLevel(logging.DEBUG)
        self.mqtt_client = mqtt_client.Client(client_id="Sevicontrol", clean_session=True)
        self.mqtt_client.username_pw_set(user, passwd)
        if use_ssl:
            self.mqtt_client.tls_set()
        if use_ssl and not validate_cert:
            self.mqtt_client.tls_insecure_set(True)
        self.mqtt_client.enable_logger()

    def __del__(self):
        self.mqtt_client.disconnect()

    def on_connect(self, client, userdate, flags, rc):
        self.log.debug("Subscribing topics.")
        self.mqtt_client.subscribe([(COMMAND_TOPIC, 0), (PERCENTAGE_COMMAND_TOPIC, 0), (OSCILLATION_COMMAND_TOPIC, 0)])
        self.mqtt_client.message_callback_add(COMMAND_TOPIC, self.on_state_change)
        self.mqtt_client.message_callback_add(PERCENTAGE_COMMAND_TOPIC, self.on_speed_change)
        self.mqtt_client.message_callback_add(OSCILLATION_COMMAND_TOPIC, self.on_oscillation_change)
        self.mqtt_client.publish('homeassistant/fan/sevicontrol/config', json.dumps(DISCOVER_MSG), retain=True)

    def publish_state(self, state):
        if state in ['on', 'off']:
            self.mqtt_client.publish(STATE_TOPIC, state, retain=True)
        else:
            self.log.error("Invalid state.")

    def on_state_change(self, client, userdata, message):
        payload = message.payload.decode('utf-8')
        if payload == 'on' and self.current_mode.name != 'OFF':
            return
        self.log.info("State change to: " + payload)
        if payload == 'on':
            self.out_queue.put(Modes['ON'])
        elif payload == 'off':
            self.out_queue.put(Modes['OFF'])

    def publish_speed(self, speed):
        if speed in ['1', '2', '3', "4"]:
            self.mqtt_client.publish(PERCENTAGE_STATE_TOPIC, speed, retain=True)
        else:
            self.log.error("Invalid speed.")

    def on_speed_change(self, client, userdata, message):
        speed = message.payload.decode('utf-8')
        oscillation = ...
        if self.current_mode.name.startswith("W") or self.current_mode.name.startswith("S"):
            oscillation = self.current_mode.name[0]
        else:
            oscillation = 'W'

        if speed not in ['1', '2', '3', '4']:
            self.log.error("Unknown speed: '%s'" % speed)
            return

        new_mode = oscillation + speed

        self.log.info("Setting new mode: %s" % new_mode)
        self.out_queue.put(Modes[new_mode])

    def publish_oscillation(self, oscillation):
        if oscillation in ['on', 'off']:
            self.mqtt_client.publish(OSCILLATION_STATE_TOPIC, oscillation, retain=True)
        else:
            self.log.error("Invalid oscillation.")

    def on_oscillation_change(self, client, userdate, message):
        oscillation = message.payload.decode('utf-8')
        if self.current_mode.name.startswith("W") or self.current_mode.name.startswith("S"):
            speed = self.current_mode.name[1]
        else:
            speed = '1'

        new_mode = ...
        if oscillation == 'on':
            new_mode = 'W' + speed
        elif oscillation == 'off':
            new_mode = 'S' + speed
        else:
            self.log.error("Unknow oscillation: '%s'" % oscillation)

        self.log.info("Setting new mode: %s" % new_mode)
        self.out_queue.put(Modes[new_mode])

    @staticmethod
    def translate_mode_to_hassio(mode):
        state = 'on'
        speed = 'low'
        oscillation = 'on'

        if mode == Modes['OFF']:
            state = 'off'
        elif mode == Modes['ON']:
            state = 'on'
        else:
            if mode.name.startswith('S'):
                oscillation = 'off'
            speed = mode.name[-1]

        return state, speed, oscillation

    def publish_mode(self, mode):
        hassio_mode = self.translate_mode_to_hassio(mode)
        self.publish_state(hassio_mode[0])
        self.publish_speed(hassio_mode[1])
        self.publish_oscillation(hassio_mode[2])

    def run(self):
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.connect(self.url, self.port)
        self.mqtt_client.loop_start()
        self.publish_mode(self.current_mode)

        while True:
            sleep(0.25)
            try:
                mode = self.in_queue.get(block=False)
                self.publish_mode(mode)
                self.current_mode = mode
            except Empty:
                pass

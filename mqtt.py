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
SPEED_STATE_TOPIC = 'sevicontrol/speed/state'
SPEED_COMMAND_TOPIC = 'sevicontrol/speed/set'

DISCOVER_MSG = {"platform": "mqtt",
                "name": "Sevicontrol",
                "state_topic": STATE_TOPIC,
                "command_topic": COMMAND_TOPIC,
                "oscillation_state_topic": OSCILLATION_STATE_TOPIC,
                "oscillation_command_topic": OSCILLATION_COMMAND_TOPIC,
                "speed_state_topic": SPEED_STATE_TOPIC,
                "speed_command_topic": SPEED_COMMAND_TOPIC,
                "payload_on": "on",
                "payload_off": "off",
                "payload_oscillation_on": "on",
                "payload_oscillation_off": "off",
                "payload_low_speed": "low",
                "payload_medium_speed": "medium",
                "payload_high_speed": "high",
                "speeds": ["low", "medium", "high"],
                "unique_id": "sevicontrol",
                "device": {"name": "Sevicontrol",
                          "model": "Sevicontrol ventilation system",
                          "manufacturer": "incub",
                          "identifiers": "sevicontrol",
                          "sw_version": str(VERSION)
                           }
                }


class Mqtt(Thread):
    def __init__(self, url, port, user, passwd, in_queue, out_queue):
        super().__init__(daemon=True)
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.current_mode = Modes['OFF']
        self.log = logging.getLogger("Mqtt-"+url)
        self.mqtt_client = mqtt_client.Client(client_id="Sevicontrol", clean_session=True)
        self.mqtt_client.username_pw_set(user, passwd)
        self.mqtt_client.connect(url, port)


    def set_state(self, state):
        if state in ['on', 'off']:
            self.mqtt_client.publish(STATE_TOPIC, state, retain=True)
        else:
            self.log.error("Invalid state.")

    def on_state_change(self, client, userdate, message):
        if message.payload == 'on':
            self.out_queue.put(Modes['ON'])
        elif message.payload == 'off':
            self.out_queue.put(Modes['OFF'])

    def set_speed(self, speed):
        if speed in ['low', 'medium', 'high']:
            self.mqtt_client.publish(SPEED_STATE_TOPIC, speed, retain=True)
        else:
            self.log.error("Invalid speed.")

    def on_speed_change(self, client, userdata, message):
        pass

    def set_oscillation(self, oscillation):
        if oscillation in ['on', 'off']:
            self.mqtt_client.publish(OSCILLATION_STATE_TOPIC, oscillation, retain=True)
        else:
            self.log.error("Invalid oscillation.")

    def on_oscillation_change(self, client, userdate, message):
        pass

    def translate_mode_to_hassio(self, mode):
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
            if mode.name.endswith('2'):
                speed = 'medium'
            elif mode.name.endswith('3'):
                speed = 'medium'
            elif mode.name.endswith('4'):
                speed = 'high'

        return (state, speed, oscillation)



    def run(self):
        self.mqtt_client.publish('homeassistant/fan/sevicontrol/config', json.dumps(DISCOVER_MSG), retain=True)
        self.mqtt_client.subscribe(COMMAND_TOPIC)
        self.mqtt_client.subscribe(SPEED_COMMAND_TOPIC)
        self.mqtt_client.subscribe(OSCILLATION_COMMAND_TOPIC)
        self.mqtt_client.message_callback_add(COMMAND_TOPIC, self.on_state_change)
        self.mqtt_client.message_callback_add(SPEED_COMMAND_TOPIC, self.on_speed_change)
        self.mqtt_client.message_callback_add(OSCILLATION_COMMAND_TOPIC, self.on_oscillation_change)
        self.mqtt_client.loop_start()

        while True:
            sleep(0.5)
            try:
                mode = self.in_queue.get(block=False)
                self.current_mode = mode
                hassio_mode = self.translate_mode_to_hassio(mode)
                self.set_state(hassio_mode[0])
                self.set_speed(hassio_mode[1])
                self.set_oscillation(hassio_mode[2])
            except Empty:
                pass
from threading import Thread
from time import sleep, time
from commands import Commands
from modes import Modes
from queue import Empty, Full
import logging


class ControlThread(Thread):
    def __init__(self, logic_board_queue, raw_cmd_queue, cmd_queue):
        super().__init__(daemon=True)
        self.logic_board_queue = logic_board_queue
        self.raw_cmd_queue = raw_cmd_queue
        self.cmd_queue = cmd_queue
        self.current_mode = Modes["OFF"]
        self.current_direction = None
        self.last_direction_change = None
        self.direction_change_interval = 75
        self.log = logging.getLogger("Controller")
        self.log.setLevel(logging.DEBUG)

    def put_logic_board_queue(self, msg_list):
        for msg in msg_list:
            try:
                self.logic_board_queue.put(msg, block=False)
            except Full:
                self.log.critical("Logic board queue full")

    def set_new_mode(self, new_mode):
        self.current_mode = new_mode

        if self.current_direction is None:
            self.current_direction = True
            self.last_direction_change = time()
        if new_mode == Modes["ON"]:
            self.put_logic_board_queue(Commands.BY_MODE[new_mode])
            self.direction_change_interval = 75
            self.current_mode = Modes['W1']
        elif new_mode == Modes["OFF"]:
            self.put_logic_board_queue(Commands.BY_MODE[new_mode])
            self.current_direction = None
        # else means we have S or W mode
        else:
            self.direction_change_interval = 75
            self.put_logic_board_queue(Commands.BY_MODE[new_mode]["FWD" if self.current_direction else "REV"])

    def direction_change(self):
        self.last_direction_change = time()
        self.current_direction = not self.current_direction
        self.set_new_mode(self.current_mode)

    def run(self):
        while True:
            sleep(0.05)
            # check for raw msgs from control panel
            # these are filtered by panel_status thread and are just passed through
            try:
                cmd = self.raw_cmd_queue.get(block=False)
                self.logic_board_queue.put(cmd, block=False)
            except Full:
                self.log.critical("Logic board queue full")
            except Empty:
                pass

            # check msgs in cmd_queue
            # these cmds come from rest-api or console input and are already mapped
            try:
                cmd = self.cmd_queue.get(block=False)
                if cmd != self.current_mode:
                    self.log.info("Setting new mode: '%s'", cmd.name)
                    self.set_new_mode(cmd)
            except Empty:
                pass

            # check if we have to switch fan direction (W-modes) or renew command (S-modes)
            if self.current_mode and \
                    (self.current_mode.name.startswith("W") or self.current_mode.name.startswith("S")) and \
                    self.last_direction_change and \
                    (time() - self.last_direction_change) > self.direction_change_interval:
                self.log.debug("Issuing direction change/renew for mode: %s", self.current_mode.name)
                self.direction_change()

import logging
from threading import Thread
from time import sleep
from queue import Empty, Full
from commands import Commands
from modes import Modes


class FlowEx(Exception):
    pass


class PanelStatus(Thread):
    def __init__(self, panel_queue, cmd_queue, raw_bypass_queue):
        super().__init__(daemon=True)
        self.panel_queue = panel_queue
        self.cmd_queue = cmd_queue
        self.raw_bypass_queue = raw_bypass_queue
        self.cmds = []
        self.max_cmds = 20
        self.last_detected_mode = None
        self.log = logging.getLogger("PanelStatus")
        self.log.setLevel(logging.INFO)

    def add_cmd(self, cmd):
        if len(self.cmds) >= self.max_cmds:
            del(self.cmds[0])
        self.cmds.append(cmd)

    def recognize_mode(self):
        # The cmds consists of 4 msgs max, compare 4 messages in our fifo list from back to forth
        # All other commands can be recognized within this 4 messages
        for i in range(0, self.max_cmds-3):
            msg_set = set(self.cmds[-4-i:None if i == 0 else i*-1])
            for mode in Modes:
                if mode == Modes.ON or mode == Modes.OFF:
                    if set(Commands.BY_MODE[mode]) <= msg_set:
                        return mode
                else:
                    for direction in ["FWD", "REV"]:
                        if set(Commands.BY_MODE[mode][direction]) <= msg_set:
                            return mode

    def run(self):
        known_cmds = Commands.generate_set_of_all_cmds()
        while 1:
            sleep(0.1)
            try:
                cmd = self.panel_queue.get(block=False)
                # bypass these "i don't know what they do, but the don't interfere with fan control" cmds
                # panel is probably requesting sensors with these cmds
                if cmd in Commands.RECURRING:
                    self.raw_bypass_queue.put(cmd, block=False)
                    # TODO: Exception for flow control... get rid of it
                    raise FlowEx
                elif cmd not in known_cmds:
                    self.log.warning("Unknown cmd detected: '%s'", cmd)
                else:
                    self.log.debug("Added cmd '%s' to recognition", cmd)
                    self.add_cmd(cmd)
            except Empty:
                pass
            except Full:
                self.log.critical("Raw bypass queue is full. Panel recognition is unstable.")
            except FlowEx:
                pass
            else:
                mode = self.recognize_mode()
                if mode is None:
                    continue
                # have we found an panel mode before?
                if self.last_detected_mode is None:
                    self.last_detected_mode = mode
                    self.log.info("Initial panel mode recognized as: '%s' (is ignored)", mode.name)
                # if the mode hasn't change, we can ignore it
                elif mode == self.last_detected_mode:
                    pass
                # there must have been an user input via the control panel
                else:
                    self.log.info("New mode '%s' on control panel detected", mode.name)
                    self.last_detected_mode = mode
                    try:
                        self.cmd_queue.put(mode, block=False)
                    except Full:
                        self.log.critical("Command queue is full")

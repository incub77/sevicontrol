import time
from threading import Thread, Lock
from queue import Full
from modes import Modes
import logging



class PauseThread(Thread):
    def __init__(self, cmd_queue):
        super().__init__(daemon=True)
        self.cmd_queue = cmd_queue
        self.lock = Lock()
        self.wakeup_time = None
        self.log = logging.getLogger("Pause")
        self.log.setLevel(logging.DEBUG)

    def pause(self, duration):
        self.log.info("Going to sleep till %s" % time.strftime("%H:%M", time.localtime(time.time() + duration)))
        with self.lock:
            self.wakeup_time = time.time() + duration
        try:
            self.cmd_queue.put(Modes.OFF)
        except Full:
            self.log.critical("Command queue full")

    def run(self) -> None:
        while 1:
            time.sleep(60)
            if self.wakeup_time and time.time() >= self.wakeup_time:
                self.log.info("Waking up from sleep mode")
                with self.lock:
                    self.wakeup_time = None
                try:
                    self.cmd_queue.put(Modes.ON)
                except Full:
                    self.log.critical("Command queue full")


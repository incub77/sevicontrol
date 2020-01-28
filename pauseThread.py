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

    def sleep(self, duration):
        with self.lock:
            self.log.info("Going to sleep till %s" % time.strftime("%H:%m", time.localtime(time.time() + duration)))
            self.wakeup_time = time.time() + duration
            #TODO: try
            self.cmd_queue.put(Modes.OFF)

    def run(self) -> None:
        while 1:
            time.sleep(60)
            if time.time() >= self.wakeup_time:
                with self.lock:
                    self.wakeup_time = None
                    try:
                        self.cmd_queue.put(Modes.ON)
                        self.log.info("Waking up from sleep mode")
                    except Full:
                        self.log.critical("Command queue full")


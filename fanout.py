import threading
from time import sleep
from queue import Full, Empty
import logging


class Fanout(threading.Thread):
    def __init__(self, in_qeueu, out_queues):
        super().__init__(daemon=True)
        self.in_queue = in_qeueu
        self.out_queues = out_queues
        self.log = logging.getLogger("Fanout")
        self.log.setLevel(logging.DEBUG)

    def run(self):
        while 1:
            sleep(0.05)
            try:
                msg = self.in_queue.get(block=False)
            except Empty:
                pass
            else:
                for q in self.out_queues:
                    try:
                        q.put(msg, block=False)
                    except Full:
                        self.log.critical("Queue full")

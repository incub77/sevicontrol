from threading import Thread
from time import sleep
from queue import Full, Empty
import logging


class ConnectorThread(Thread):
    def __init__(self, cnx, in_queue, out_queue):
        super().__init__(daemon=True)
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.cnx = cnx
        self.log = logging.getLogger("ConnectorThread"+cnx.port.split('/')[-1])
        self.log.setLevel(logging.DEBUG)

    def run(self):
        send = 0
        while 1:
            # We need to sleep a bit, otherwise SEVI controller doesn't have enough time to process msgs
            # (prevent DOS attack :-)). Send every 4th loop.
            sleep(0.05)
            send += 1
            if self.cnx.inWaiting():
                msg = self.cnx.read_msg()
                if msg:
                    try:
                        self.in_queue.put(msg, block=False)
                    except Full:
                        self.log.critical("Input queue full for %s", self.cnx.port)
            elif send >= 4:
                try:
                    send = 0
                    self.cnx.send_msg(self.out_queue.get(block=False))
                except Empty:
                    pass

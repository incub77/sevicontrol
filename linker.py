from requests import get, HTTPError, ConnectionError, ConnectTimeout
from threading import Thread
from time import sleep
from queue import Empty
import logging


class Linker(Thread):
    def __init__(self, url, in_queue):
        super().__init__(daemon=True)
        self.in_queue = in_queue
        self.url = url
        self.log = logging.getLogger("Linker-"+self.url)

    def run(self):
        while True:
            sleep(0.5)
            try:
                mode = self.in_queue.get(block=False)
                r = get(self.url+'/set?'+mode.name)
                r.raise_for_status()
            except Empty:
                pass
            except (HTTPError, ConnectionError, ConnectTimeout) as e:
                self.log.critical(e, exc_info=True)

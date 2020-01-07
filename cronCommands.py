import time
from threading import Thread, Lock
import json
from copy import deepcopy
from queue import Full
from modes import Modes
import logging

# Example cron entry
# cron_entry = {
#     "id": "1",
#     "status": "active",
#     "days": ["Mon-Fri"],
#     "hour": "08",
#     "minute": "00",
#     'mode': "W4"
# }

DATA_FILE = "cron_data.json"


class CronCommands(Thread):
    def __init__(self, cmd_queue):
        super().__init__(daemon=True)
        self.lock = Lock()
        self.cron_data = []
        self.cmd_queue = cmd_queue
        self.log = logging.getLogger("Chrono")
        self.log.setLevel(logging.DEBUG)

    def load_cron_data(self):
        try:
            with open(DATA_FILE, 'r') as fp:
                with self.lock:
                    self.cron_data = json.load(fp)
        except FileNotFoundError:
            pass

    def _persists_cron_data(self):
        with open(DATA_FILE, 'w') as fp:
            with self.lock:
                json.dump(self.cron_data, fp, indent=2)

    def add_cron_data(self, cron_data):
        with self.lock:
            self.cron_data.append(cron_data)
        self._persists_cron_data()

    def get_cron_data(self):
        with self.lock:
            return deepcopy(self.cron_data)

    def del_cron_data(self, ids_to_delete):
        filtered_cron_data = [e for e in self.cron_data if e["id"] not in ids_to_delete]
        with self.lock:
            self.cron_data = filtered_cron_data
        self._persists_cron_data()

    @staticmethod
    def relevant_days(day):
        rde = ["Sun-Sat"]
        day = int(day)
        # a bit complicated, but time module offers local abbreviations only... our frontend is in english,
        # so to use time module I would have to localize it...
        if day == 0:
            rde.append("Sun")
        elif day == 1:
            rde.append("Mon")
        elif day == 2:
            rde.append("Tue")
        elif day == 3:
            rde.append("Wed")
        elif day == 4:
            rde.append("Thu")
        elif day == 5:
            rde.append("Fri")
        elif day == 6:
            rde.append("Sat")
        # saturday (6) or sunday (0)
        if day == 0 or day == 6:
            rde.append('Sat-Sun')
        # monday (1) to friday (5)
        if 1 <= day <= 5:
            rde.append('Mon-Fri')
        # workingdays + saturday
        if (1 <= day <= 5) or day == 6:
            rde.append('Mon-Sat')
        return rde

    def run(self):
        self.load_cron_data()
        last_now = ""
        while 1:
            time.sleep(30)
            now = time.strftime('%w %H %M').split(' ')
            if now == last_now:
                continue
            else:
                last_now = now
            with self.lock:
                cron_data = deepcopy(self.cron_data)
            for entry in cron_data:
                # set-expression := if two lists contain at least one match
                if entry["status"] == "active" \
                        and set(entry["days"]) & set(self.relevant_days(now[0])) \
                        and entry["hour"] == now[1] \
                        and entry["minute"] == now[2]:
                    try:
                        self.cmd_queue.put(Modes[entry['mode']])
                        self.log.info("Chrono trigger new mode: %s", entry["mode"])
                    except Full:
                        self.log.critical("Command queue full")

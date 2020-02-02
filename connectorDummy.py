import logging

class ConnectorDummy():
    def __init__(self):
        self.log = logging.getLogger("connector-Dummy")
        self.port = "dummy"
        self.log.setLevel(logging.DEBUG)

    def read_msg(self):
        return None

    def send_msg(self, msg):
        self.log.debug("Writing msg: %s" % msg)

    def inWaiting(self):
        return 0
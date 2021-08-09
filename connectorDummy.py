import logging


class ConnectorDummy:
    def __init__(self):
        self.log = logging.getLogger("connector-Dummy")
        self.port = "dummy"
        self.log.setLevel(logging.DEBUG)

    @staticmethod
    def read_msg():
        return None

    def send_msg(self, msg):
        self.log.debug("Writing msg: %s" % msg)

    @staticmethod
    def inWaiting():
        return 0

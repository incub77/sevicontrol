import serial
from binascii import hexlify
from time import sleep
import logging


class ConnectorRS485(serial.Serial):
    def __init__(self, device, baud=1000):
        super().__init__(port=device, baudrate=baud, stopbits=serial.STOPBITS_ONE, parity=serial.PARITY_NONE)
        self.log = logging.getLogger("connector-"+device.split('/')[-1])
        self.log.setLevel(logging.DEBUG)

    @staticmethod
    def verify_checksum(msg):
        chksum = 0
        for i in range(0, len(msg)-1):
            chksum ^= msg[i]

        if chksum == msg[-1]:
            return True
        else:
            return False

    def read_msg(self):
        msg_buffer = ""
        while self.inWaiting() > 0:
            msg_buffer += hexlify(self.read(1)).decode('utf-8')
            # in case we are reading while msg is being sent,
            # we sleep till next byte is ready (we don't know msg length)
            sleep(round((1/self.baudrate) * 12, 8))

        if len(msg_buffer) > 0:
            if self.verify_checksum(bytes.fromhex(msg_buffer)):
                return msg_buffer
            else:
                self.log.error("Checksum error. Device: %s, Msg: %s", self.port, msg_buffer)

    def send_msg(self, msg):
        self.write(bytes.fromhex(msg))

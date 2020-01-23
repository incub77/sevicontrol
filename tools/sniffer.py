#!/usr/bin/python3

import serial
import time
from binascii import hexlify

device = "/dev/ttyUSB0"
#device = "/dev/ttyUSB1"
#device = "/dev/ttyAMA0"
baudrates = [1000]
#baudrates = [2400, 4800, 9600, 115200, 38400, 57600, ]
bytesizes = [(serial.EIGHTBITS, "EIGHT")]
#bytesizes = [(serial.EIGHTBITS, "EIGHT"), (serial.SEVENBITS, "SEVEN"), (serial.SIXBITS, "SIX"), (serial.FIVEBITS, "FIVE")]
parities = [(serial.PARITY_NONE, "NONE")]
#parities = [(serial.PARITY_NONE, "NONE"), (serial.PARITY_EVEN, "EVEN"), (serial.PARITY_ODD, "ODD"),
#            (serial.PARITY_MARK, "MARK"), (serial.PARITY_SPACE, "SPACE")]
stopbits = [(serial.STOPBITS_ONE, "ONE")]
#stopbits = [(serial.STOPBITS_ONE, "ONE"), (serial.STOPBITS_ONE_POINT_FIVE,"ONE_POINT_FIVE"), (serial.STOPBITS_TWO, "TWO")]
xonxoff = [(True, "True"), (False, "False")]
rtscts = [(True, "True"), (False, "False")]
dsrdtr = [(True, "True"), (False, "False")]
startTime = time.time()

class Sniffer:
    #def __init__(self, device, baud, bytesize, parity, stopbits, xonxoff, rtscts, dsrdtr, logSep):
    def __init__(self, device, baud, bytesize, parity, stopbits, logSep):
        self.usart = serial.Serial(port= device,
                                   baudrate= baud,
                                   bytesize= bytesize[0],
                                   parity= parity[0],
                                   stopbits= stopbits[0])
                                   #xonxoff= xonxoff[0],
                                   #rtscts= rtscts[0],
                                   #dsrdtr= dsrdtr[0])
        self.baudrate = baud
        self.usart.flushInput()
        self.out = open("llog_%s_%s_%s.log" % (str(baud), bytesize[1], str(logSep)), "w")
        self.out.write("Baudrate: "+str(baud)+"\r\n")
        self.out.write("Bytesize: "+bytesize[1]+" Parity: "+parity[1]+"\r\n")
        self.out.write("Stopbits: " + stopbits[1] + "\r\n")
       # self.out.write("Stopbits: "+stopbits[1]+" Xonxoff: "+xonxoff[1]+"\n")
       # self.out.write("Rtscts: "+rtscts[1]+" Dsrdtr: "+dsrdtr[1]+"\n")
        self.out.write("============================================================================================\r\n")

    def __del__(self):
        self.out.close()
        self.usart.close()

    @staticmethod
    def verify_checksum(msg):
        chksum = 0
        for i in range(0, len(msg) - 1):
            chksum ^= msg[i]

        return True if chksum == msg[-1] else False

    @staticmethod
    def toLogString(secs, inBuffer, chksum_ok):
        log_str = "%06.3f" % (secs)
        log_str += " : "
        if chksum_ok:
            log_str += "OK : "
        else:
            log_str += "NOK : "
        bin_str = ""
        byte_count = 0
        for byte in inBuffer:
            log_str += byte
            tmp_bin = bin(int(byte, base=16))[2:].zfill(8)
            #bin_str += tmp_bin
            bin_str += "%s %s " % (tmp_bin[:4], tmp_bin[4:])
            byte_count += 1
            if byte_count % 2 == 0:
                log_str += " "
                bin_str += " "

        log_str = log_str.ljust(50)
        log_str += " : "
        log_str += bin_str

        return log_str


    def sniff(self, duration):
        startTime = time.time()
        chksum_nok_cnt = 0
        while int(time.time() - startTime) < duration:
            inBuffer = []
            while self.usart.inWaiting() > 0:
                inBuffer += hexlify(self.usart.read(1)).decode('utf-8')
                time.sleep(round((1 / self.baudrate) * 12, 8))

            if len(inBuffer) > 0:
                chksum_ok = self.verify_checksum(bytes.fromhex(''.join(inBuffer)))
                if not chksum_ok:
                    chksum_nok_cnt += 1
                log_str = self.toLogString(time.time() - startTime, inBuffer, chksum_ok)
                print(log_str)
                self.out.write(log_str + "\r\n")
                if chksum_nok_cnt >= 5:
                    return

for baudrate in baudrates:
    for bytesize in bytesizes:
        print("Start sniffing on " + device + " with baudrate " + str(baudrate)+" and bytesize "+bytesize[1]+" ...")
        logSep = 0
        for parity in parities:
            for stopbit in stopbits:
                print("--> Parity: " + parity[1] + " Stopbits: " + stopbit[1])
#                for xx in xonxoff:
#                    for rts in rtscts:
#                        for dsr in dsrdtr:
                logSep+=1
                sn = Sniffer(device, baud=baudrate,
                                bytesize=bytesize, parity=parity,
                                stopbits=stopbit,
                                logSep=logSep)
                sn.sniff(120)
                sn = None




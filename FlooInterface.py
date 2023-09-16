import time, os, sys, platform
import serial
import serial.tools.list_ports
from FlooParser import FlooParser
from FlooInterfaceDelegate import FlooInterfaceDelegate
from FlooMessage import FlooMessage

class FlooInterface:
    """FlooGoo Bluetooth USB Dongle Control Interface on USB COM port"""

    def __init__(self, delegate):
        super().__init__()
        self.delegate = delegate
        self.isSleep = False
        self.port_name = None
        self.port_opened = False
        self.port = None
        self.parser = FlooParser()

    def setSleep(self, flag):
        self.isSleep = flag

    def reset(self):
        print("FlooInterface: reset")
        if self.port_opened:
            print("FlooInterface: close port")
            self.port.close()
        # self.port_name = None
        self.port_opened = False
        self.port = None
        self.delegate.interfaceState(False, None)

    def monitor_port(self) -> bool:
        if self.isSleep:
            return False

        print([port.hwid for port in serial.tools.list_ports.grep('0A12:4007.*FMA120.*')])
        ports = [port.name for port in serial.tools.list_ports.grep('0A12:4007.*FMA120.*')] # FMA120
        if ports:
            if not self.port_opened:
                self.port_name = ports[0]
                print("monitor_port: try open " + self.port_name)
                try:
                    if platform.system().lower().startswith('win'):
                        self.port = serial.Serial(port=self.port_name, baudrate=921600,
                                                  bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)
                    elif platform.system().lower().startswith('lin'):
                        self.port = serial.Serial(port='/dev/' + self.port_name, baudrate=921600,
                                                  bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)

                    # self.port.open()
                    self.port_opened = self.port.is_open
                    if self.port_opened:
                        self.delegate.interfaceState(True, self.port_name)
                    # print("Change port state: ", self.port_opened)
                    return self.port_opened
                except Exception as exec0:
                    print(exec0)
                    self.reset()
                    return False
        else:
            if self.port_opened:
                print("monitor_port: no port exists")
                self.reset()
        return False

    def run(self):
        while True:
            if self.monitor_port():
                while self.port is not None and self.port.is_open and not self.isSleep:
                    try:
                        if self.port.inWaiting() > 0:
                            print("FlooInterface: got some msgs")
                            newLine = self.port.read_until(b'\r\n')
                            print("FlooInterface: full line " + newLine.decode('utf-8'))
                            flooMsg = self.parser.run(newLine[:-2])
                            if flooMsg is None:
                                break
                            else:
                                self.delegate.handleMessage(flooMsg)
                            time.sleep(0.01)
                    except Exception as exec0:
                        print(exec0)
                        self.portOpenDelay = None
                        self.reset()
            else:
                self.reset()
            print("sleep for 1 second")
            time.sleep(1)  # check port after 1 second

    def sendMsg(self, msg:FlooMessage):
        if self.port is not None and self.port.is_open and not self.isSleep:
            try:
                print("FlooInterface: send " + msg.bytes.decode())
                self.port.write(msg.bytes)
            except Exception as exec0:
                print (exec0)

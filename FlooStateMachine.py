from threading import *
from FlooInterface import FlooInterface
from FlooInterfaceDelegate import FlooInterfaceDelegate
from FlooMessage import FlooMessage
from FlooStateMachineDelegate import FlooStateMachineDelegate
from FlooMsgAd import FlooMsgAd

class FlooStateMachine(FlooInterfaceDelegate, Thread):
    """The state machine of the host app working with FlooGoo USB Bluetooth Dongle"""

    INIT = -1
    IDLE = 0
    BLE_BROADCASTING = 1
    PAIRING = 2
    CONNECTING = 3
    CONNECTED = 4

    def __init__(self, delegate):
        super().__init__()
        self.state = FlooStateMachine.INIT
        self.lastCmd = None
        self.delegate = delegate
        self.inf = FlooInterface(self)

    def reset(self):
        self.state = FlooStateMachine.IDLE
        self.lastCmd = None

    def run(self):
        self.inf.run()

    def interfaceState(self, enabled: bool, port: str):
        if enabled and self.state == FlooStateMachine.INIT:
            cmdReadAddr = FlooMsgAd(True)
            self.inf.sendMsg(cmdReadAddr)

    def handleMessage(self, message: FlooMessage):
        print("FlooStateMachine: handleMessage " + message.header)
        if self.state == FlooStateMachine.INIT:
            if isinstance(message, FlooMsgAd):
                self.delegate.deviceDetected(True, self.inf.port_name)
                self.state = FlooStateMachine.IDLE
                # read current working mode - broadcast or unicast
        elif self.state == FlooStateMachine.IDLE:
            pass

    def enableBroadcast(self, enable: bool):
        print("FlooStateMachine " + "en" if enable else "dis" +  "able broadcast")
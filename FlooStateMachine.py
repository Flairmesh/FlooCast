from threading import *
from FlooInterface import FlooInterface
from FlooInterfaceDelegate import FlooInterfaceDelegate
from FlooMessage import FlooMessage
from FlooStateMachineDelegate import FlooStateMachineDelegate
from FlooMsgAd import FlooMsgAd
from FlooMsgAm import FlooMsgAm
from FlooMsgLa import FlooMsgLa
from FlooMsgSt import FlooMsgSt
from FlooMsgBm import FlooMsgBm
from FlooMsgBn import FlooMsgBn
from FlooMsgOk import FlooMsgOk
from FlooMsgEr import FlooMsgEr

class FlooStateMachine(FlooInterfaceDelegate, Thread):
    """The state machine of the host app working with FlooGoo USB Bluetooth Dongle"""

    INIT = -1
    CONNECTED = 0

    def __init__(self, delegate):
        super().__init__()
        self.state = FlooStateMachine.INIT
        self.lastCmd = None
        self.delegate = delegate
        self.inf = FlooInterface(self)
        self.pendingCmdPara = None

    def reset(self):
        self.state = FlooStateMachine.INIT
        self.lastCmd = None
        self.pendingCmdPara = None

    def run(self):
        self.inf.run()

    def interfaceState(self, enabled: bool, port: str):
        if enabled and self.state == FlooStateMachine.INIT:
            cmdReadAddr = FlooMsgAd(True)
            self.inf.sendMsg(cmdReadAddr)
            self.lastCmd = cmdReadAddr
        elif not enabled:
            print("FlooStateMachine reset bypass")
            self.lastCmd = None
            self.pendingCmdPara = None
            self.state = FlooStateMachine.INIT
            self.delegate.deviceDetected(False, None)

    def handleMessage(self, message: FlooMessage):
        print("FlooStateMachine: handleMessage " + message.header)
        if self.state == FlooStateMachine.INIT:
            if isinstance(message, FlooMsgAd):
                if isinstance(self.lastCmd, FlooMsgAd):
                    self.delegate.deviceDetected(True, self.inf.port_name)
                    cmdGetAudioMode = FlooMsgAm(True)
                    self.inf.sendMsg(cmdGetAudioMode)
                    self.lastCmd = cmdGetAudioMode
            elif isinstance(message, FlooMsgAm):
                if isinstance(self.lastCmd, FlooMsgAm):
                    self.delegate.audioModeInd(message.mode)
                    cmdGetSourceState = FlooMsgSt(True)
                    self.inf.sendMsg(cmdGetSourceState)
                    self.lastCmd = cmdGetSourceState
            elif isinstance(message, FlooMsgSt):
                if isinstance(self.lastCmd, FlooMsgSt):
                    self.delegate.sourceStateInd(message.state)
                    cmdGetLeaState = FlooMsgLa(True)
                    self.inf.sendMsg(cmdGetLeaState)
                    self.lastCmd = cmdGetLeaState
            elif isinstance(message, FlooMsgLa):
                if isinstance(self.lastCmd, FlooMsgLa):
                    self.delegate.leAudioStateInd(message.state)
                    cmdGetBroadcastMode = FlooMsgBm(True)
                    self.inf.sendMsg(cmdGetBroadcastMode)
                    self.lastCmd = cmdGetBroadcastMode
            elif isinstance(message, FlooMsgBm):
                if isinstance(self.lastCmd, FlooMsgBm):
                    self.delegate.broadcastModeInd(message.mode)
                    cmdGetBroadcastName = FlooMsgBn(True)
                    self.inf.sendMsg(cmdGetBroadcastName)
                    self.lastCmd = cmdGetBroadcastName
            elif isinstance(message, FlooMsgBn):
                if isinstance(self.lastCmd, FlooMsgBn):
                    self.delegate.broadcastNameInd(message.name)
                    self.lastCmd = None
                    self.state = FlooStateMachine.CONNECTED
                # read current audio mode
        elif self.state == FlooStateMachine.CONNECTED:
            if isinstance(message, FlooMsgOk):
                if isinstance(self.lastCmd, FlooMsgAm) \
                        or isinstance(self.lastCmd, FlooMsgBm) \
                        or isinstance(self.lastCmd, FlooMsgBn):
                    self.lastCmd = None
            elif isinstance(message, FlooMsgEr):
                if isinstance(self.lastCmd, FlooMsgAm):
                    self.delegate.audioModeInd(self.pendingCmdPara)
                elif isinstance(self.lastCmd, FlooMsgBm):
                    self.delegate.broadcastModeInd(self.pendingCmdPara)
                elif isinstance(self.lastCmd, FlooMsgBn):
                    self.delegate.broadcastNameInd(self.pendingCmdPara)
                self.lastCmd = None
            elif isinstance(message, FlooMsgSt):
                self.delegate.sourceStateInd(message.state)
            elif isinstance(message, FlooMsgLa):
                self.delegate.leAudioStateInd(message.state)

    def setAudioMode(self, mode: int):
        if self.state == FlooStateMachine.CONNECTED:
            cmdSetAudioMode = FlooMsgAm(True, mode)
            self.pendingCmdPara = mode
            self.lastCmd = cmdSetAudioMode
            self.inf.sendMsg(cmdSetAudioMode)

    def setPublicBroadcast(self, enable: bool):
        pass

    def setBroadcastEncrypt(self, enable: bool):
        pass

    def setBroadcastName(self, name:str):
        if self.state == FlooStateMachine.CONNECTED:
            print("setBroadcastName " + name)
            cmdSetBroadcastName = FlooMsgBn(True, name)
            self.pendingCmdPara = name
            self.lastCmd = cmdSetBroadcastName
            self.inf.sendMsg(cmdSetBroadcastName)

    def setBroadcastKey(self, key:str):
        if self.state == FlooStateMachine.CONNECTED:
            print("setBroadcastKey " + key)
            cmdSetBroadcastName = FlooMsgBn(True, name)
            self.pendingCmdPara = key
            self.lastCmd = cmdSetBroadcastName
            self.inf.sendMsg(cmdSetBroadcastName)

    def setNewPairing(self):
        pass

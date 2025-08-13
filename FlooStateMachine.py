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
from FlooMsgBe import FlooMsgBe
from FlooMsgOk import FlooMsgOk
from FlooMsgEr import FlooMsgEr
from FlooMsgFn import FlooMsgFn
from FlooMsgCp import FlooMsgCp
from FlooMsgIq import FlooMsgIq
from FlooMsgCt import FlooMsgCt
from FlooMsgDc import FlooMsgDc
from FlooMsgAc import FlooMsgAc
from FlooMsgLf import FlooMsgLf
from FlooMsgVr import FlooMsgVr
from FlooMsgMd import FlooMsgMd
from FlooMsgTc import FlooMsgTc
from FlooMsgFd import FlooMsgFd
from FlooMsgFt import FlooMsgFt
import wx


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
        self.audioMode = None
        self.preferLea = None
        self.broadcastMode = None
        self.broadcastName = None
        self.broadcastKey = None
        self.pairedDevices = []
        self.sourceState = None
        self.a2dpSink = False
        self.feature = None

    def reset(self):
        self.state = FlooStateMachine.INIT
        self.lastCmd = None
        self.pendingCmdPara = None
        self.a2dpSink = False
        self.feature = None

    def run(self):
        self.inf.run()

    def interfaceState(self, enabled: bool, port: str):
        if enabled and self.state == FlooStateMachine.INIT:
            cmdReadVersion = FlooMsgVr(True)
            self.inf.sendMsg(cmdReadVersion)
            self.lastCmd = cmdReadVersion
        elif not enabled:
            print("FlooStateMachine reset bypass")
            self.lastCmd = None
            self.pendingCmdPara = None
            self.state = FlooStateMachine.INIT
            wx.CallAfter(self.delegate.deviceDetected, False, None)

    def handleMessage(self, message: FlooMessage):
        print("FlooStateMachine: handleMessage " + message.header)
        if self.state == FlooStateMachine.INIT:
            if isinstance(message, FlooMsgVr):
                if isinstance(self.lastCmd, FlooMsgVr):
                    if message.verStr.startswith("AS"):
                        self.a2dpSink = True
                    else:
                        self.a2dpSink = False
                    wx.CallAfter(self.delegate.deviceDetected, True, self.inf.port_name, message.verStr)
                    cmdGetAudioMode = FlooMsgAm(True)
                    self.inf.sendMsg(cmdGetAudioMode)
                    self.lastCmd = cmdGetAudioMode
            elif isinstance(message, FlooMsgAm):
                if isinstance(self.lastCmd, FlooMsgAm):
                    self.audioMode = message.mode
                    wx.CallAfter(self.delegate.audioModeInd, message.mode)
                    cmdGetSourceState = FlooMsgSt(True)
                    self.inf.sendMsg(cmdGetSourceState)
                    self.lastCmd = cmdGetSourceState
            elif isinstance(message, FlooMsgSt):
                if isinstance(self.lastCmd, FlooMsgSt):
                    self.sourceState = message.state
                    wx.CallAfter(self.delegate.sourceStateInd, message.state)
                    cmdGetLeaState = FlooMsgLa(True)
                    self.inf.sendMsg(cmdGetLeaState)
                    self.lastCmd = cmdGetLeaState
            elif isinstance(message, FlooMsgLa):
                if isinstance(self.lastCmd, FlooMsgLa):
                    wx.CallAfter(self.delegate.leAudioStateInd, message.state)
                    cmdGetPreferLea = FlooMsgLf(True)
                    self.inf.sendMsg(cmdGetPreferLea)
                    self.lastCmd = cmdGetPreferLea
            elif isinstance(message, FlooMsgLf):
                if isinstance(self.lastCmd, FlooMsgLf):
                    wx.CallAfter(self.delegate.preferLeaInd, message.mode)
                    cmdGetBroadcastMode = FlooMsgBm(True)
                    self.inf.sendMsg(cmdGetBroadcastMode)
                    self.lastCmd = cmdGetBroadcastMode
            elif isinstance(message, FlooMsgBm):
                if isinstance(self.lastCmd, FlooMsgBm):
                    self.broadcastMode = message.mode
                    wx.CallAfter(self.delegate.broadcastModeInd, message.mode)
                    cmdGetBroadcastName = FlooMsgBn(True)
                    self.inf.sendMsg(cmdGetBroadcastName)
                    self.lastCmd = cmdGetBroadcastName
            elif isinstance(message, FlooMsgBn):
                if isinstance(self.lastCmd, FlooMsgBn):
                    self.broadcastName = message.name
                    wx.CallAfter(self.delegate.broadcastNameInd, message.name)
                    self.pairedDevices.clear()
                    cmdGetDeviceName = FlooMsgFn(True)
                    self.inf.sendMsg(cmdGetDeviceName)
                    self.lastCmd = cmdGetDeviceName
            elif isinstance(message, FlooMsgFn):
                if isinstance(self.lastCmd, FlooMsgFn):
                    if message.btAddress is None:
                        # end of the device list
                        wx.CallAfter(self.delegate.pairedDevicesUpdateInd, self.pairedDevices)
                        cmdGetFeature = FlooMsgFt(True)
                        self.inf.sendMsg(cmdGetFeature)
                        self.lastCmd = cmdGetFeature
                    else:
                        self.pairedDevices.append(message.name)
            elif isinstance(message, FlooMsgFt):
                if isinstance(self.lastCmd, FlooMsgFt):
                    self.feature = message.feature
                    wx.CallAfter(self.delegate.ledEnabledInd, message.feature & 0x01)
                    wx.CallAfter(self.delegate.aptxLosslessEnabledInd, 1 if (message.feature & 0x02) == 0x02 else 0)
                    wx.CallAfter(self.delegate.gattClientEnabledInd, 1 if (self.feature & 0x04) == 0x04 else 0)
                    wx.CallAfter(self.delegate.audioSourceInd, 1 if (self.feature & 0x08) == 0x08 else 0)
                    cmdGetCodecInUse = FlooMsgAc(True)
                    self.inf.sendMsg(cmdGetCodecInUse)
                    self.lastCmd = cmdGetCodecInUse
            elif isinstance(message, FlooMsgAc) or isinstance(message, FlooMsgEr):
                if isinstance(self.lastCmd, FlooMsgAc) and isinstance(message, FlooMsgAc):
                    wx.CallAfter(self.delegate.audioCodecInUseInd, message.codec, message.rssi, message.rate,
                                 message.spkSampleRate, message.micSampleRate, message.sduInterval, message.transportDelay,
                                 message.presentDelay)
                    self.lastCmd = None
                    self.state = FlooStateMachine.CONNECTED

        elif self.state == FlooStateMachine.CONNECTED:
            if isinstance(message, FlooMsgOk):
                if isinstance(self.lastCmd, FlooMsgAm):
                    self.audioMode = self.pendingCmdPara
                    self.lastCmd = None
                elif isinstance(self.lastCmd, FlooMsgLf):
                    self.preferLea = self.pendingCmdPara
                    self.lastCmd = None
                elif isinstance(self.lastCmd, FlooMsgBm):
                    self.broadcastMode = self.pendingCmdPara
                    self.lastCmd = None
                elif isinstance(self.lastCmd, FlooMsgBn):
                    self.broadcastName = self.pendingCmdPara
                    self.lastCmd = None
                elif isinstance(self.lastCmd, FlooMsgBe):
                    self.lastCmd = None
                elif isinstance(self.lastCmd, FlooMsgCp):
                    self.pairedDevices.clear()
                    self.delegate.pairedDevicesUpdateInd([])
                elif isinstance(self.lastCmd, FlooMsgFt):
                    self.feature = self.lastCmd.feature
                    self.lastCmd = None
                else:
                    self.lastCmd = None
                self.pendingCmdPara = None
            elif isinstance(message, FlooMsgEr):
                if isinstance(self.lastCmd, FlooMsgAm):
                    wx.CallAfter(self.delegate.audioModeInd, self.audioMode)
                elif isinstance(self.lastCmd, FlooMsgLf):
                    wx.CallAfter(self.delegate.preferLeaInd, self.preferLea)
                elif isinstance(self.lastCmd, FlooMsgBm):
                    wx.CallAfter(self.delegate.broadcastModeInd, self.broadcastMode)
                elif isinstance(self.lastCmd, FlooMsgBn):
                    wx.CallAfter(self.delegate.broadcastNameInd, self.broadcastName)
                elif isinstance(self.lastCmd, FlooMsgFt):
                    wx.CallAfter(self.delegate.ledEnabledInd, self.feature & 0x01)
                    wx.CallAfter(self.delegate.aptxLosslessEnabledInd, 1 if (self.feature & 0x02) == 0x02 else 0)
                    wx.CallAfter(self.delegate.gattClientEnabledInd, 1 if (self.feature & 0x04) == 0x04 else 0)
                self.lastCmd = None
                self.pendingCmdPara = None
            elif isinstance(message, FlooMsgSt):
                self.sourceState = message.state
                wx.CallAfter(self.delegate.sourceStateInd, message.state)
                if message.state == 4 or message.state == 6:
                    self.getRecentlyUsedDevices()
            elif isinstance(message, FlooMsgLa):
                wx.CallAfter(self.delegate.leAudioStateInd, message.state)
            elif isinstance(message, FlooMsgFn):
                if message.btAddress is None:
                    # end of the device list
                    wx.CallAfter(self.delegate.pairedDevicesUpdateInd, self.pairedDevices)
                    self.lastCmd = None
                else:
                    self.pairedDevices.append(message.name)
            elif isinstance(message, FlooMsgAc):
                wx.CallAfter(self.delegate.audioCodecInUseInd, message.codec, message.rssi, message.rate,
                             message.spkSampleRate, message.micSampleRate, message.sduInterval, message.transportDelay,
                             message.presentDelay)
            elif isinstance(message, FlooMsgFt):
                self.feature = message.feature
                wx.CallAfter(self.delegate.ledEnabledInd, self.feature & 0x01)
                wx.CallAfter(self.delegate.aptxLosslessEnabledInd, 1 if (self.feature & 0x02) == 0x02 else 0)
                wx.CallAfter(self.delegate.gattClientEnabledInd, 1 if (self.feature & 0x04) == 0x04 else 0)

    def setAudioMode(self, mode: int):
        if self.state == FlooStateMachine.CONNECTED:
            cmdSetAudioMode = FlooMsgAm(True, mode)
            self.pendingCmdPara = mode
            self.lastCmd = cmdSetAudioMode
            self.inf.sendMsg(cmdSetAudioMode)

    def setPreferLea(self, enable: bool):
        if self.state == FlooStateMachine.CONNECTED:
            cmdPreferLea = FlooMsgLf(True, 1 if enable else 0)
            self.pendingCmdPara = enable
            self.lastCmd = cmdPreferLea
            self.inf.sendMsg(cmdPreferLea)

    def setPublicBroadcast(self, enable: bool):
        oldValue = self.broadcastMode & 2 == 2
        if oldValue != enable:
            print("setPublicBroadcast")
            self.pendingCmdPara = (self.broadcastMode & 0x3D) + (2 if enable else 0)
            cmdSetBroadcastMode = FlooMsgBm(True, self.pendingCmdPara)
            self.lastCmd = cmdSetBroadcastMode
            self.inf.sendMsg(cmdSetBroadcastMode)

    def setBroadcastHighQuality(self, enable: bool):
        oldValue = self.broadcastMode & 4 == 4
        if oldValue != enable:
            print("setBroadcastHighQuality")
            self.pendingCmdPara = (self.broadcastMode & 0x3B) + (4 if enable else 0)
            cmdSetBroadcastMode = FlooMsgBm(True, self.pendingCmdPara)
            self.lastCmd = cmdSetBroadcastMode
            self.inf.sendMsg(cmdSetBroadcastMode)

    def setBroadcastEncrypt(self, enable: bool):
        oldValue = self.broadcastMode & 1 == 1
        if oldValue != enable:
            print("setBroadcastEncrypt old: %d, new %d" % (oldValue, enable))
            self.pendingCmdPara = (self.broadcastMode & 0x3E) + (1 if enable else 0)
            cmdSetBroadcastMode = FlooMsgBm(True, self.pendingCmdPara)
            self.lastCmd = cmdSetBroadcastMode
            self.inf.sendMsg(cmdSetBroadcastMode)

    def setBroadcastStopOnIdle(self, enable: bool):
        oldValue = self.broadcastMode & 8 == 8
        if oldValue != enable:
            print("setBroadcastStopOnIdle old: %d, new %d" % (oldValue, enable))
            self.pendingCmdPara = (self.broadcastMode & 0x37) + (8 if enable else 0)
            cmdSetBroadcastMode = FlooMsgBm(True, self.pendingCmdPara)
            self.lastCmd = cmdSetBroadcastMode
            self.inf.sendMsg(cmdSetBroadcastMode)

    def setBroadcastLatency(self, mode: int):
        oldValue = (self.broadcastMode & 0x30) >> 4
        if oldValue != mode:
            print("setBroadcastLatency old: %d, new %d" % (oldValue, mode))
            self.pendingCmdPara = (self.broadcastMode & 0xF) + (mode << 4)
            cmdSetBroadcastMode = FlooMsgBm(True, self.pendingCmdPara)
            self.lastCmd = cmdSetBroadcastMode
            self.inf.sendMsg(cmdSetBroadcastMode)

    def setBroadcastName(self, name: str):
        if self.state == FlooStateMachine.CONNECTED:
            cmdSetBroadcastName = FlooMsgBn(True, name)
            self.pendingCmdPara = name
            self.lastCmd = cmdSetBroadcastName
            self.inf.sendMsg(cmdSetBroadcastName)

    def setBroadcastKey(self, key: str):
        if self.state == FlooStateMachine.CONNECTED:
            cmdSetBroadcastKey = FlooMsgBe(True, key)
            self.pendingCmdPara = key
            self.lastCmd = cmdSetBroadcastKey
            self.inf.sendMsg(cmdSetBroadcastKey)

    def setNewPairing(self):
        if self.state == FlooStateMachine.CONNECTED:
            if self.a2dpSink:
                cmdSetDiscoverable = FlooMsgMd(True, 1)
                self.pendingCmdPara = 1
                self.lastCmd = cmdSetDiscoverable
                self.inf.sendMsg(cmdSetDiscoverable)
            else:
                cmdStartNewPairing = FlooMsgIq()
                self.lastCmd = cmdStartNewPairing
                self.inf.sendMsg(cmdStartNewPairing)

    def clearAllPairedDevices(self):
        if self.state == FlooStateMachine.CONNECTED:
            cmdClearAllPairedDevices = FlooMsgCp()
            self.lastCmd = cmdClearAllPairedDevices
            self.inf.sendMsg(cmdClearAllPairedDevices)

    def clearIndexedDevice(self, index: int):
        if self.state == FlooStateMachine.CONNECTED:
            cmdClearIndexedDevice = FlooMsgCp(index)
            self.lastCmd = cmdClearIndexedDevice
            self.inf.sendMsg(cmdClearIndexedDevice)

    def getRecentlyUsedDevices(self):
        if self.state == FlooStateMachine.CONNECTED:
            self.pairedDevices.clear()
            cmdGetDeviceName = FlooMsgFn(True)
            self.lastCmd = cmdGetDeviceName
            self.inf.sendMsg(cmdGetDeviceName)

    def toggleConnection(self, index: int):
        if self.state == FlooStateMachine.CONNECTED:
            cmdToggleConnection = FlooMsgTc(index)
            self.lastCmd = cmdToggleConnection
            self.inf.sendMsg(cmdToggleConnection)

    def enableLed(self, onOff: int):
        if self.state == FlooStateMachine.CONNECTED:
            feature = (self.feature & 0x0E) + onOff
            cmdLedOnOff = FlooMsgFt(True, feature)
            self.pendingCmdPara = feature
            self.lastCmd = cmdLedOnOff
            self.inf.sendMsg(cmdLedOnOff)

    def enableAptxLossless(self, onOff: int):
        if self.state == FlooStateMachine.CONNECTED:
            feature = (self.feature & 0x0D) + (0x02 if onOff else 0x00)
            cmdLosslessOnOff = FlooMsgFt(True, feature)
            self.lastCmd = cmdLosslessOnOff
            self.inf.sendMsg(cmdLosslessOnOff)

    def enableGattClient(self, onOff: int):
        if self.state == FlooStateMachine.CONNECTED:
            feature = (self.feature & 0x0B) + (0x04 if onOff else 0x00)
            cmdGattClientOnOff = FlooMsgFt(True, feature)
            self.lastCmd = cmdGattClientOnOff
            self.inf.sendMsg(cmdGattClientOnOff)

    def enableUsbInput(self, onOff: int):
        if self.state == FlooStateMachine.CONNECTED:
            feature = (self.feature & 0x07) + (0x08 if onOff else 0x00)
            cmdLedOnOff = FlooMsgFt(True, feature)
            self.pendingCmdPara = feature
            self.lastCmd = cmdLedOnOff
            self.inf.sendMsg(cmdLedOnOff)

from FlooMessage import FlooMessage

class FlooMsgAc(FlooMessage):
    """Audio Codec in Use
    AC=xx
    xx: 01 Voice CVSD
        02 Voice mSBC
        03 A2DP SBC
        04 A2DP APTX
        05 A2DP APTX HD
        06 A2DP APTX Adaptive
        07 LEA LC3
        08 LEA APTX Adaptive
        09 LEA APTX Lite
        0A A2DP APTX Adaptive Lossless
    """

    HEADER = "AC"

    def __init__(self, isSend, codec = None, rssi = 0, rate = 0, spkSampleRate = 0, micSampleRate = 0):
        self.codec = codec
        self.rssi = rssi
        self.rate = rate
        self.spkSampleRate = spkSampleRate * 10
        self.micSampleRate = micSampleRate * 10
        if codec == 0x0A or codec == 0x06:
            adaptiveStr = "%02X" % codec + "," + "%02X" % rssi + "," + "%04X" % rate + "," + "%04X" % self.spkSampleRate
            super().__init__(isSend, FlooMsgAc.HEADER, bytes(adaptiveStr, 'ascii'))
        elif codec != None:
            codecStr = "%02X" % codec + "," + "%04X" % self.spkSampleRate + "," + "%04X" % self.micSampleRate
            super().__init__(isSend, FlooMsgAc.HEADER, bytes(codecStr, 'ascii'))
        else:
            super().__init__(isSend, FlooMsgAc.HEADER)

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen == 5:
            return cls(False, int(payload[3:5].decode('ascii'), 16))
        elif msgLen == 13:
            return cls(False, int(payload[3:5].decode('ascii'), 16),
                       int(payload[6:8].decode('ascii'), 16),
                       int(payload[9:13].decode('ascii'), 16))
        elif msgLen == 18:
            return cls(False, int(payload[3:5].decode('ascii'), 16),
                       int(payload[6:8].decode('ascii'), 16),
                       int(payload[9:13].decode('ascii'), 16),
                       int(payload[14:18].decode('ascii'), 16))
        elif msgLen == 23:
            return cls(False, int(payload[3:5].decode('ascii'), 16),
                       int(payload[6:8].decode('ascii'), 16),
                       int(payload[9:13].decode('ascii'), 16),
                       int(payload[14:18].decode('ascii'), 16),
                       int(payload[19:23].decode('ascii'), 16))
        else:
            return cls(False, int(payload[3:5].decode('ascii'), 16))
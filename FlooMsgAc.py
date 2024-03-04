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

    def __init__(self, isSend, codec = None):
        self.codec = codec
        if codec != None:
            codecStr = "%02X" % codec
            super().__init__(isSend, FlooMsgAc.HEADER, bytes(codecStr, 'ascii'))
        else:
            super().__init__(isSend, FlooMsgAc.HEADER)

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen != 5:
            return None
        return cls(False, int(payload[3:5].decode('ascii'), 16))
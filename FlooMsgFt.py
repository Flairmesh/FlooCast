from FlooMessage import FlooMessage

class FlooMsgFt(FlooMessage):
    """
    BC:FT
    BC:FT=xx xx: feature bits, LSB: LED ON/OFF
    FT=xx
    """

    HEADER = "FT"

    def __init__(self, isSend, feature = None):
        self.feature = feature
        if feature != None:
            featureStr = "%02X" % feature
            super().__init__(isSend, FlooMsgFt.HEADER, bytes(featureStr, 'ascii'))
        else:
            super().__init__(isSend, FlooMsgFt.HEADER)

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen < 5:
            return None
        return cls(False, int(payload[3:5].decode('ascii'), 16))
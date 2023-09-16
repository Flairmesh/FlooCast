from FlooMessage import FlooMessage

class FlooMsgLf(FlooMessage):
    """
    BC:LF
    BC:LF=xx xx:00 prefer A2DP, 01 prefer LEA
    LF=xx
    """

    HEADER = "LF"

    def __init__(self, isSend, mode = None):
        self.mode = mode
        if mode != None:
            modStr = "%02X" % mode
            super().__init__(isSend, FlooMsgLf.HEADER, bytes(modStr, 'ascii'))
        else:
            super().__init__(isSend, FlooMsgLf.HEADER)

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen < 5:
            return None
        return cls(False, int(payload[3:5].decode('utf-8')))
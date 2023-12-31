from FlooMessage import FlooMessage

class FlooMsgAm(FlooMessage):
    """
    BC:AM
    BC:AM=xx xx:00 high quality, 01 gaming, 02 broadcast
    AM=xx
    """

    HEADER = "AM"

    def __init__(self, isSend, mode = None):
        self.mode = mode
        if mode != None:
            modStr = "%02X" % mode
            super().__init__(isSend, FlooMsgAm.HEADER, bytes(modStr, 'ascii'))
        else:
            super().__init__(isSend, FlooMsgAm.HEADER)

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen < 5:
            return None
        return cls(False, int(payload[3:5].decode('utf-8')))
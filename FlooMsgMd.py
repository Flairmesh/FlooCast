from FlooMessage import FlooMessage

class FlooMsgMd(FlooMessage):
    """
    BC:MD
    BC:MD=xx xx:00 discoverable off, 01 discoverable on
    MD=xx
    """

    HEADER = "MD"

    def __init__(self, isSend, mode = None):
        self.mode = mode
        if mode != None:
            modStr = "%02X" % mode
            super().__init__(isSend, FlooMsgMd.HEADER, bytes(modStr, 'ascii'))
        else:
            super().__init__(isSend, FlooMsgMd.HEADER)

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen < 5:
            return None
        return cls(False, int(payload[3:5].decode('utf-8')))
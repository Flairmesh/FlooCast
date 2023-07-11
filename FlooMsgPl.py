from FlooMessage import FlooMessage

class FlooMsgPl(FlooMessage):
    """
    BC:PL
    PL=index(U8),addr(U48),name(str)
    """

    HEADER = "PL"

    def __init__(self, isSend, index = None, addr = None, name = None, payload = None):
        self.index = index
        self.addr = addr
        self.name = name
        if isSend:
            super().__init__(isSend, FlooMsgPl.HEADER)
        else:
            super().__init__(isSend, FlooMsgPl.HEADER, payload)

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen < 20:
            return None
        return cls(False, int(payload[3:5].decode('utf-8')), payload[6:18], payload[19:], payload[3:])
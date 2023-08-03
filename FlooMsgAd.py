from FlooMessage import FlooMessage

class FlooMsgAd(FlooMessage):
    """
    BC:AD
    AD=addr(U48)
    """

    HEADER = "AD"

    def __init__(self, isSend, addr = None, payload = None):
        self.addr = addr
        if isSend:
            super().__init__(isSend, FlooMsgAd.HEADER)
        else:
            super().__init__(isSend, FlooMsgAd.HEADER, payload)

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen != 15:
            return None
        return cls(False, payload[3:15], payload[3:])
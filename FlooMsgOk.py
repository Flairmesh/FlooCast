from FlooMessage import FlooMessage

class FlooMsgOk(FlooMessage):
    """OK message format: OK"""

    HEADER = "OK"

    def __init__(self, isSend):
        super().__init__(isSend, FlooMsgOk.HEADER)

    @classmethod
    def create_valid_msg(cls, pkt: bytes):
        msgLen = len(pkt)
        if msgLen != 2:
            return None
        return cls(False)
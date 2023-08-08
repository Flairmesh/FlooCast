from FlooMessage import FlooMessage

class FlooMsgUnknown(FlooMessage):
    """Unknown message"""

    HEADER = "~~"

    def __init__(self, isSend):
        super().__init__(isSend, FlooMsgUnknown.HEADER)

    @classmethod
    def create_valid_msg(cls, pkt: bytes = None):
        return cls(False)
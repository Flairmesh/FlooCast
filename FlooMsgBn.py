from FlooMessage import FlooMessage

class FlooMsgBn(FlooMessage):
    """
    BC:BN
    BN=<name>
    """

    HEADER = "BN"

    def __init__(self, isSend, name = None):
        self.name = name
        if isSend or name is None:
            super().__init__(isSend, FlooMsgBn.HEADER)
        else:
            super().__init__(isSend, FlooMsgBn.HEADER, bytes(name, 'utf-8'))

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen < 7:
            return None
        return cls(False, payload[3:].decode('utf-8'))
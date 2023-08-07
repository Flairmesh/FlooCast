from FlooMessage import FlooMessage

class FlooMsgBe(FlooMessage):
    """
    BC:BE=<KEY> : key of length <=16
    BN=00 or 01 : 00 key has not been set, 01 key set.
    """

    HEADER = "BE"

    def __init__(self, isSend, key = None):
        self.key = key
        if not isSend or name is None:
            super().__init__(isSend, FlooMsgBe.HEADER)
        else:
            super().__init__(isSend, FlooMsgBe.HEADER, bytes(key, 'utf-8'))

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen != 5:
            return None
        return cls(False, payload[3:].decode('utf-8'))
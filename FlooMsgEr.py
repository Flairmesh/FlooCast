from FlooMessage import FlooMessage

class FlooMsgEr(FlooMessage):
    """Error message
    ER=xx
    xx: 01 Last command not allowed in current state
        02 Format error in the last command
    """

    HEADER = "ER"

    def __init__(self, isSend, error):
        self.error = error
        errStr = "%02d" % error
        super().__init__(isSend, FlooMsgEr.HEADER, bytes(errStr, 'ascii'))

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen != 5:
            return None
        return cls(False, int(payload[3:5].decode('ascii')))
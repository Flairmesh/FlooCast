from FlooMessage import FlooMessage

class FlooMsgLa(FlooMessage):
    """
    BC:LA
    LA=xx
    xx: 00 disconnected
        01 connected
        02 unicast streaming starting
        03 unicast streaming
        04 broadcast streaming starting,
        05 broadcast streaming
        06 streaming stopping
    """

    HEADER = "LA"

    def __init__(self, isSend, state = None):
        self.state = state
        if state != None:
            stateStr = "%02X" % state
            super().__init__(isSend, FlooMsgLa.HEADER, bytes(stateStr, 'ascii'))
        else:
            super().__init__(isSend, FlooMsgLa.HEADER)

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen != 5:
            return None
        return cls(False, int(payload[3:5].decode('ascii')))
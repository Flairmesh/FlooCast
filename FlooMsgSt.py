from FlooMessage import FlooMessage

class FlooMsgSt(FlooMessage):
    """
    BC:ST
    ST=xx
    xx: 00 Init
        01 Idle
        02 Pairing
        03 Connecting
        04 Connected
        05 Audio starting
        06 Audio streaming
        07 Audio stopping
        08 Disconnecting
        09 Voice staring
        0A Voice streaming
        0B Voice stopping
    """

    HEADER = "ST"

    def __init__(self, isSend, state = None):
        self.state = state
        if state != None:
            stateStr = "%02X" % state
            super().__init__(isSend, FlooMsgSt.HEADER, bytes(stateStr, 'ascii'))
        else:
            super().__init__(isSend, FlooMsgSt.HEADER)

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen != 5:
            return None
        return cls(False, int(payload[3:5].decode('ascii'), 16))
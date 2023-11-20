from FlooMessage import FlooMessage

class FlooMsgVr(FlooMessage):
    """
    BC:VR
    VR=version string, such as 1.0.0.0
    """

    HEADER = "VR"

    def __init__(self, isSend, version = None):
        self.verStr = version
        if isSend:
            super().__init__(isSend, FlooMsgVr.HEADER)
        else:
            super().__init__(isSend, FlooMsgVr.HEADER, bytes(version, 'utf-8'))

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen < 4:
            return None
        return cls(False, payload[3:].decode('utf-8'))
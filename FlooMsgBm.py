from FlooMessage import FlooMessage

class FlooMsgBm(FlooMessage):
    """
    BC:BM
    BC:BM=xx xx:00 TMAP broadcast, no encrypt
                01 TMAP broadcast, encrypted
                02 PBP broadcast, no encrypt
                03 PBP broadcast, encrypted
    BM=xx
    """

    HEADER = "BM"

    def __init__(self, isSend, mode = None):
        self.mode = mode
        if mode != None:
            modStr = "%02X" % mode
            super().__init__(isSend, FlooMsgBm.HEADER, bytes(modStr, 'ascii'))
        else:
            super().__init__(isSend, FlooMsgBm.HEADER)

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen < 5:
            return None
        return cls(False, int(payload[3:5].decode('ascii')))
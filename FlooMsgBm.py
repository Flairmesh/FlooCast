from FlooMessage import FlooMessage

class FlooMsgBm(FlooMessage):
    """
    BC:BM
    BC:BM=xx xx:Bit 0~1:
                0 TMAP broadcast, no encrypt
                1 TMAP broadcast, encrypted
                2 PBP broadcast, no encrypt
                3 PBP broadcast, encrypted
                Bit 2:
                0 Broadcast in standard quality
                1 Broadcast in high quality
                Bit 3:
                0 Maintain broadcast for 3 minutes after USB audio playback ends
                1 Stop broadcasting immediately when USB audio playback ends
                Bit 4~5:
                0 reserved
                1 lowest latency
                2 lower latency
                3 default
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
        if msgLen != 5:
            return None
        return cls(False, int(payload[3:5].decode('ascii'), 16))
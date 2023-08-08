from FlooMessage import FlooMessage

class FlooMsgFn(FlooMessage):
    """
    BC:FN
    FN=<index>,<name>
    """

    HEADER = "FN"

    def __init__(self, isSend, index = None, btAddress = None, name = None):
        if isSend:
            self.index = None
            self.name = None
            self.btAddress = None
            super().__init__(isSend, FlooMsgFn.HEADER)
        else:
            self.index = index
            self.btAddress = btAddress
            if btAddress is None:
                self.name = None
                paramStr = "%02X" % index
            else:
                self.name = "No Name" if name is None else name
                paramStr = "%02X,%s,%s" % (index, btAddress, self.name)
            super().__init__(isSend, FlooMsgFn.HEADER, bytes(paramStr, 'utf-8'))

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen == 5:
            return cls(False, int(payload[3:5].decode('ascii')))
        elif msgLen == 18:
            return cls(False, int(payload[3:5].decode('ascii')), payload[6:].decode('utf-8'))
        elif msgLen > 19:
            return cls(False, int(payload[3:5].decode('ascii')), payload[6:18].decode('utf-8'), payload[19:].decode('utf-8'))
        else:
            return None
class FlooMessage:
    """FlooGoo BAI message"""

    def __init__(self, isSend, header, payload = None):
        super().__init__()
        self.isSend = isSend
        self.header = header
        self.bytes = bytearray()
        if isSend:
            self.bytes.extend(bytes("BC:", 'ascii'))
        self.bytes.extend(bytes(header, 'ascii'))
        if payload != None:
            self.bytes.extend(bytes("=", 'ascii'))
            self.bytes.extend(payload)
        self.bytes.extend(bytes("\r\n", 'ascii'))


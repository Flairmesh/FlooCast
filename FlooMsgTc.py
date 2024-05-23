from FlooMessage import FlooMessage

class FlooMsgTc(FlooMessage):
    """
    BC:TC
    BC:TC=xx xx:index of the device
    The module replies OK or ER for TC command
    """

    HEADER = "TC"

    def __init__(self, index = None):
        if index is None:
            super().__init__(True, FlooMsgTc.HEADER)
        else:
            paramStr = "%02X" % index
            super().__init__(True, FlooMsgTc.HEADER, bytes(paramStr, 'ascii'))

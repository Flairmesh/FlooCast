from FlooMessage import FlooMessage

class FlooMsgCt(FlooMessage):
    """
    BC:CT
    BC:CP=xx xx:index of the device
    The module replies OK or ER
    """

    HEADER = "CT"

    def __init__(self, index = None):
        if index is None:
            super().__init__(True, FlooMsgCt.HEADER)
        else:
            paramStr = "%02X" % index
            super().__init__(True, FlooMsgCt.HEADER, bytes(paramStr, 'ascii'))

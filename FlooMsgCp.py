from FlooMessage import FlooMessage

class FlooMsgCp(FlooMessage):
    """
    BC:CP
    BC:CP=xx xx:index of the device
    The module replies OK or ER for CP command
    """

    HEADER = "CP"

    def __init__(self, index = None):
        if index is None:
            super().__init__(True, FlooMsgCp.HEADER)
        else:
            paramStr = "%02X" % index
            super().__init__(True, FlooMsgCP.HEADER, bytes(paramStr, 'ascii'))

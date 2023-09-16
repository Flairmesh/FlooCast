from FlooMessage import FlooMessage

class FlooMsgDc(FlooMessage):
    """
    BC:DC
    The module replies OK or ER for CP command
    """

    HEADER = "DC"

    def __init__(self):
        super().__init__(True, FlooMsgDc.HEADER)

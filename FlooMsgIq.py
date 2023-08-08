from FlooMessage import FlooMessage

class FlooMsgIq(FlooMessage):
    """
    BC:IQ
    """

    HEADER = "IQ"

    def __init__(self):
        super().__init__(True, FlooMsgIq.HEADER)

from FlooMessage import FlooMessage

class FlooMsgFd(FlooMessage):
    """
    BC:FD
    The module replies OK for CP command
    """

    HEADER = "FD"

    def __init__(self):
        super().__init__(True, FlooMsgFd.HEADER)

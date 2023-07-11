from FlooMessage import FlooMessage
from FlooMsgOk import FlooMsgOk
from FlooMsgPl import FlooMsgPl
from FlooMsgAd import FlooMsgAd

class FlooParser:
    """FlooGoo message parser"""

    MSG_HEADERS =  {
        FlooMsgOk.HEADER : FlooMsgOk.create_valid_msg,
        FlooMsgPl.HEADER : FlooMsgPl.create_valid_msg,
        FlooMsgAd.HEADER : FlooMsgAd.create_valid_msg
    }

    def __init__(self):
        super().__init__()

    def create_valid_message(self, pkt: bytes) -> FlooMessage:
        msgLen = len(pkt)
        if msgLen < 2:
            return None
        msgHeader = pkt[:2].decode('utf-8')
        if msgHeader in FlooParser.MSG_HEADERS.keys():
            print("FlooParser: create a " + msgHeader + " message")
            return FlooParser.MSG_HEADERS[msgHeader](pkt)
        return None

    def run(self, pkt: bytes) -> FlooMessage:
        return self.create_valid_message(pkt)


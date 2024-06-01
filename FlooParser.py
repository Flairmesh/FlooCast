from FlooMessage import FlooMessage
from FlooMsgPl import FlooMsgPl
from FlooMsgAd import FlooMsgAd
from FlooMsgAm import FlooMsgAm
from FlooMsgLa import FlooMsgLa
from FlooMsgSt import FlooMsgSt
from FlooMsgBm import FlooMsgBm
from FlooMsgBn import FlooMsgBn
from FlooMsgFn import FlooMsgFn
from FlooMsgOk import FlooMsgOk
from FlooMsgEr import FlooMsgEr
from FlooMsgAc import FlooMsgAc
from FlooMsgLf import FlooMsgLf
from FlooMsgVr import FlooMsgVr
from FlooMsgFt import FlooMsgFt
from FlooMsgUnknown import FlooMsgUnknown

class FlooParser:
    """FlooGoo message parser"""

    MSG_HEADERS =  {
        FlooMsgOk.HEADER : FlooMsgOk.create_valid_msg,
        FlooMsgPl.HEADER : FlooMsgPl.create_valid_msg,
        FlooMsgAd.HEADER : FlooMsgAd.create_valid_msg,
        FlooMsgAm.HEADER : FlooMsgAm.create_valid_msg,
        FlooMsgLa.HEADER : FlooMsgLa.create_valid_msg,
        FlooMsgSt.HEADER : FlooMsgSt.create_valid_msg,
        FlooMsgBm.HEADER : FlooMsgBm.create_valid_msg,
        FlooMsgBn.HEADER : FlooMsgBn.create_valid_msg,
        FlooMsgFn.HEADER : FlooMsgFn.create_valid_msg,
        FlooMsgOk.HEADER : FlooMsgOk.create_valid_msg,
        FlooMsgEr.HEADER : FlooMsgEr.create_valid_msg,
        FlooMsgAc.HEADER : FlooMsgAc.create_valid_msg,
        FlooMsgLf.HEADER : FlooMsgLf.create_valid_msg,
        FlooMsgVr.HEADER : FlooMsgVr.create_valid_msg,
        FlooMsgFt.HEADER : FlooMsgFt.create_valid_msg
    }

    def __init__(self):
        super().__init__()

    def create_valid_message(self, pkt: bytes) -> FlooMessage:
        msgLen = len(pkt)
        if msgLen < 2:
            return None
        msgHeader = pkt[:2].decode('ascii')
        if msgHeader in FlooParser.MSG_HEADERS.keys():
            print("FlooParser: create a " + msgHeader + " message")
            return FlooParser.MSG_HEADERS[msgHeader](pkt)
        else:
            return FlooMsgUnknown(False)
        return None

    def run(self, pkt: bytes) -> FlooMessage:
        return self.create_valid_message(pkt)


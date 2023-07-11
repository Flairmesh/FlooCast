from FlooMessage import FlooMessage

class FlooInterfaceDelegate:

    def interfaceState(self, enabled: bool, port: str):
        """The delegate shall handle the state of the interface."""
        pass

    def handleMessage(self, message: FlooMessage):
        """The delegate shall handle the message got from the interface."""
        pass
class FlooStateMachineDelegate:
    def deviceDetected(self, flag: bool, port: str):
        """Called when FlooGoo device connection state changes."""
        pass

    def audioModeInd(self, mode: int):
        """Called when FlooGoo device reports current audio mode."""
        pass

    def sourceStateInd(self, state: int):
        """Called when FlooGoo device reports current source state."""
        pass

    def leAudioStateInd(self, state: int):
        """Called when FlooGoo device reports current LE audio state."""
        pass

    def broadcastModeInd(self, state: int):
        """Called when FlooGoo device reports current broadcast mode."""
        pass

    def broadcastNameInd(self, name):
        """Called when FlooGoo device reports current LE audio state."""
        pass




import subprocess
import threading
import sys, io
import time
from subprocess import PIPE, Popen
from threading  import Thread
from tkinter import messagebox
import tkinter as tk

class FlooDfuThread(threading.Thread):
    #
    # Pre-defined constants, 0~100 as progress
    #
    DFU_STATE_DONE = 101

    def __init__(self, cmd, stateCallback):
        self.cmd = cmd
        self.stateCallback = stateCallback
        threading.Thread.__init__(self)

    def run(self):
        try:
            myDll = HidDfu(self.cmd[0])
            retval, count = myDll.hidDfuConnect(vid=0x0A12, pid=0x4007, usage=1, usagePage=0xFF00)
            if retval == HidDfu.HIDDFU_ERROR_NONE:
                retval = myDll.hidDfuUpgradeBin(fileName=self.cmd[1])
                if retval == HidDfu.HIDDFU_ERROR_NONE:
                    progress = 0
                    while True:
                        progress = myDll.hidDfuGetProgress()
                        self.stateCallback(progress)
                        if progress == 100:
                            break
                        else:
                            time.sleep(0.5)
                    retval = myDll.hidDfuGetResult()
                    if retval == HidDfu.HIDDFU_ERROR_NONE:
                        time.sleep(2.0)
                        self.stateCallback(FlooDfuThread.DFU_STATE_DONE - myDll.hidDfuDisconnect())
                    else:
                        self.stateCallback(FlooDfuThread.DFU_STATE_DONE - retval)
            else:
                self.stateCallback(retval)
        except Exception as exec0:
            print(exec0)


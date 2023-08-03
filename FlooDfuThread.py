import subprocess
import threading
import sys, io
from subprocess import PIPE, Popen
from threading  import Thread
import tkinter as tk

class FlooDfuThread(threading.Thread):
    def __init__(self, cmd, stateCallback):
        self.cmd = cmd
        self.stateCallback = stateCallback
        threading.Thread.__init__(self)

    def run(self):
        try:
            p = Popen(self.cmd, stdout=PIPE, stdin=PIPE, stderr=subprocess.STDOUT)
            for line in io.TextIOWrapper(p.stdout, encoding="utf-8"):  # or another encoding
                self.stateCallback(line)
            p.wait()
            self.stateCallback(None)
        except Exception as exec0:
            print(exec0)


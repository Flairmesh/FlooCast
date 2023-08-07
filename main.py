# Import Module
import gettext
import locale
import os
import platform
import sys
import tkinter as tk
import webbrowser
import pystray
from tkinter import ttk
from tkinter import filedialog as fd
from EntryWithPlaceholder import EntryWithPlaceholder
from FlooStateMachine import FlooStateMachine
from FlooStateMachineDelegate import FlooStateMachineDelegate
from FlooDfuThread import FlooDfuThread
from PIL import Image
from pystray import MenuItem as TrayMenuItem


appIcon = "FlooCastApp.ico"
appGif = "FlooPasteApp.gif"
appTitle = "FlooCast"
appLogoPng = "FlooCastHeader.png"

userLocale = locale.getdefaultlocale()
lan = userLocale[0].split('_')[0]
# print(lan)

# Set the local directory
app_path = os.path.abspath(os.path.dirname(sys.argv[0]))
localedir = app_path + os.sep +'locale'
# Set up your magic function
translate = gettext.translation("messages", localedir, languages=[lan], fallback=True)
translate.install()
_ = translate.gettext

# create root window
root = tk.Tk()

# root window title and dimension
root.title(appTitle)
if platform.system().lower().startswith('win'):
    root.iconbitmap(app_path + os.sep + appIcon)
elif platform.system().lower().startswith('lin'):
    img_icon = tk.PhotoImage(file=app_path + os.sep + appGif)
    root.tk.call('wm', 'iconphoto', root._w, img_icon)
# Set geometry (widthxheight)
root.geometry('720x400')

mainFrame = tk.Frame(root, relief=tk.RAISED)
mainFrame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# statusBar
statusBar = tk.Label(root, text=_("Initializing"), bd=1, relief=tk.SUNKEN, anchor=tk.W)
statusBar.pack(side=tk.BOTTOM, fill=tk.X)

def update_status_bar(info: str):
    global statusBar
    statusBar.config(text=info)


# Define On/Off Images
on = tk.PhotoImage(file=app_path+os.sep+'onS.png')
off = tk.PhotoImage(file=app_path+os.sep+'offS.png')

mainFrame.rowconfigure(0, weight=0)
mainFrame.rowconfigure(1, weight=0)
mainFrame.rowconfigure(2, weight=1)
# mainFrame.grid_columnconfigure(0, weight=1)
mainFrame.columnconfigure(0, weight=1)
mainFrame.columnconfigure(1, weight=0)
# Setup contains LE Broadcast and Paired Devices
audioModePanel = ttk.LabelFrame(mainFrame, text=_('Audio Mode'))
audioModePanel.grid(column=0, row=0, padx=4, sticky='nsew')
leBroadcastPanel = ttk.LabelFrame(mainFrame, text=_('LE Broadcast'))
leBroadcastPanel.grid(column=0, row=1, padx=4, sticky='nsew')
pairedDevicesPanel = ttk.LabelFrame(mainFrame, text=_('Paired Devices'))
pairedDevicesPanel.grid(column=0, row=2, padx=4, sticky='nsew')
# Window panel
windowPanel = ttk.LabelFrame(mainFrame, text=_('Window'))
windowPanel.grid(column=1, row=0, padx=4, sticky='nsew')
# About panel
aboutPanel = ttk.LabelFrame(mainFrame, text=_('About'))
aboutPanel.grid(column=1, row=1, padx=4, rowspan=2, sticky='nsew')

# Audio mode panel
for i in range(0, 2):
    audioModePanel.rowconfigure(i, weight=i)
for i in range(0, 3):
    audioModePanel.columnconfigure(i, weight=1)

def audioModeSel():
    enable_pairing_widgets(audioMode.get() != 2)
    flooSm.setAudioMode(audioMode.get())

audioMode = tk.IntVar()
audioMode.set(0)
highQualityRadioButton = ttk.Radiobutton(audioModePanel, text=_('High Quality (one-to-one)'), variable=audioMode,
                                         value=0, command=audioModeSel)
highQualityRadioButton.grid(column=0, row=0, padx=4, sticky='w')
gamingModeRadioButton = ttk.Radiobutton(audioModePanel, text=_('Gaming (one-to-one)'), variable=audioMode,
                                        value=1, command=audioModeSel)
gamingModeRadioButton.grid(column=1, row=0, padx=4, sticky='w')
broadcastRadioButton = ttk.Radiobutton(audioModePanel, text=_('Broadcast'), variable=audioMode,
                                       value=2, command=audioModeSel)
broadcastRadioButton.grid(column=2, row=0, padx=4, sticky='w')

dongleStatePanel = ttk.LabelFrame(audioModePanel, text=_('Dongle State'))
dongleStatePanel.grid(column=0, row=1, columnspan=1, padx=4, pady=4, sticky='nsew')
dongleStateLabel = tk.Label(dongleStatePanel, text=_("Initialization"))
dongleStateLabel.place(relx=.5, rely=.5,anchor= tk.CENTER)
leaStatePanel = ttk.LabelFrame(audioModePanel, text=_('LE Audio State'))
leaStatePanel.grid(column=1, row=1, columnspan=1, padx=4, pady=4, sticky='nsew')
leaStateLabel = tk.Label(leaStatePanel, text=_("Disconnected"))
leaStateLabel.place(relx=.5, rely=.5,anchor= tk.CENTER)
codecInUsePanel = ttk.LabelFrame(audioModePanel, text=_('Codec in Use'))
codecInUsePanel.grid(column=2, row=1, columnspan=1, padx=4, pady=4, sticky='nsew')
codecInUseLabel = tk.Label(codecInUsePanel, text=_("LC3"))
codecInUseLabel.place(relx=.5, rely=.5,anchor= tk.CENTER)

# LE Broadcast panel
leBroadcastPanel.columnconfigure(0, weight=1)
leBroadcastPanel.columnconfigure(1, weight=1)
leBroadcastPanel.columnconfigure(2, weight=1)

broadcastEnableLabel = tk.Label(leBroadcastPanel, text=_("Public broadcast"))
broadcastEnableLabel.grid(column=0, row=0, columnspan=2, sticky='w')
publicBroadcastEnable = None

def public_broadcast_enable_switch_set(enable):
    global publicBroadcastEnable
    publicBroadcastEnable = enable
    publicBroadcastEnableButton.config(image= on if publicBroadcastEnable else off)
    flooSm.setPublicBroadcast(enable)

# Broadcast enable switch function
def public_broadcast_enable_switch():
    global publicBroadcastEnable
    public_broadcast_enable_switch_set(not publicBroadcastEnable)

publicBroadcastEnableButton = tk.Button(leBroadcastPanel, image=off, bd=0, command=public_broadcast_enable_switch)
publicBroadcastEnableButton.grid(column=2, row=0, sticky='e')

broadcastEncryptEnableLabel = tk.Label(leBroadcastPanel, text=_("Encrypt broadcast, please set a key first"))
broadcastEncryptEnableLabel.grid(column=0, row=1, columnspan=2, sticky='w')
broadcastEncryptEnable = None

def broadcast_encrypt_switch_set(enable):
    global broadcastEncryptEnable
    broadcastEncryptEnable = enable
    broadcastEncryptEnableButton.config(image= on if broadcastEncryptEnable else off)
    flooSm.setBroadcastEncrypt(enable)

# Broadcast encrypt enable switch function
def broadcast_encrypt_enable_switch():
    global broadcastEncryptEnable
    broadcast_encrypt_switch_set(not broadcastEncryptEnable)

broadcastEncryptEnableButton = tk.Button(leBroadcastPanel, image=off, bd=0, command=broadcast_encrypt_enable_switch)
broadcastEncryptEnableButton.grid(column=2, row=1, sticky='e')

broadcastNameLabel = tk.Label(leBroadcastPanel, text=_("Broadcast Name"))
broadcastNameLabel.grid(column=0, row=2, sticky='w')
broadcastName = tk.StringVar()

# Broadcase name entry function
def broadcast_name_entry(name: str):
    bytes = name.encode('utf-8')
    if len(bytes) > 0 and len(bytes) < 31:
        flooSm.setBroadcastName(name)
    else:
        broadcastNameEntry.put_placeholder()

broadcastNameEntry = EntryWithPlaceholder(leBroadcastPanel, textvariable=broadcastName,
                                          placeholder="Input a new name of no more than 30 characters then press <ENTER>",
                                          edit_end_proc=broadcast_name_entry)
broadcastNameEntry.grid(column=1, row=2, columnspan=2, padx=4, sticky='we')

broadcastKeyLabel = tk.Label(leBroadcastPanel, text=_("Broadcast Key"))
broadcastKeyLabel.grid(column=0, row=3, sticky='w')
broadcastKey = tk.StringVar()

# Broadcase key entry function
def broadcast_key_entry(key: str):
    print(key)
    # floo_transceiver.setShareToMobile(shareToMobile)

broadcastKeyEntry = EntryWithPlaceholder(leBroadcastPanel, textvariable=broadcastKey,
                                         placeholder=_("Input a new key of no more than 16 characters then press <ENTER>"),
                                         edit_end_proc=broadcast_key_entry)
broadcastKeyEntry.grid(column=1, row=3, columnspan=2, padx=4, sticky='we')

# New pairing button function
def button_new_pairing():
    flooSm.setNewPairing()

pairedDevicesPanel.columnconfigure(0, weight=1)
pairedDevicesPanel.columnconfigure(1, weight=1)
pairedDevicesPanel.columnconfigure(2, weight=1)

newPairFrame = tk.Frame(pairedDevicesPanel)
newPairFrame.grid(column=0, row=0, padx=4, sticky='w')
newPairingButton = tk.Button(newPairFrame, text='+', relief="groove", command=button_new_pairing)
newPairingButton.pack(side = tk.LEFT)
newPairingLabel = tk.Label(newPairFrame, text=_("Add device"))
newPairingLabel.pack(side = tk.LEFT)

# Clear all paired device function
def button_clear_all():
    global newPairingButton
    global publicBroadcastEnable
    # Determine is on or off
    if shareToMobile:
        shareToMobileButton.config(image=off)
        shareToMobile = False
    else:
        shareToMobileButton.config(image=on)
        shareToMobile = True
    floo_transceiver.setShareToMobile(shareToMobile)
    flooConfig.setShareToMobile(shareToMobile)


clearAllButton = tk.Button(pairedDevicesPanel, text=_("Clear All"), relief="groove", command=button_clear_all)
clearAllButton.grid(column=2, row=0, padx=4, sticky='we')

def enable_pairing_widgets(enable: bool):
    global clearAllButton
    global newPairingButton
    if enable:
        newPairingButton.config(state=tk.NORMAL)
        clearAllButton.config(state=tk.NORMAL)
    else:
        newPairingButton.config(state=tk.DISABLED)
        clearAllButton.config(state=tk.DISABLED)

# Window panel
def quit_all():
    root.destroy()

# Define a function for quit the window
def quit_window(icon, TrayMenuItem):
    icon.stop()
    root.destroy()

# Define a function to show the window again
def show_window(icon, TrayMenuItem):
    global windowIcon
    try:
        icon.stop()
        root.after(0, root.deiconify())
        windowIcon = None
    except Exception:
        pass

# Hide the window and show on the system taskbar
def hide_window():
    global windowIcon
    root.withdraw()
    # file_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    if platform.system().lower().startswith('win'):
        image = Image.open(app_path + os.sep + appIcon)
    elif platform.system().lower().startswith('lin'):
        image = tk.PhotoImage(file=app_path + os.sep + appGif)
    menu = (TrayMenuItem(_('Quit'), quit_window), TrayMenuItem(_('Show Window'), show_window))
    icon = pystray.Icon(appTitle, image, _("FlooGoo Bluetooth Audio Source"), menu) # "FlooGoo Bluetooth Audio Source"
    icon.run()
    windowIcon = icon


root.protocol('WM_DELETE_WINDOW', hide_window)
windowPanel.columnconfigure(0, weight=1)
windowPanel.columnconfigure(1, weight=1)
minimizeButton = tk.Button(windowPanel, text=_("Minimize to System Tray"), command=hide_window)
minimizeButton.grid(column=0, row=0, columnspan=2, padx=(10, 10), pady=(10, 10), sticky='ew')
quitButton = tk.Button(windowPanel, text=_("Quit App"), command=quit_all)
quitButton.grid(column=0, row=1, columnspan=2, padx=(10, 10), pady=(0, 10), sticky='ew')


# aboutPanel
def url_callback(url):
    webbrowser.open_new(url)


aboutFrame = tk.Frame(aboutPanel)
aboutPanel.rowconfigure(0, weight=1)
aboutPanel.rowconfigure(1, weight=1)
aboutPanel.rowconfigure(2, weight=1)
aboutFrame.grid(row=1, column=0)

logoFrame = tk.Frame(aboutFrame, relief=tk.RAISED)
logoFrame.pack(pady=4)
logo = tk.Canvas(logoFrame, width=230, height=64)
img = tk.PhotoImage(file=app_path + os.sep + appLogoPng)
logo.create_image(0, 0, anchor=tk.NW, image=img)
logo.pack()
copyRightInfo = tk.Label(aboutFrame, text="Copyright© 2023 Flairmesh Technologies.")
copyRightInfo.pack()
thirdPartyLink = tk.Label(aboutFrame, text=_("Third-Party Software Licenses"), fg="blue", cursor="hand2")
thirdPartyLink.pack()
thirdPartyLink.bind("<Button-1>", lambda e: url_callback("https://www.flairmesh.com/support/third_lic.html"))
supportLink = tk.Label(aboutFrame, text=_("Support Link"), fg="blue", cursor="hand2")
supportLink.pack()
supportLink.bind("<Button-1>", lambda e: url_callback("https://www.flairmesh.com/Dongle/FMA120.html"))
versionInfo = tk.Label(aboutFrame, text=_("Version") + "1.0.0")
versionInfo.pack()

dfuUndergoing = False
dfuInfo = tk.Label(aboutFrame, text="")

def update_dfu_info(stateStr: str):
    global dfuUndergoing
    if stateStr:
        print(stateStr)
        dfuInfo.config(text = stateStr)
        if not dfuUndergoing:
            dfuInfo.pack()
            minimizeButton.config(state=tk.DISABLED)
            quitButton.config(state=tk.DISABLED)
            dfuButton.config(state=tk.DISABLED)
            dfuUndergoing = True
    else:
        dfuInfo.pack_forget()
        minimizeButton.config(state=tk.NORMAL)
        quitButton.config(state=tk.NORMAL)
        dfuButton.config(state=tk.NORMAL)
        dfuUndergoing = False

def button_dfu():
    filename = fd.askopenfilename()
    if filename:
        print("Run DFU in directory: " + os.getcwd())
        dfuThread = FlooDfuThread(['myDfuDo.bat', filename], update_dfu_info)
        dfuThread.start()

if platform.system().lower().startswith('win'):
    dfuButton = tk.Button(aboutFrame, text=_('Device Firmware Upgrade'), relief="groove", command=button_dfu)
    dfuButton.pack()

def enable_settings_widgets(enable: bool):
    if enable:
        highQualityRadioButton.config(state=tk.NORMAL)
        gamingModeRadioButton.config(state=tk.NORMAL)
        broadcastRadioButton.config(state=tk.NORMAL)
        publicBroadcastEnableButton.config(state=tk.NORMAL)
        broadcastEncryptEnableButton.config(state=tk.NORMAL)
        broadcastNameEntry.config(state=tk.NORMAL)
        broadcastKeyEntry.config(state=tk.NORMAL)
        if platform.system().lower().startswith('win'):
            dfuButton.config(state=tk.NORMAL)
    else:
        highQualityRadioButton.config(state=tk.DISABLED)
        gamingModeRadioButton.config(state=tk.DISABLED)
        broadcastRadioButton.config(state=tk.DISABLED)
        publicBroadcastEnableButton.config(state=tk.DISABLED)
        broadcastEncryptEnableButton.config(state=tk.DISABLED)
        broadcastNameEntry.config(state=tk.DISABLED)
        broadcastKeyEntry.config(state=tk.DISABLED)
        if platform.system().lower().startswith('win'):
            dfuButton.config(state=tk.DISABLED)

enable_settings_widgets(False)

sourceStateStr = [_("Initializing"),
                  _("Idle"),
                  _("Pairing"),
                  _("Connecting"),
                  _("Connected"),
                  _("Audio staring"),
                  _("Audio streaming"),
                  _("Audio stopping"),
                  _("Disconnecting"),
                  _("Voice starting"),
                  _("Voice streaming"),
                  _("Voice stopping")]

leaStateStr = [_("Disconnected"),
               _("Connected"),
               _("Unicast starting"),
               _("Unicast streaming"),
               _("Broadcast starting"),
               _("Broadcast streaming"),
               _("Streaming stopping")]

# All GUI object initialized, start FlooStateMachine
class FlooSmDelegate(FlooStateMachineDelegate):
    def deviceDetected(self, flag: bool, port: str):
        enable_settings_widgets(flag)
        if flag:
            update_status_bar(_("Use FlooGoo dongle on ") + " " + port)
        else:
            update_status_bar(_("Please insert your FlooGoo dongle"))
            enable_pairing_widgets(False)

    def audioModeInd(self, mode: int):
        audioMode.set(mode)
        enable_pairing_widgets(mode != 2)

    def sourceStateInd(self, state: int):
        dongleStateLabel.config(text = sourceStateStr[state])

    def leAudioStateInd(self, state: int):
        leaStateLabel.config(text=leaStateStr[state])

    def broadcastModeInd(self, state: int):
        public_broadcast_enable_switch_set(state & 2 == 2)
        broadcast_encrypt_switch_set(state & 1 == 1)

    def broadcastNameInd(self, name):
        broadcastName.set(name)
        enable_settings_widgets(True)

flooSmDelegate = FlooSmDelegate()
flooSm = FlooStateMachine(flooSmDelegate)
flooSm.daemon = True
flooSm.start()

# Execute Tkinter
root.mainloop()
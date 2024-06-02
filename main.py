# Import Module
import gettext
import locale
import subprocess
import re
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
import urllib.request
import certifi
import ssl

appIcon = "FlooCastApp.ico"
appGif = "FlooCastApp.gif"
appTitle = "FlooCast"
appLogoPng = "FlooCastHeader.png"

codecStr = ['None',
            'CVSD',
            'mSBC/WBS',
            'SBC',
            'aptX',
            'aptX HD',
            'aptX Adaptive',
            'LC3',
            'aptX Adaptive',
            'aptX Lite',
            'aptX Lossless',
            'aptX Voice']

if platform.system().lower().startswith('darwin'):
    preferLanguages = subprocess.run(['defaults', 'read', '-g', 'AppleLanguages'], stdout=subprocess.PIPE)
    preferLanguage = preferLanguages.stdout.decode('utf-8').split('\n')[1]
    lanSearch = re.search(r'(?<=\")\w+', preferLanguage.lstrip())
    lan = lanSearch.group(0)
else:
    userLocale = locale.getdefaultlocale()
    lan = userLocale[0].split('_')[0]

# Set the local directory
app_path = os.path.abspath(os.path.dirname(sys.argv[0]))
localedir = app_path + os.sep + 'locales'
# Set up your magic function
translate = gettext.translation("messages", localedir, languages=[lan], fallback=True)
translate.install()
_ = translate.gettext

sourceStateStr = [_("Initializing"),
                  _("Idle"),
                  _("Pairing"),
                  _("Connecting"),
                  _("Connected"),
                  _("Audio starting"),
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

# create root window
root = tk.Tk()

# root window title and dimension
root.title(appTitle)
if platform.system().lower().startswith('win'):
    root.iconbitmap(app_path + os.sep + appIcon)
else:
    img_icon = tk.PhotoImage(file=app_path + os.sep + appGif)
    root.tk.call('wm', 'iconphoto', root._w, img_icon)
# Set geometry (widthxheight)
root.geometry('900x480')

root.rowconfigure(0, weight=1)
root.rowconfigure(1, weight=0)
root.columnconfigure(0, weight=1)

mainFrame = tk.Frame(root)  # , relief=tk.RAISED
mainFrame.grid(column=0, row=0, sticky="nsew")

# statusBar
statusBar = tk.Label(root, text=_("Initializing"), bd=1, relief=tk.SUNKEN, anchor=tk.W)
statusBar.grid(column=0, row=1, sticky="ew")


def update_status_bar(info: str):
    global statusBar
    statusBar.config(text=info)


# Define On/Off Images
on = tk.PhotoImage(file=app_path + os.sep + 'onS.png')
off = tk.PhotoImage(file=app_path + os.sep + 'offS.png')

mainFrame.rowconfigure(0, weight=0)
mainFrame.rowconfigure(1, weight=0)
mainFrame.rowconfigure(2, weight=1)
# mainFrame.grid_columnconfigure(0, weight=1)
mainFrame.columnconfigure(0, weight=1)
mainFrame.columnconfigure(1, weight=0)
# Setup contains LE Broadcast and Paired Devices
audioModePanel = ttk.LabelFrame(mainFrame, text=_('Audio Mode'))
audioModePanel.grid(column=0, row=0, padx=2, sticky='nsew')
leBroadcastPanel = ttk.LabelFrame(mainFrame, text=_('LE Broadcast'))
leBroadcastPanel.grid(column=0, row=1, padx=2, sticky='nsew')
pairedDevicesPanel = ttk.LabelFrame(mainFrame, text=_('Most Recently Used Devices'))
pairedDevicesPanel.grid(column=0, row=2, padx=2, sticky='nsew')
# Window panel
windowPanel = ttk.LabelFrame(mainFrame, text=_('Window'))
windowPanel.grid(column=1, row=0, padx=2, sticky='nsew')
# About panel
aboutPanel = ttk.LabelFrame(mainFrame, text=_('Settings'))
aboutPanel.grid(column=1, row=1, padx=2, rowspan=2, sticky='nsew')

# Audio mode panel
for i in range(0, 3):
    if i == 1:
        audioModePanel.rowconfigure(i, weight=1)
    else:
        audioModePanel.rowconfigure(i, weight=0)
for i in range(0, 4):
    if i > 2:
        audioModePanel.columnconfigure(i, weight=2)
    else:
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
dongleStateLabel = tk.Label(dongleStatePanel, text=_("Initializing"))
dongleStateLabel.place(relx=.5, rely=.5, anchor=tk.CENTER)
leaStatePanel = ttk.LabelFrame(audioModePanel, text=_('LE Audio State'))
leaStatePanel.grid(column=1, row=1, columnspan=1, padx=4, pady=4, sticky='nsew')
leaStateLabel = tk.Label(leaStatePanel, text=_("Disconnected"))
leaStateLabel.place(relx=.5, rely=.5, anchor=tk.CENTER)
codecInUsePanel = ttk.LabelFrame(audioModePanel, text=_('Codec in Use'))
codecInUsePanel.grid(column=2, row=1, columnspan=2, padx=4, pady=4, sticky='nsew')
codecInUseLabel = tk.Label(codecInUsePanel, text=codecStr[0])
codecInUseLabel.place(relx=.5, rely=.5, anchor=tk.CENTER)

preferLeaEnableLabel = tk.Label(audioModePanel, text=_("Prefer using LE audio for dual-mode devices"))
preferLeaEnableLabel.grid(column=0, row=2, columnspan=2, sticky='w')
preferLeaEnable = None


def prefer_lea_enable_switch_set(enable):
    global preferLeaEnable
    preferLeaEnable = enable
    preferLeaEnableButton.config(image=on if preferLeaEnable else off)
    flooSm.setPreferLea(enable)


# Broadcast enable switch function
def prefer_lea_enable_switch():
    global preferLeaEnable
    prefer_lea_enable_switch_set(not preferLeaEnable)


preferLeaEnableButton = tk.Button(audioModePanel, image=off, bd=0, command=prefer_lea_enable_switch)
preferLeaEnableButton.grid(column=3, row=2, sticky='e')

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
    publicBroadcastEnableButton.config(image=on if publicBroadcastEnable else off)
    flooSm.setPublicBroadcast(enable)


# Broadcast enable switch function
def public_broadcast_enable_switch():
    global publicBroadcastEnable
    public_broadcast_enable_switch_set(not publicBroadcastEnable)


publicBroadcastEnableButton = tk.Button(leBroadcastPanel, image=off, bd=0, command=public_broadcast_enable_switch)
publicBroadcastEnableButton.grid(column=2, row=0, sticky='e')

broadcastQualityLabel = tk.Label(leBroadcastPanel, text=_("Broadcast high-quality music, otherwise, voice"))
broadcastQualityLabel.grid(column=0, row=1, columnspan=2, sticky='w')
broadcastHighQualityEnable = None


def broadcast_high_quality_switch_set(enable):
    global broadcastHighQualityEnable
    broadcastHighQualityEnable = enable
    broadcastHighQualityEnableButton.config(image=on if broadcastHighQualityEnable else off)
    flooSm.setBroadcastHighQuality(enable)


# Broadcast high quality enable switch function
def broadcast_high_quality_enable_switch():
    global broadcastHighQualityEnable
    broadcast_high_quality_switch_set(not broadcastHighQualityEnable)


broadcastHighQualityEnableButton = tk.Button(leBroadcastPanel, image=off, bd=0,
                                             command=broadcast_high_quality_enable_switch)
broadcastHighQualityEnableButton.grid(column=2, row=1, sticky='e')

broadcastEncryptEnableLabel = tk.Label(leBroadcastPanel, text=_("Encrypt broadcast; please set a key first"))
broadcastEncryptEnableLabel.grid(column=0, row=2, columnspan=2, sticky='w')
broadcastEncryptEnable = None


def broadcast_encrypt_switch_set(enable):
    global broadcastEncryptEnable
    broadcastEncryptEnable = enable
    broadcastEncryptEnableButton.config(image=on if broadcastEncryptEnable else off)
    flooSm.setBroadcastEncrypt(enable)


# Broadcast encrypt enable switch function
def broadcast_encrypt_enable_switch():
    global broadcastEncryptEnable
    broadcast_encrypt_switch_set(not broadcastEncryptEnable)


broadcastEncryptEnableButton = tk.Button(leBroadcastPanel, image=off, bd=0, command=broadcast_encrypt_enable_switch)
broadcastEncryptEnableButton.grid(column=2, row=2, sticky='e')

broadcastNameLabel = tk.Label(leBroadcastPanel, text=_("Broadcast Name, maximum 30 characters"))
broadcastNameLabel.grid(column=0, row=3, sticky='w')
broadcastName = tk.StringVar()


# Broadcase name entry function
def broadcast_name_entry(name: str):
    bytes = name.encode('utf-8')
    if len(bytes) > 0 and len(bytes) < 31:
        flooSm.setBroadcastName(name)
    else:
        broadcastNameEntry.put_placeholder()


broadcastNameEntry = EntryWithPlaceholder(leBroadcastPanel, textvariable=broadcastName,
                                          placeholder=_("Input a new name of no more than 30 characters then press <ENTER>"),
                                          edit_end_proc=broadcast_name_entry)
broadcastNameEntry.grid(column=1, row=3, columnspan=2, padx=4, sticky='we')

broadcastKeyLabel = tk.Label(leBroadcastPanel, text=_("Broadcast Key, maximum 16 characters"))
broadcastKeyLabel.grid(column=0, row=4, sticky='w')
broadcastKey = tk.StringVar()


# Broadcase key entry function
def broadcast_key_entry(key: str):
    bytes = key.encode('utf-8')
    if len(bytes) > 0 and len(bytes) < 17:
        flooSm.setBroadcastKey(key)
    else:
        broadcastNameEntry.put_placeholder()


broadcastKeyEntry = EntryWithPlaceholder(leBroadcastPanel, textvariable=broadcastKey,
                                         placeholder=_(
                                             "Input a new key then press <ENTER>"),
                                         edit_end_proc=broadcast_key_entry)
broadcastKeyEntry.grid(column=1, row=4, columnspan=2, padx=4, sticky='we')


# New pairing button function
def button_new_pairing():
    flooSm.setNewPairing()


pairedDevicesPanel.columnconfigure(0, weight=0)
pairedDevicesPanel.columnconfigure(1, weight=1)
pairedDevicesPanel.columnconfigure(2, weight=0)
pairedDevicesPanel.rowconfigure(0, weight=0)
pairedDevicesPanel.rowconfigure(1, weight=1)

# newPairFrame = tk.Frame(pairedDevicesPanel)
# newPairFrame.grid(column=0, row=0, padx=4, sticky='w')
newPairingButton = tk.Button(pairedDevicesPanel, text='+', relief="groove", command=button_new_pairing)
newPairingButton.grid(column=0, row=0, padx=4, sticky='we')
# newPairingButton.pack(side = tk.LEFT)
newPairingLabel = tk.Label(pairedDevicesPanel, text=_("Add device"))
newPairingLabel.grid(column=1, row=0, padx=4, sticky='w')


# newPairingLabel.pack(side = tk.LEFT)

# Clear all paired device function
def button_clear_all():
    flooSm.clearAllPairedDevices()


class PopMenuListbox(tk.Listbox):

    def __init__(self, parent, *args, **kwargs):
        tk.Listbox.__init__(self, parent, *args, **kwargs)
        self.popup_menu = tk.Menu(self, tearoff=0)
        self.popup_menu.add_command(command=self.connect_disconnect_selected)
        self.popup_menu.add_command(label=_("Delete"), command=self.delete_selected)
        self.bind("<Button-3>", self.popup)  # Button-2 on Aqua

    def popup(self, event):
        try:
            # resolve selected device index
            sel = self.nearest(event.y)
            # set proper menu label based on device status
            self.popup_menu.entryconfig(
                0, label=_("Connect") if sel > 0 or flooSm.sourceState < 4 else _("Disconnect"))
            # forcefully select the device for better UX
            self.selection_clear(0, tk.END)
            self.selection_set(sel, sel)
            # show popup menu
            self.popup_menu.tk_popup(event.x_root, event.y_root, sel)
        finally:
            self.popup_menu.grab_release()

    def delete_selected(self):
        for i in self.curselection()[::-1]:
            flooSm.clearIndexedDevice(i)

    def connect_disconnect_selected(self):
        for i in self.curselection()[::-1]:
            flooSm.toggleConnection(i)
        # self.selection_set(0, 'end')


clearAllButton = tk.Button(pairedDevicesPanel, text=_("Clear All"), relief="groove", command=button_clear_all)
clearAllButton.grid(column=2, row=0, padx=4, sticky='we')
pairedDeviceFrame = tk.Frame(pairedDevicesPanel)
pairedDeviceFrame.grid(column=0, row=1, columnspan=3, padx=4, sticky='nswe')
pairedDeviceListbox = PopMenuListbox(pairedDeviceFrame)  # selectmode=tk.MULTIPLE
pairedDeviceListbox.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
scrollbar = tk.Scrollbar(pairedDeviceFrame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
pairedDeviceListbox.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=pairedDeviceListbox.yview)
currentPairedDeviceList = []


# pairedDeviceListbox = tk.Listbox(pairedDeviceFrame, )
# pairedDeviceListbox.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
# scrollbar = tk.Scrollbar(pairedDeviceFrame)
# scrollbar.pack(side = tk.RIGHT, fill=tk.Y)
# pairedDeviceListbox.config(yscrollcommand = scrollbar.set)
# scrollbar.config(command = pairedDeviceListbox.yview)

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
    image = Image.open(app_path + os.sep + appIcon)
    menu = (TrayMenuItem(_('Quit'), quit_window), TrayMenuItem(_('Show Window'), show_window))
    icon = pystray.Icon(appTitle, image, _("FlooGoo Bluetooth Audio Source"), menu)  # "FlooGoo Bluetooth Audio Source"
    icon.run()
    windowIcon = icon


windowIcon = None
root.protocol('WM_DELETE_WINDOW', hide_window)
windowPanel.columnconfigure(0, weight=1)
windowPanel.columnconfigure(1, weight=1)
minimizeButton = tk.Button(windowPanel, text=_("Minimize to System Tray"), command=hide_window)
minimizeButton.grid(column=0, row=0, columnspan=2, padx=(10, 10), pady=(15, 15), sticky='ew')
quitButton = tk.Button(windowPanel, text=_("Quit App"), command=quit_all)
quitButton.grid(column=0, row=1, columnspan=2, padx=(10, 10), pady=(0, 15), sticky='ew')


# aboutPanel
def url_callback(url):
    webbrowser.open_new(url)


aboutPanel.rowconfigure(0, weight=0)
aboutPanel.rowconfigure(1, weight=0)
aboutPanel.rowconfigure(2, weight=1)
aboutPanel.rowconfigure(3, weight=1)

ledEnableLabel = tk.Label(aboutPanel, text=_("LED"))
ledEnableLabel.grid(column=0, row=0, sticky='w')
ledEnable = None


def led_enable_switch_set(enable):
    global ledEnable
    ledEnable = enable
    ledEnableButton.config(image=on if ledEnable else off)
    flooSm.enableLed(enable)


# Broadcast enable switch function
def led_enable_switch():
    global ledEnable
    led_enable_switch_set(not ledEnable)


ledEnableButton = tk.Button(aboutPanel, image=off, bd=0, command=led_enable_switch)
ledEnableButton.grid(column=1, row=0, sticky='e')

aptxLosslessEnableLabel = tk.Label(aboutPanel, text="aptX\u2122 Lossless")
aptxLosslessEnableLabel.grid(column=0, row=1, sticky='w')
aptxLosslessEnable = None


def aptxLossless_enable_switch_set(enable):
    global aptxLosslessEnable
    aptxLosslessEnable = enable
    aptxLosslessEnableButton.config(image=on if aptxLosslessEnable else off)
    flooSm.enableAptxLossless(enable)


# Broadcast enable switch function
def aptxLossless_enable_switch():
    global aptxLosslessEnable
    aptxLossless_enable_switch_set(not aptxLosslessEnable)


aptxLosslessEnableButton = tk.Button(aboutPanel, image=off, bd=0, command=aptxLossless_enable_switch)
aptxLosslessEnableButton.grid(column=1, row=1, sticky='e')

resetExplanationLabel = tk.Message(aboutPanel,
                                   text=_("Disconnect and reconnect the dongle to activate configuration changes, " \
                                          "after which it will function independently without the app."),
                                   aspect=400)
resetExplanationLabel.grid(column=0, row=3, columnspan=2, padx=(0, 0), sticky='ewns')

aboutFrame = tk.Frame(aboutPanel)
aboutFrame.grid(row=2, column=0, columnspan=2)
logoFrame = tk.Frame(aboutFrame, relief=tk.RAISED)
logoFrame.pack(pady=4)
logo = tk.Canvas(logoFrame, width=230, height=64)
img = tk.PhotoImage(file=app_path + os.sep + appLogoPng)
logo.create_image(0, 0, anchor=tk.NW, image=img)
logo.pack()
copyRightInfo = tk.Label(aboutFrame, text="Copyright© 2023~2024 Flairmesh Technologies.")
copyRightInfo.pack()
thirdPartyLink = tk.Label(aboutFrame, text=_("Third-Party Software Licenses"), fg="blue", cursor="hand2")
thirdPartyLink.pack()
thirdPartyLink.bind("<Button-1>", lambda e: url_callback("https://www.flairmesh.com/support/third_lic.html"))
supportLink = tk.Label(aboutFrame, text=_("Support Link"), fg="blue", cursor="hand2")
supportLink.pack()
supportLink.bind("<Button-1>", lambda e: url_callback("https://www.flairmesh.com/Dongle/FMA120.html"))
versionInfo = tk.Label(aboutFrame, text=_("Version") + "1.0.8")
versionInfo.pack()

dfuUndergoing = False
dfuInfo = tk.Label(aboutFrame, text="")
dfuInfoDefaultColor = dfuInfo.cget('foreground')
dfuInfoBind = False
firmwareVersion = ""
variant = ""
a2dpSink = False


def update_dfu_info(state: int):
    global dfuUndergoing
    global firmwareVersion
    global dfuInfoBind

    if dfuInfoBind:
        dfuInfo.unbind("<Button-1>", dfuInfoBind)
        dfuInfoBind = False
        dfuInfo.config(fg=dfuInfoDefaultColor, cursor='')
    #print(state)
    if state == FlooDfuThread.DFU_STATE_DONE:
        dfuInfo.config(text=_("Firmware") + " " + firmwareVersion)
        minimizeButton.config(state=tk.NORMAL)
        quitButton.config(state=tk.NORMAL)
        dfuButton.config(state=tk.NORMAL)
        dfuUndergoing = False
    elif state > FlooDfuThread.DFU_STATE_DONE:
        dfuInfo.config(text=_("Upgrade error"))
        minimizeButton.config(state=tk.NORMAL)
        quitButton.config(state=tk.NORMAL)
        # dfuButton.config(state=tk.NORMAL)
        dfuUndergoing = True
    else:
        dfuInfo.config(text=_("Upgrade progress") + (" %d" % state) + "%")
        if not dfuUndergoing:
            dfuInfo.pack()
            minimizeButton.config(state=tk.DISABLED)
            quitButton.config(state=tk.DISABLED)
            dfuButton.config(state=tk.DISABLED)
            dfuUndergoing = True


def button_dfu():
    filename = fd.askopenfilename(filetypes=[("Binary files", ".bin")])
    if filename:
        os.chdir(app_path)
        fileBasename = os.path.splitext(filename)[0]
        if not re.search(r'\d+$', fileBasename):
            fileBasename = fileBasename[:-1]
        fileBasename += variant
        filename = fileBasename + ".bin"
        print(filename)
        if os.path.isfile(filename):
            dfuThread = FlooDfuThread([app_path, filename], update_dfu_info)
            dfuThread.start()


if platform.system().lower().startswith('win'):
    dfuButton = tk.Button(aboutFrame, text=_('Device Firmware Upgrade'), relief="groove", command=button_dfu)
    dfuButton.pack()


def enable_settings_widgets(enable: bool):
    if enable:
        if a2dpSink:
            highQualityRadioButton.config(state=tk.DISABLED)
            gamingModeRadioButton.config(state=tk.DISABLED)
            preferLeaEnableButton.config(state=tk.DISABLED)
        else:
            highQualityRadioButton.config(state=tk.NORMAL)
            gamingModeRadioButton.config(state=tk.NORMAL)
            preferLeaEnableButton.config(state=tk.NORMAL)
        broadcastRadioButton.config(state=tk.NORMAL)
        publicBroadcastEnableButton.config(state=tk.NORMAL)
        broadcastHighQualityEnableButton.config(state=tk.NORMAL)
        broadcastEncryptEnableButton.config(state=tk.NORMAL)
        broadcastNameEntry.config(state=tk.NORMAL)
        broadcastKeyEntry.config(state=tk.NORMAL)
        ledEnableButton.config(state=tk.NORMAL)
        aptxLosslessEnableButton.config(state=tk.NORMAL)
        if platform.system().lower().startswith('win'):
            dfuButton.config(state=tk.DISABLED if dfuUndergoing else tk.NORMAL)
    else:
        highQualityRadioButton.config(state=tk.DISABLED)
        gamingModeRadioButton.config(state=tk.DISABLED)
        broadcastRadioButton.config(state=tk.DISABLED)
        preferLeaEnableButton.config(state=tk.DISABLED)
        publicBroadcastEnableButton.config(state=tk.DISABLED)
        broadcastHighQualityEnableButton.config(state=tk.DISABLED)
        broadcastEncryptEnableButton.config(state=tk.DISABLED)
        broadcastNameEntry.config(state=tk.DISABLED)
        broadcastKeyEntry.config(state=tk.DISABLED)
        ledEnableButton.config(state=tk.DISABLED)
        aptxLosslessEnableButton.config(state=tk.DISABLED)
        if platform.system().lower().startswith('win'):
            dfuButton.config(state=tk.DISABLED)


enable_settings_widgets(False)


# All GUI object initialized, start FlooStateMachine
class FlooSmDelegate(FlooStateMachineDelegate):
    def deviceDetected(self, flag: bool, port: str, version : str = None):
        global currentPairedDeviceList
        global firmwareVersion
        global variant
        global a2dpSink
        global dfuInfoBind

        if flag:
            update_status_bar(_("Use FlooGoo dongle on ") + " " + port)
            variant = "" if re.search(r'\d+$', version) else version[-1]
            a2dpSink = True if version.startswith("AS") else False
            firmwareVersion = version if variant == "" else version[:-1]
            # firmwareVersion = firmwareVersion[2:] if a2dpSink else firmwareVersion
            if a2dpSink:
                latest = urllib.request.urlopen("https://www.flairmesh.com/Dongle/FMA120/latest_as",
                                                context=ssl.create_default_context(cafile=certifi.where())).read()
            else:
                latest = urllib.request.urlopen("https://www.flairmesh.com/Dongle/FMA120/latest",
                                                context=ssl.create_default_context(cafile=certifi.where())).read()
            latest = latest.decode("utf-8").rstrip()
            if not dfuUndergoing:
                if latest > firmwareVersion:
                    dfuInfo.config(text=(_("New Firmware is available") + " " + firmwareVersion + " -> " + latest),
                                   fg="blue",cursor="hand2")
                    newFirmwareUrl = "https://www.flairmesh.com/support/FMA120_" + latest +".zip"
                    dfuInfoBind = dfuInfo.bind("<Button-1>",lambda e: url_callback(newFirmwareUrl))
                else:
                    if dfuInfoBind:
                        dfuInfo.unbind("<Button-1>",dfuInfoBind)
                        dfuInfoBind = False
                        dfuInfo.config(fg=dfuInfoDefaultColor,cursor='')
                    dfuInfo.config(text=_("Firmware") + " " + firmwareVersion)
            dfuInfo.pack()
        else:
            update_status_bar(_("Please insert your FlooGoo dongle"))
            enable_settings_widgets(flag)
            enable_pairing_widgets(False)
            pairedDeviceListbox.delete(0, tk.END)
            dfuInfo.pack_forget()

    def audioModeInd(self, mode: int):
        audioMode.set(mode)
        if a2dpSink:
            enable_pairing_widgets(True)
        else:
            enable_pairing_widgets(mode != 2)

    def sourceStateInd(self, state: int):
        dongleStateLabel.config(text=sourceStateStr[state])
        # if state < 4:
        #    codecInUseLabel.config(text=codecStr[0])

    def leAudioStateInd(self, state: int):
        leaStateLabel.config(text=leaStateStr[state])

    def preferLeaInd(self, state: int):
        prefer_lea_enable_switch_set(state == 1)

    def broadcastModeInd(self, state: int):
        broadcast_high_quality_switch_set(state & 4 == 4)
        public_broadcast_enable_switch_set(state & 2 == 2)
        broadcast_encrypt_switch_set(state & 1 == 1)

    def broadcastNameInd(self, name):
        broadcastName.set(name)
        enable_settings_widgets(True)

    def pairedDevicesUpdateInd(self, pairedDevices):
        global currentPairedDeviceList
        print("update paired list len %d" % len(pairedDevices))
        pairedDeviceListbox.delete(0, tk.END)
        i = 0
        while i < len(pairedDevices):
            pairedDeviceListbox.insert(tk.END, pairedDevices[i])
            i = i + 1

    def audioCodecInUseInd(self, codec, rssi, rate):
        codecInUseLabel.config(text=codecStr[codec] if codec < len(codecStr) else _("Unknown"))
        if (codec == 6 or codec == 10) and rssi != 0:
            codecInUseLabel.config(text=codecStr[codec]  + " @ " + str(rate) + "Kbps "
                                        + _("RSSI") +" -" + str(0x100 - rssi) + "dBm")
        else:
            codecInUseLabel.config(text=codecStr[codec] if codec < len(codecStr) else _("Unknown"))

    def ledEnabledInd(self, enabled):
        led_enable_switch_set(enabled)

    def aptxLosslessEnabledInd(self, enabled):
        aptxLossless_enable_switch_set(enabled)


flooSmDelegate = FlooSmDelegate()
flooSm = FlooStateMachine(flooSmDelegate)
flooSm.daemon = True
flooSm.start()

# Execute Tkinter
root.mainloop()

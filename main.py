# Import Module
import os, sys, platform
import locale
import tkinter as tk
from tkinter import ttk
from pystray import MenuItem as TrayMenuItem
import pystray
from PIL import Image
import gettext
import webbrowser
# from FlooTransceiver import FlooTransceiver

appIcon = "FlooCastApp.ico"
appGif = "FlooPasteApp.gif"
appTitle = "FlooCast"
appIconText = "FlooGoo Bluetooth Audio Source"
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
root.geometry('600x400')

mainFrame = tk.Frame(root, relief=tk.RAISED)
mainFrame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# statusbar.grid(column = 0, row = 2)
statusbar = tk.Label(root, text=_("Initializing"), bd=1, relief=tk.SUNKEN, anchor=tk.W)
statusbar.pack(side=tk.BOTTOM, fill=tk.X)

# Define On/Off Images
on = tk.PhotoImage(file=app_path+os.sep+'onS.png')
off = tk.PhotoImage(file=app_path+os.sep+'offS.png')

mainFrame.rowconfigure(0, weight=0)
mainFrame.rowconfigure(1, weight=1)
# mainFrame.grid_columnconfigure(0, weight=1)
mainFrame.columnconfigure(0, weight=1)
mainFrame.columnconfigure(1, weight=0)
# Setup contains LE Broadcast and Paired Devices
leBroadcastPanel = ttk.LabelFrame(mainFrame, text=_('LE Broadcast'))
leBroadcastPanel.grid(column=0, row=0, sticky='nsew')
pairedDevicesPanel = ttk.LabelFrame(mainFrame, text=_('Paired Devices'))
pairedDevicesPanel.grid(column=0, row=1, sticky='nsew')
# Window panel
windowPanel = ttk.LabelFrame(mainFrame, text=_('Window'))
windowPanel.grid(column=1, row=0, sticky='nsew')
# About panel
aboutPanel = ttk.LabelFrame(mainFrame, text=_('About'))
aboutPanel.grid(column=1, row=1, sticky='nsew')

# LE Broadcast panel
leBroadcastPanel.columnconfigure(0, weight=1)
leBroadcastPanel.columnconfigure(1, weight=1)
leBroadcastPanel.columnconfigure(2, weight=1)

broadcastEnableLabel = tk.Label(leBroadcastPanel, text=_("Broadcast"))
broadcastEnableLabel.grid(column=0, row=0, sticky='w')
leBroadcastEnable = None


# Broadcast enable switch function
def broadcast_enable_switch():
    global leBroadcastEnable
    # Determine is on or off
    if shareToMobile:
        shareToMobileButton.config(image=off)
        shareToMobile = False
    else:
        shareToMobileButton.config(image=on)
        shareToMobile = True
    floo_transceiver.setShareToMobile(shareToMobile)
    flooConfig.setShareToMobile(shareToMobile)


broadcastEnableButton = tk.Button(leBroadcastPanel, image=off, bd=0, command=broadcast_enable_switch)
broadcastEnableButton["state"] = "disabled"
broadcastEnableButton.grid(column=2, row=0, sticky='e')

broadcastNameLabel = tk.Label(leBroadcastPanel, text=_("Broadcast Name"))
broadcastNameLabel.grid(column=0, row=1, sticky='w')
broadcastName = tk.StringVar()

# Broadcase name entry function
def broadcast_name_entry():
    global leBroadcastEnable
    # Determine is on or off
    if shareToMobile:
        shareToMobileButton.config(image=off)
        shareToMobile = False
    else:
        shareToMobileButton.config(image=on)
        shareToMobile = True
    floo_transceiver.setShareToMobile(shareToMobile)
    flooConfig.setShareToMobile(shareToMobile)


broadcastNameEntry = tk.Entry(leBroadcastPanel, textvariable=broadcastName,
                              validate="focusout", validatecommand=broadcast_name_entry)
broadcastNameEntry["state"] = "disabled"
broadcastNameEntry.grid(column=1, row=1, columnspan=2, padx=4, sticky='we')
broadcastKeyLabel = tk.Label(leBroadcastPanel, text=_("Broadcast Key"))
broadcastKeyLabel.grid(column=0, row=2, sticky='w')
broadcastKey = tk.StringVar()

# Broadcase key entry function
def broadcast_key_entry():
    global leBroadcastEnable
    # Determine is on or off
    if shareToMobile:
        shareToMobileButton.config(image=off)
        shareToMobile = False
    else:
        shareToMobileButton.config(image=on)
        shareToMobile = True
    floo_transceiver.setShareToMobile(shareToMobile)
    flooConfig.setShareToMobile(shareToMobile)


broadcastKeyEntry = tk.Entry(leBroadcastPanel, textvariable=broadcastKey,
                              validate="focusout", validatecommand=broadcast_key_entry)
broadcastKeyEntry["state"] = "disabled"
broadcastKeyEntry.grid(column=1, row=2, columnspan=2, padx=4, sticky='we')

# New pairing button function
def button_new_pairing():
    global leBroadcastEnable
    # Determine is on or off
    if shareToMobile:
        shareToMobileButton.config(image=off)
        shareToMobile = False
    else:
        shareToMobileButton.config(image=on)
        shareToMobile = True
    floo_transceiver.setShareToMobile(shareToMobile)
    flooConfig.setShareToMobile(shareToMobile)


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
    global leBroadcastEnable
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


# Initialize FlooTransceiver


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
    icon.stop()
    root.after(0, root.deiconify())
    windowIcon = None


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
    icon = pystray.Icon(appTitle, image, _(appIconText), menu)
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


# all widgets will be here
# Execute Tkinter
root.mainloop()
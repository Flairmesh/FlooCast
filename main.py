# !/usr/bin/env python
import gettext
import locale
import subprocess
import re
import os
import platform
import sys
import wx
import wx.lib.agw.hyperlink as hl
from wx.adv import TaskBarIcon as TaskBarIcon
from FlooStateMachine import FlooStateMachine
from FlooStateMachineDelegate import FlooStateMachineDelegate
from FlooDfuThread import FlooDfuThread
from PIL import Image
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
            'aptX\u2122',
            'aptX\u2122 HD',
            'aptX\u2122 Adaptive',
            'LC3',
            'aptX\u2122 Adaptive',
            'aptX\u2122 Lite',
            'aptX\u2122 Lossless',
            'aptX\u2122 Voice']

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
app = wx.App(False)

appFrame = wx.Frame(None, wx.ID_ANY, "FlooCast", size=wx.Size(930, 560))
appFrame.SetIcon(wx.Icon(app_path + os.sep + appIcon))

statusBar = appFrame.CreateStatusBar(name=_("Status Bar"))
statusBar.SetStatusText(_("Initializing"))


# Update the status bar
def update_status_bar(info: str):
    global statusBar
    statusBar.SetStatusText(info)


# Define On/Off Images
on = wx.Bitmap(app_path + os.sep + 'onS.png', )
off = wx.Bitmap(app_path + os.sep + 'offS.png')

appPanel = wx.Panel(appFrame)
appSizer = wx.FlexGridSizer(2, 2, vgap=2, hgap=4)

# Audio mode panel
audioMode = None
audioModeSb = wx.StaticBox(appPanel, wx.ID_ANY, _('Audio Mode'))
audioModeSbSizer = wx.StaticBoxSizer(audioModeSb, wx.VERTICAL)

audioModeUpperPanel = wx.Panel(audioModeSb)
audioModeUpperPanelSizer = wx.FlexGridSizer(2, 3, (0, 0))
audioModeHighQualityRadioButton = wx.RadioButton(audioModeUpperPanel, label=_('High Quality (one-to-one)'),
                                                 style=wx.RB_GROUP)
audioModeGamingRadioButton = wx.RadioButton(audioModeUpperPanel, label=_('Gaming (one-to-one)'))
audioModeBroadcastRadioButton = wx.RadioButton(audioModeUpperPanel, label=_('Broadcast'))


def audio_mode_sel_set(mode):
    if mode == 0:
        settingsPanelSizer.Show(aptxLosslessCheckBox)
        settingsPanelSizer.Show(aptxLosslessEnableButton)
        settingsPanelSizer.Hide(gattClientWithBroadcastCheckBox)
        settingsPanelSizer.Hide(gattClientWithBroadcastEnableButton)
    elif mode == 1:
        settingsPanelSizer.Hide(aptxLosslessCheckBox)
        settingsPanelSizer.Hide(aptxLosslessEnableButton)
        settingsPanelSizer.Hide(gattClientWithBroadcastCheckBox)
        settingsPanelSizer.Hide(gattClientWithBroadcastEnableButton)
    elif mode == 2:
        settingsPanelSizer.Hide(aptxLosslessCheckBox)
        settingsPanelSizer.Hide(aptxLosslessEnableButton)
        settingsPanelSizer.Show(gattClientWithBroadcastCheckBox)
        settingsPanelSizer.Show(gattClientWithBroadcastEnableButton)
    aboutSbSizer.Layout()


def audio_mode_sel(event):
    selectedLabel = (event.GetEventObject().GetLabel())
    if selectedLabel == audioModeHighQualityRadioButton.GetLabel():
        mode = 0
    elif selectedLabel == audioModeGamingRadioButton.GetLabel():
        mode = 1
    else:
        mode = 2
    audio_mode_sel_set(mode)
    settingsPanelSizer.Layout()
    flooSm.setAudioMode(mode)


audioModeUpperPanel.Bind(wx.EVT_RADIOBUTTON, audio_mode_sel)

dongleStateSb = wx.StaticBox(audioModeUpperPanel, wx.ID_ANY, _('Dongle State'))
dongleStateSbSizer = wx.StaticBoxSizer(dongleStateSb, wx.VERTICAL)
dongleStateText = wx.StaticText(dongleStateSb, wx.ID_ANY, _("Initializing"))
dongleStateSbSizer.Add(dongleStateText, flag=wx.ALIGN_CENTER_HORIZONTAL | wx.TOP | wx.BOTTOM, border=4)

leaStateSb = wx.StaticBox(audioModeUpperPanel, wx.ID_ANY, _('LE Audio State'))
leaStateSbSizer = wx.StaticBoxSizer(leaStateSb, wx.VERTICAL)
leaStateText = wx.StaticText(leaStateSb, wx.ID_ANY, _("Disconnected"))
leaStateSbSizer.Add(leaStateText, flag=wx.ALIGN_CENTER_HORIZONTAL | wx.TOP | wx.BOTTOM, border=4)

codecInUseSb = wx.StaticBox(audioModeUpperPanel, wx.ID_ANY, _('Codec in Use'))
codecInUseSbSizer = wx.StaticBoxSizer(codecInUseSb, wx.VERTICAL)
codecInUseText = wx.StaticText(codecInUseSb, wx.ID_ANY, codecStr[0])
codecInUseSbSizer.Add(codecInUseText, flag=wx.ALIGN_CENTER_HORIZONTAL | wx.TOP | wx.BOTTOM, border=4)

audioModeUpperPanelSizer.Add(audioModeHighQualityRadioButton, flag=wx.EXPAND | wx.ALL, border=4)
audioModeUpperPanelSizer.Add(audioModeGamingRadioButton, flag=wx.EXPAND | wx.ALL, border=4)
audioModeUpperPanelSizer.Add(audioModeBroadcastRadioButton, flag=wx.EXPAND | wx.ALL, border=4)
audioModeUpperPanelSizer.Add(dongleStateSbSizer, flag=wx.EXPAND | wx.ALL, border=4)
audioModeUpperPanelSizer.Add(leaStateSbSizer, flag=wx.EXPAND | wx.ALL, border=4)
audioModeUpperPanelSizer.Add(codecInUseSbSizer, flag=wx.EXPAND | wx.ALL, border=4)
audioModeUpperPanelSizer.AddGrowableRow(0, 1)
audioModeUpperPanelSizer.AddGrowableRow(1, 1)
audioModeUpperPanelSizer.AddGrowableCol(0, 1)
audioModeUpperPanelSizer.AddGrowableCol(1, 1)
audioModeUpperPanelSizer.AddGrowableCol(2, 2)
audioModeUpperPanel.SetSizer(audioModeUpperPanelSizer)

audioModeLowerPanel = wx.Panel(audioModeSb)
audioModeLowerPanelSizer = wx.BoxSizer(wx.HORIZONTAL)

preferLeaEnable = None


def prefer_lea_enable_switch_set(enable):
    global preferLeaEnable
    preferLeaEnable = enable
    preferLeaCheckBox.SetValue(enable)
    preferLeButton.SetBitmap(on if preferLeaEnable else off)
    preferLeButton.SetToolTip(
        _('Toggle switch for') + ' ' + _('Prefer using LE audio for dual-mode devices') + ' ' + (_(
            'On') if preferLeaEnable else _(
            'Off')))
    flooSm.setPreferLea(enable)
    newPairingButton.Enable(False if preferLeaEnable and pairedDeviceListbox.GetCount() > 0 else True)


def prefer_lea_enable_switch(event):
    prefer_lea_enable_switch_set(not preferLeaEnable)


preferLeaCheckBox = wx.CheckBox(audioModeLowerPanel, wx.ID_ANY,
                                label=_('Prefer using LE audio for dual-mode devices') + ' (' + _(
                                    'Must be disabled for') + ' ' + 'aptX\u2122 Lossless' + ')')
preferLeButton = wx.Button(audioModeLowerPanel, wx.ID_ANY, style=wx.NO_BORDER | wx.MINIMIZE)
preferLeButton.SetToolTip(
    _('Toggle switch for') + ' ' + _('Prefer using LE audio for dual-mode devices') + ' ' + _('Off'))
preferLeButton.SetBitmap(off)
audioModeLowerPanel.Bind(wx.EVT_CHECKBOX, prefer_lea_enable_switch, preferLeaCheckBox)
preferLeButton.Bind(wx.EVT_BUTTON, prefer_lea_enable_switch)
audioModeLowerPanelSizer.Add(preferLeaCheckBox, flag=wx.EXPAND, proportion=1)
audioModeLowerPanelSizer.Add(preferLeButton, proportion=0)
audioModeLowerPanel.SetSizer(audioModeLowerPanelSizer)

audioModeSbSizer.Add(audioModeUpperPanel, flag=wx.EXPAND)  # , proportion=5
audioModeSbSizer.Add(audioModeLowerPanel, flag=wx.EXPAND)  # , proportion=1


# Window panel
class FlooCastTaskBarIcon(TaskBarIcon):
    def __init__(self, frame):
        TaskBarIcon.__init__(self)

        self.frame = frame
        # file_path = os.path.abspath(os.path.dirname(sys.argv[0]))
        image = Image.open(app_path + os.sep + appIcon)

        self.SetIcon(wx.Icon(app_path + os.sep + appIcon, wx.BITMAP_TYPE_ICO), 'FlooCast')

        # ------------

        self.Bind(wx.EVT_MENU, self.OnTaskBarActivate, id=1)
        self.Bind(wx.EVT_MENU, self.OnTaskBarDeactivate, id=2)
        self.Bind(wx.EVT_MENU, self.OnTaskBarClose, id=3)

    # -----------------------------------------------------------------------

    def CreatePopupMenu(self):
        menu = wx.Menu()
        menu.Append(1, _('Show Window'))
        menu.Append(2, _('Minimize to System Tray'))
        menu.Append(3, _('Quit'))

        return menu

    def OnTaskBarClose(self, event):
        self.frame.Close()

    def OnTaskBarActivate(self, event):
        if not self.frame.IsShown():
            self.frame.Show()

    def OnTaskBarDeactivate(self, event):
        if self.frame.IsShown():
            self.frame.Hide()


def quit_all():
    appFrame.Close()


# Define a function for quit the window
def quit_window(event):
    windowIcon.Destroy()
    appFrame.Destroy()


# Hide the window and show on the system taskbar
def hide_window(event):
    if appFrame.IsShown():
        appFrame.Hide()


windowIcon = FlooCastTaskBarIcon(appFrame)
appFrame.Bind(wx.EVT_ICONIZE, hide_window)
appFrame.Bind(wx.EVT_CLOSE, quit_window)

windowSb = wx.StaticBox(appPanel, wx.ID_ANY, _('Window'))
windowSbSizer = wx.StaticBoxSizer(windowSb, wx.VERTICAL)
minimizeButton = wx.Button(windowSb, label=_('Minimize to System Tray'))
minimizeButton.Bind(wx.EVT_BUTTON, hide_window)
quitButton = wx.Button(windowSb, label=_('Quit App'))
quitButton.Bind(wx.EVT_BUTTON, quit_window)

windowSbSizer.AddStretchSpacer()
windowSbSizer.Add(minimizeButton, proportion=2, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)
windowSbSizer.AddStretchSpacer()
windowSbSizer.Add(quitButton, proportion=2, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)
windowSbSizer.AddStretchSpacer()

# A combined panel for broadcast settings and paired devices
broadcastAndPairedDevicePanel = wx.Panel(appPanel)
broadcastAndPairedDeviceSizer = wx.BoxSizer(wx.VERTICAL)

leBroadcastSb = wx.StaticBox(broadcastAndPairedDevicePanel, wx.ID_ANY,
                             _('LE Broadcast') + " - " + _('Changes Take Effect After Restart'))
leBroadcastSbSizer = wx.StaticBoxSizer(leBroadcastSb, wx.VERTICAL)
leBroadcastSwitchPanel = wx.Panel(leBroadcastSb)
leBroadcastSwitchPanelSizer = wx.FlexGridSizer(3, 2, (0, 0))

publicBroadcastEnable = None


def public_broadcast_enable_switch_set(enable):
    global publicBroadcastEnable
    publicBroadcastEnable = enable
    publicBroadcastCheckBox.SetValue(enable)
    publicBroadcastButton.SetBitmap(on if publicBroadcastEnable else off)
    publicBroadcastButton.SetToolTip(
        _('Toggle switch for') + ' ' + _('Public broadcast') + ' ' + (_('On') if publicBroadcastEnable else _(
            'Off')))
    flooSm.setPublicBroadcast(enable)


# Broadcast enable switch function
def public_broadcast_enable_switch(event):
    public_broadcast_enable_switch_set(not publicBroadcastEnable)


publicBroadcastCheckBox = wx.CheckBox(leBroadcastSwitchPanel, wx.ID_ANY, label=_('Public broadcast') + ' (' + _(
    'Must be enabled for compatibility with') + ' Auracast\u2122)')
publicBroadcastButton = wx.Button(leBroadcastSwitchPanel, wx.ID_ANY, style=wx.NO_BORDER | wx.MINIMIZE)
publicBroadcastButton.SetToolTip(_('Toggle switch for') + ' ' + _('Public broadcast') + ' ' + _('Off'))
publicBroadcastButton.SetBitmap(off)
leBroadcastSwitchPanel.Bind(wx.EVT_CHECKBOX, public_broadcast_enable_switch, publicBroadcastCheckBox)
publicBroadcastButton.Bind(wx.EVT_BUTTON, public_broadcast_enable_switch)

broadcastHighQualityEnable = None


def broadcast_high_quality_switch_set(enable):
    global broadcastHighQualityEnable
    broadcastHighQualityEnable = enable
    broadcastHighQualityCheckBox.SetValue(enable)
    broadcastHighQualityButton.SetBitmap(on if broadcastHighQualityEnable else off)
    publicBroadcastButton.SetToolTip(
        _('Toggle switch for') + ' ' + _('Broadcast high-quality music, otherwise, voice') + ' ' + (_(
            'On') if broadcastHighQualityEnable else _(
            'Off')))
    flooSm.setBroadcastHighQuality(enable)


# Broadcast high quality enable switch function
def broadcast_high_quality_enable_switch(event):
    broadcast_high_quality_switch_set(not broadcastHighQualityEnable)


broadcastHighQualityCheckBox = wx.CheckBox(leBroadcastSwitchPanel, wx.ID_ANY,
                                           label=_('Broadcast high-quality music, otherwise, voice') + ' (' + _(
                                               'Must be disabled for compatibility with') + ' Auracast\u2122)')
broadcastHighQualityButton = wx.Button(leBroadcastSwitchPanel, wx.ID_ANY, style=wx.NO_BORDER | wx.MINIMIZE)
broadcastHighQualityButton.SetToolTip(
    _('Toggle switch for') + ' ' + _('Broadcast high-quality music, otherwise, voice') + ' ' + _('Off'))
broadcastHighQualityButton.SetBitmap(off)
leBroadcastSwitchPanel.Bind(wx.EVT_CHECKBOX, broadcast_high_quality_enable_switch, broadcastHighQualityCheckBox)
broadcastHighQualityButton.Bind(wx.EVT_BUTTON, broadcast_high_quality_enable_switch)

broadcastEncryptEnable = None


def broadcast_encrypt_switch_set(enable):
    global broadcastEncryptEnable
    broadcastEncryptEnable = enable
    broadcastEncryptCheckBox.SetValue(enable)
    broadcastEncryptButton.SetBitmap(on if broadcastEncryptEnable else off)
    broadcastEncryptButton.SetToolTip(
        _('Toggle switch for') + ' ' + _('Encrypt broadcast; please set a key first') + ' ' + (_(
            'On') if broadcastEncryptEnable else _('Off')))
    flooSm.setBroadcastEncrypt(enable)


# Broadcast encrypt enable switch function
def broadcast_encrypt_enable_switch(event):
    broadcast_encrypt_switch_set(not broadcastEncryptEnable)


broadcastEncryptCheckBox = wx.CheckBox(leBroadcastSwitchPanel, wx.ID_ANY,
                                       label=_('Encrypt broadcast; please set a key first'))
broadcastEncryptButton = wx.Button(leBroadcastSwitchPanel, wx.ID_ANY, style=wx.NO_BORDER | wx.MINIMIZE)
broadcastEncryptButton.SetToolTip(
    _('Toggle switch for') + ' ' + _('Encrypt broadcast; please set a key first') + ' ' + _('Off'))
broadcastEncryptButton.SetBitmap(off)
leBroadcastSwitchPanel.Bind(wx.EVT_CHECKBOX, broadcast_encrypt_enable_switch, broadcastEncryptCheckBox)
broadcastEncryptButton.Bind(wx.EVT_BUTTON, broadcast_encrypt_enable_switch)

leBroadcastSwitchPanelSizer.Add(publicBroadcastCheckBox, flag=wx.ALIGN_LEFT)
leBroadcastSwitchPanelSizer.Add(publicBroadcastButton, flag=wx.ALIGN_RIGHT)
leBroadcastSwitchPanelSizer.Add(broadcastHighQualityCheckBox, flag=wx.ALIGN_LEFT)
leBroadcastSwitchPanelSizer.Add(broadcastHighQualityButton, flag=wx.ALIGN_RIGHT)
leBroadcastSwitchPanelSizer.Add(broadcastEncryptCheckBox, flag=wx.ALIGN_LEFT)
leBroadcastSwitchPanelSizer.Add(broadcastEncryptButton, flag=wx.ALIGN_RIGHT)

leBroadcastSwitchPanelSizer.AddGrowableCol(0, 0)
leBroadcastSwitchPanelSizer.AddGrowableCol(1, 1)

leBroadcastEntryPanel = wx.Panel(leBroadcastSb)
leBroadcastEntryPanelSizer = wx.FlexGridSizer(2, 2, (0, 0))


# Broadcast name entry function
def broadcast_name_entry(event):
    name = broadcastNameEntry.GetValue()
    print("new broadcast name", name)
    nameBytes = name.encode('utf-8')
    if 0 < len(nameBytes) < 31:
        flooSm.setBroadcastName(name)
    event.Skip()


broadcastNameLabel = wx.StaticText(leBroadcastEntryPanel, wx.ID_ANY, label=_('Broadcast Name, maximum 30 characters'))
broadcastNameEntry = wx.SearchCtrl(leBroadcastEntryPanel, wx.ID_ANY)
broadcastNameEntry.ShowSearchButton(False)
broadcastNameEntry.SetHint(_("Input a new name of no more than 30 characters then press <ENTER>"))
broadcastNameEntry.SetDescriptiveText(_("Input a new name of no more than 30 characters then press <ENTER>"))
broadcastNameEntry.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, broadcast_name_entry)
broadcastNameEntry.Bind(wx.EVT_KILL_FOCUS, broadcast_name_entry)


# Broadcast key entry function
def broadcast_key_entry(event):
    key = broadcastKeyEntry.GetValue()
    keyBytes = key.encode('utf-8')
    if 0 < len(keyBytes) < 17:
        flooSm.setBroadcastKey(key)
    event.Skip()


broadcastKey = wx.StaticText(leBroadcastEntryPanel, wx.ID_ANY, label=_('Broadcast Key, maximum 16 characters'))
broadcastKeyEntry = wx.SearchCtrl(leBroadcastEntryPanel, wx.ID_ANY, style=wx.TE_PASSWORD)
broadcastKeyEntry.ShowSearchButton(False)
# broadcastKeyEntry.SetHint(_("Input a new key then press <ENTER>"))
broadcastKeyEntry.SetDescriptiveText(_("Input a new key then press <ENTER>"))
broadcastKeyEntry.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, broadcast_key_entry)
broadcastKeyEntry.Bind(wx.EVT_KILL_FOCUS, broadcast_key_entry)

leBroadcastEntryPanelSizer.Add(broadcastNameLabel, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
leBroadcastEntryPanelSizer.Add(broadcastNameEntry, flag=wx.EXPAND | wx.LEFT, border=8)
leBroadcastEntryPanelSizer.Add(broadcastKey, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
leBroadcastEntryPanelSizer.Add(broadcastKeyEntry, flag=wx.EXPAND | wx.LEFT, border=8)

leBroadcastEntryPanelSizer.AddGrowableCol(0, 1)
leBroadcastEntryPanelSizer.AddGrowableCol(1, 1)
leBroadcastEntryPanel.SetSizer(leBroadcastEntryPanelSizer)

leBroadcastSbSizer.Add(leBroadcastSwitchPanel, flag=wx.EXPAND | wx.TOP, border=4)
leBroadcastSbSizer.Add(leBroadcastEntryPanel, flag=wx.EXPAND, border=4)
leBroadcastSwitchPanel.SetSizer(leBroadcastSwitchPanelSizer)

pairedDevicesSb = wx.StaticBox(broadcastAndPairedDevicePanel, wx.ID_ANY, _('Most Recently Used Devices'))
pairedDevicesSbPanelSizer = wx.StaticBoxSizer(pairedDevicesSb, wx.VERTICAL)

pairedDevicesSbButtonPanel = wx.Panel(pairedDevicesSb)
pairedDevicesSbButtonPanelSizer = wx.BoxSizer(wx.HORIZONTAL)


# New pairing button function
def button_new_pairing(event):
    flooSm.setNewPairing()


# Clear all paired device function
def button_clear_all(event):
    flooSm.clearAllPairedDevices()


newPairingButton = wx.Button(pairedDevicesSbButtonPanel, wx.ID_ANY, label=_('Add device'))
clearAllButton = wx.Button(pairedDevicesSbButtonPanel, wx.ID_ANY, label=_('Clear All'))
pairedDevicesSbButtonPanelSizer.Add(newPairingButton, flag=wx.LEFT)
pairedDevicesSbButtonPanelSizer.AddStretchSpacer()
pairedDevicesSbButtonPanelSizer.Add(clearAllButton, flag=wx.RIGHT)
newPairingButton.Bind(wx.EVT_BUTTON, button_new_pairing)
clearAllButton.Bind(wx.EVT_BUTTON, button_clear_all)
pairedDevicesSbButtonPanel.SetSizer(pairedDevicesSbButtonPanelSizer)


class PopMenu(wx.Menu):
    def __init__(self, parent):
        super(PopMenu, self).__init__()
        self.parent = parent
        listBox = parent
        self.index = listBox.GetSelection()
        # menu item Connect/Disconnect
        menuItemConnection = wx.MenuItem(self, wx.ID_ANY, _("Connect") if self.index > 0 or
                                                                          flooSm.sourceState < 4 else _("Disconnect"))
        self.Bind(wx.EVT_MENU, self.connect_disconnect_selected, menuItemConnection)
        self.Append(menuItemConnection)
        # menu item clear
        menuItemDelete = wx.MenuItem(self, wx.ID_ANY, _("Delete"))
        self.Bind(wx.EVT_MENU, self.delete_selected, menuItemDelete)
        self.Append(menuItemDelete)

    def delete_selected(self, e):
        flooSm.clearIndexedDevice(self.index)

    def connect_disconnect_selected(self, e):
        flooSm.toggleConnection(self.index)


def OnContextMenu(Event):
    listBox = Event.GetEventObject()
    listBox.PopupMenu(PopMenu(listBox), listBox.ScreenToClient(Event.GetPosition()))  # wx.GetMousePosition()


pairedDeviceListbox = wx.ListBox(pairedDevicesSb, style=wx.LB_SINGLE | wx.LB_ALWAYS_SB)
pairedDeviceListbox.Bind(wx.EVT_CONTEXT_MENU, OnContextMenu)
currentPairedDeviceList = []

pairedDevicesSbPanelSizer.Add(pairedDevicesSbButtonPanel, proportion=0, flag=wx.EXPAND)
pairedDevicesSbPanelSizer.Add(pairedDeviceListbox, proportion=1, flag=wx.EXPAND)

broadcastAndPairedDeviceSizer.Add(leBroadcastSbSizer, proportion=0, flag=wx.EXPAND)
broadcastAndPairedDeviceSizer.Add(pairedDevicesSbPanelSizer, proportion=1, flag=wx.EXPAND)
broadcastAndPairedDevicePanel.SetSizer(broadcastAndPairedDeviceSizer)

# Settings panel
aboutSb = wx.StaticBox(appPanel, wx.ID_ANY, _('Settings'))
aboutSbSizer = wx.StaticBoxSizer(aboutSb, wx.VERTICAL)
settingsPanel = wx.Panel(aboutSb)
settingsPanelSizer = wx.FlexGridSizer(3, 2, (5, 0))

ledEnable = None


def led_enable_switch_set(enable):
    global ledEnable
    ledEnable = enable
    ledCheckBox.SetValue(enable)
    ledEnableButton.SetBitmap(on if ledEnable else off)
    ledEnableButton.SetToolTip(_('Toggle switch for') + ' ' + _('LED') + ' ' + (_('On') if ledEnable else _('Off')))
    flooSm.enableLed(enable)


# led enable switch function
def led_enable_switch(event):
    led_enable_switch_set(not ledEnable)


ledCheckBox = wx.CheckBox(settingsPanel, wx.ID_ANY, label=_('LED'))
ledEnableButton = wx.Button(settingsPanel, wx.ID_ANY, style=wx.NO_BORDER | wx.MINIMIZE)
ledEnableButton.SetToolTip(_('Toggle switch for') + ' ' + _('LED') + ' ' + _(' Off'))
ledEnableButton.SetBitmap(off)
settingsPanel.Bind(wx.EVT_CHECKBOX, led_enable_switch, ledCheckBox)
ledEnableButton.Bind(wx.EVT_BUTTON, led_enable_switch)

aptxLosslessEnable = None


def aptxLossless_enable_switch_set(enable):
    global aptxLosslessEnable
    aptxLosslessEnable = enable
    aptxLosslessCheckBox.SetValue(enable)
    aptxLosslessEnableButton.SetBitmap(on if aptxLosslessEnable else off)
    aptxLosslessEnableButton.SetToolTip(
        _('Toggle switch for') + ' ' + _('aptX Lossless') + ' ' + (_('On') if aptxLosslessEnable else _('Off')))
    flooSm.enableAptxLossless(enable)


# aptxLossless enable switch function
def aptxLossless_enable_switch(event):
    aptxLossless_enable_switch_set(not aptxLosslessEnable)


aptxLosslessCheckBox = wx.CheckBox(settingsPanel, wx.ID_ANY, label='aptX\u2122 Lossless')
aptxLosslessEnableButton = wx.Button(settingsPanel, wx.ID_ANY, style=wx.NO_BORDER | wx.MINIMIZE)
aptxLosslessEnableButton.SetToolTip(_('Toggle switch for') + ' ' + _('aptX Lossless') + ' ' + _('Off'))
aptxLosslessEnableButton.SetBitmap(off)  # , wx.RIGHT
settingsPanel.Bind(wx.EVT_CHECKBOX, aptxLossless_enable_switch, aptxLosslessCheckBox)
aptxLosslessEnableButton.Bind(wx.EVT_BUTTON, aptxLossless_enable_switch)

gattClientWithBroadcastEnable = None


def gatt_client_enable_switch_set(enable):
    global gattClientWithBroadcastEnable
    gattClientWithBroadcastEnable = enable
    gattClientWithBroadcastCheckBox.SetValue(enable)
    gattClientWithBroadcastEnableButton.SetBitmap(on if gattClientWithBroadcastEnable else off)
    gattClientWithBroadcastEnableButton.SetToolTip(
        _('Toggle switch for') + ' ' + 'GATT ' + _('Client') + ' ' + (
            _('On') if gattClientWithBroadcastEnable else _('Off')))
    flooSm.enableGattClient(enable)


# gatt client enable switch function
def gatt_client_enable_switch(event):
    gatt_client_enable_switch_set(not gattClientWithBroadcastEnable)


gattClientWithBroadcastCheckBox = wx.CheckBox(settingsPanel, wx.ID_ANY, label='GATT ' + _('Client'))
gattClientWithBroadcastEnableButton = wx.Button(settingsPanel, wx.ID_ANY, style=wx.NO_BORDER | wx.MINIMIZE)
gattClientWithBroadcastEnableButton.SetToolTip(_('Toggle switch for') + ' ' + ('GATT ') + _('Client') + ' ' + _('Off'))
gattClientWithBroadcastEnableButton.SetBitmap(off)  # , wx.RIGHT
settingsPanel.Bind(wx.EVT_CHECKBOX, gatt_client_enable_switch, gattClientWithBroadcastCheckBox)
gattClientWithBroadcastEnableButton.Bind(wx.EVT_BUTTON, gatt_client_enable_switch)

settingsPanelSizer.Add(ledCheckBox, 1, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
settingsPanelSizer.Add(ledEnableButton, flag=wx.ALIGN_RIGHT)
settingsPanelSizer.Add(aptxLosslessCheckBox, 1, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
settingsPanelSizer.Add(aptxLosslessEnableButton, flag=wx.ALIGN_RIGHT)
settingsPanelSizer.Add(gattClientWithBroadcastCheckBox, 1, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
settingsPanelSizer.Add(gattClientWithBroadcastEnableButton, flag=wx.ALIGN_RIGHT)
settingsPanelSizer.Hide(aptxLosslessCheckBox)
settingsPanelSizer.Hide(aptxLosslessEnableButton)
settingsPanelSizer.Hide(gattClientWithBroadcastCheckBox)
settingsPanelSizer.Hide(gattClientWithBroadcastEnableButton)

settingsPanelSizer.AddGrowableCol(0, 1)
settingsPanelSizer.AddGrowableCol(1, 0)
settingsPanel.SetSizer(settingsPanelSizer)

versionPanel = wx.Panel(aboutSb)
versionPanelSizer = wx.BoxSizer(wx.VERTICAL)
logoImg = wx.Image(app_path + os.sep + appLogoPng, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
logoStaticBmp = wx.StaticBitmap(versionPanel, wx.ID_ANY, logoImg)
logoStaticBmp.SetToolTip(_('FlooGoo'))
versionPanelSizer.Add(logoStaticBmp, flag=wx.ALIGN_CENTER)
copyRightText = "Copyright© 2023~2024 Flairmesh Technologies."
copyRightInfo = wx.StaticText(versionPanel, wx.ID_ANY, label=copyRightText)
versionPanelSizer.Add(copyRightInfo, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=4)
font = wx.Font(pointSize=10, family=wx.DEFAULT,
               style=wx.NORMAL, weight=wx.NORMAL,
               faceName='Consolas')
dc = wx.ScreenDC()
dc.SetFont(font)
settingsMaxWidth, notUsed = dc.GetTextExtent(copyRightText)
thirdPartyLink = hl.HyperLinkCtrl(versionPanel, wx.ID_ANY, _("Third-Party Software Licenses"),
                                  URL="https://www.flairmesh.com/support/third_lic.html")
versionPanelSizer.Add(thirdPartyLink, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=4)
supportLink = hl.HyperLinkCtrl(versionPanel, wx.ID_ANY, _("Support Link"),
                               URL="https://www.flairmesh.com/Dongle/FMA120.html")
versionPanelSizer.Add(supportLink, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=4)
versionPanel.SetSizer(versionPanelSizer)
versionInfo = wx.StaticText(versionPanel, wx.ID_ANY, label=_("Version") + " 1.1.2")
versionPanelSizer.Add(versionInfo, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=4)

dfuUndergoing = False

# dfuInfoDefaultColor = dfuInfo.cget('foreground')
dfuInfoBind = False
firmwareVersion = ""
variant = ""
a2dpSink = False


def update_dfu_info(state: int):
    global dfuUndergoing
    global firmwareVersion
    global dfuInfoBind

    if state == FlooDfuThread.DFU_STATE_DONE:
        audioModeSb.Enable()
        windowSb.Enable()
        broadcastAndPairedDevicePanel.Enable()
        settingsPanel.Enable()
        dfuButton.Enable()
        dfuInfo.SetLabelText(_("Firmware") + " " + firmwareVersion)
        dfuUndergoing = False
    elif state > FlooDfuThread.DFU_STATE_DONE:
        dfuInfo.SetLabelText(_("Upgrade error"))
        windowSb.Enable()
        dfuUndergoing = True
    else:
        versionPanelSizer.Hide(newFirmwareUrl)
        versionPanelSizer.Show(dfuInfo)
        dfuInfo.SetLabelText(_("Upgrade progress") + (" %d" % state) + "%")
        if not dfuUndergoing:
            dfuButton.Disable()
            audioModeSb.Disable()
            windowSb.Disable()
            broadcastAndPairedDevicePanel.Disable()
            settingsPanel.Disable()
            dfuUndergoing = True
    versionPanelSizer.Layout()


def button_dfu(event):
    with wx.FileDialog(appFrame, _("Open Firmware file"), wildcard="Bin files (*.bin)|*.bin",
                       style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

        if fileDialog.ShowModal() == wx.ID_CANCEL:
            return  # the user changed their mind

        # Proceed loading the file chosen by the user
        filename = fileDialog.GetPath()
        if filename:
            os.chdir(app_path)
            # os.add_dll_directory(app_path)
            fileBasename = os.path.splitext(filename)[0]
            if not re.search(r'\d+$', fileBasename):
                fileBasename = fileBasename[:-1]
            fileBasename += variant
            filename = fileBasename + ".bin"
            if os.path.isfile(filename):
                dfuThread = FlooDfuThread([app_path, filename], update_dfu_info)
                dfuThread.start()


if platform.system().lower().startswith('win'):
    dfuButton = wx.Button(versionPanel, wx.ID_ANY, label=_('Device Firmware Upgrade'))
    dfuButton.Bind(wx.EVT_BUTTON, button_dfu)
    versionPanelSizer.Add(dfuButton, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=4)

dfuInfo = wx.StaticText(versionPanel, wx.ID_ANY, "")
versionPanelSizer.Add(dfuInfo, flag=wx.ALIGN_CENTER)
newFirmwareUrl = hl.HyperLinkCtrl(versionPanel, wx.ID_ANY, _("New Firmware is available"), URL="")
versionPanelSizer.Add(newFirmwareUrl, flag=wx.ALIGN_CENTER)
versionPanelSizer.Hide(newFirmwareUrl)

aboutSbSizer.Add(settingsPanel, proportion=1, flag=wx.EXPAND)
aboutSbSizer.Add(versionPanel, proportion=3)

appSizer.Add(audioModeSbSizer, flag=wx.EXPAND | wx.LEFT, border=4)
appSizer.Add(windowSbSizer, flag=wx.EXPAND | wx.RIGHT, border=4)
appSizer.Add(broadcastAndPairedDevicePanel, flag=wx.EXPAND | wx.LEFT, border=4)
appSizer.Add(aboutSbSizer, flag=wx.EXPAND | wx.RIGHT, border=4)

appSizer.AddGrowableRow(0, 0)
appSizer.AddGrowableRow(1, 1)
appSizer.AddGrowableCol(0, 1)
appSizer.AddGrowableCol(1, 0)

appPanel.SetSizer(appSizer)


def update_status_bar(info: str):
    global statusBar
    statusBar.SetStatusText(text=info)


def enable_settings_widgets(enable: bool):
    if dfuUndergoing:
        return
    if enable:
        if a2dpSink:
            audioModeSb.Disable()
        else:
            audioModeSb.Enable()
        broadcastAndPairedDevicePanel.Enable()
        settingsPanel.Enable()
        pairedDevicesSb.Enable()
        thirdPartyLink.Refresh()
        supportLink.Refresh()
        if platform.system().lower().startswith('win'):
            dfuButton.Enable(not dfuUndergoing)
    else:
        audioModeSb.Disable()
        broadcastAndPairedDevicePanel.Disable()
        settingsPanel.Disable()
        if platform.system().lower().startswith('win'):
            dfuButton.Disable()


enable_settings_widgets(False)

appFrame.Show(True)  # Show the frame.


# All GUI object initialized, start FlooStateMachine
class FlooSmDelegate(FlooStateMachineDelegate):
    def deviceDetected(self, flag: bool, port: str, version: str = None):
        global firmwareVersion
        global variant
        global a2dpSink
        global dfuInfoBind
        global newFirmwareUrl
        global versionPanelSizer
        global aboutSbSizer

        if flag:
            update_status_bar(_("Use FlooGoo dongle on ") + " " + port)
            variant = "" if re.search(r'\d+$', version) else version[-1]
            a2dpSink = True if version.startswith("AS") else False
            firmwareVersion = version if variant == "" else version[:-1]
            # firmwareVersion = firmwareVersion[2:] if a2dpSink else firmwareVersion
            try:
                if a2dpSink:
                    latest = urllib.request.urlopen("https://www.flairmesh.com/Dongle/FMA120/latest_as",
                                                    context=ssl.create_default_context(cafile=certifi.where())).read()
                else:
                    latest = urllib.request.urlopen("https://www.flairmesh.com/Dongle/FMA120/latest",
                                                    context=ssl.create_default_context(cafile=certifi.where())).read()
                latest = latest.decode("utf-8").rstrip()
            except Exception as exec0:
                print("Cann't get the latest version")
                latest = "Unable"

            if not dfuUndergoing:
                if latest == "Unable":
                    newFirmwareUrl.SetLabelText(
                        _("Current firmware: ") + firmwareVersion + _(", check the latest."))
                    newFirmwareUrl.SetURL("https://www.flairmesh.com/Dongle/FMA120.html")

                elif latest > firmwareVersion:
                    versionPanelSizer.Hide(dfuInfo)
                    newFirmwareUrl.SetLabelText(
                        _("New Firmware is available") + " " + firmwareVersion + " -> " + latest)
                    newFirmwareUrl.SetURL("https://www.flairmesh.com/support/FMA120_" + latest + ".zip")
                    versionPanelSizer.Show(newFirmwareUrl)
                    versionPanelSizer.Layout()
                else:
                    dfuInfo.SetLabelText(_("Firmware") + " " + firmwareVersion)
                    versionPanelSizer.Show(dfuInfo)
                    versionPanelSizer.Layout()
        else:
            update_status_bar(_("Please insert your FlooGoo dongle"))
            pairedDeviceListbox.Clear()
            versionPanelSizer.Hide(dfuInfo)
        enable_settings_widgets(flag)

    def audioModeInd(self, mode: int):
        global audioMode
        audioMode = mode
        if a2dpSink:
            pairedDevicesSb.Enable(True)
        else:
            if mode == 0:
                audioModeHighQualityRadioButton.SetValue(True)
            elif mode == 1:
                audioModeGamingRadioButton.SetValue(True)
            elif mode == 2:
                audioModeBroadcastRadioButton.SetValue(True)
            audio_mode_sel_set(mode)

    def sourceStateInd(self, state: int):
        dongleStateText.SetLabelText(sourceStateStr[state])
        audioModeSbSizer.Layout()

    def leAudioStateInd(self, state: int):
        leaStateText.SetLabelText(leaStateStr[state])
        audioModeSbSizer.Layout()

    def preferLeaInd(self, state: int):
        prefer_lea_enable_switch_set(state == 1)

    def broadcastModeInd(self, state: int):
        broadcast_high_quality_switch_set(state & 4 == 4)
        public_broadcast_enable_switch_set(state & 2 == 2)
        broadcast_encrypt_switch_set(state & 1 == 1)

    def broadcastNameInd(self, name):
        broadcastNameEntry.SetValue(name)

    def pairedDevicesUpdateInd(self, pairedDevices):
        pairedDeviceListbox.Clear()
        i = 0
        while i < len(pairedDevices):
            print(pairedDevices[i])
            pairedDeviceListbox.Append(pairedDevices[i])
            i = i + 1
        newPairingButton.Enable(False if preferLeaEnable and i > 0 else True)
        clearAllButton.Enable(True if i > 0 else False)

    def audioCodecInUseInd(self, codec, rssi, rate):
        codecInUseText.SetLabelText(codecStr[codec] if codec < len(codecStr) else _("Unknown"))
        if (codec == 6 or codec == 10) and rssi != 0:
            codecInUseText.SetLabelText(codecStr[codec] + " @ " + str(rate) + "Kbps "
                                        + _("RSSI") + " -" + str(0x100 - rssi) + "dBm")
        else:
            codecInUseText.SetLabelText(codecStr[codec] if codec < len(codecStr) else _("Unknown"))
        audioModeSbSizer.Layout()

    def ledEnabledInd(self, enabled):
        led_enable_switch_set(enabled)

    def aptxLosslessEnabledInd(self, enabled):
        aptxLossless_enable_switch_set(enabled)

    def gattClientEnabledInd(self, enabled):
        gatt_client_enable_switch_set(enabled)


flooSmDelegate = FlooSmDelegate()
flooSm = FlooStateMachine(flooSmDelegate)
flooSm.daemon = True
flooSm.start()

app.MainLoop()

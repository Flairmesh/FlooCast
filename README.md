# FlooCast

A Python application that allows for the control and configuration of FlooGoo USB Bluetooth dongles.

It configures a FlooGoo FMA120 Bluetooth dongle to pair and connect with a Bluetooth headset/speaker for streaming audio or making VoIP calls. It can also configure the dongle to work as an AuraCast sender.

The dongle functions as a standard USB audio speaker and microphone, requiring no drivers on Windows, macOS, or Linux.

## Installation

### Windows
On Windows, the compiled App can be downloaded directly from Microsoft Store.

### Linux/Mac

Requires python 3.7+

#### Configure Python Environment
Create a virtual environment and install the required packages.
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Running
After configuring the environment, run `main.py` within it.
```bash
venv/bin/python main.py
```

If your dongle is not found, or if you see a permission denied error, check the [Platform specific notes/issues](#Platform-specific-notes/issues) section.
You may also choose to run the command as root to ensure it has access to the serial device.
```bash
sudo venv/bin/python main.py
```

## Usage

Once configured, the dongle can automatically reconnect to the most recently used device. Please check the support link for more advanced uses. 
 
## Platform specific notes/issues

On Linux, if you run the app as a non-root user, you might get "Permission denied: '/dev/ttyACM0'" error. 
Please verify the ttyACM0 device is the "dialout" user group and add your $USER to the group.
You may take the following link as a reference,
https://askubuntu.com/questions/133235/how-do-i-allow-non-root-access-to-ttyusb0

## Acknowledgements


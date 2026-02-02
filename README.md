## Usage

WLED Controller for operating various synchronized led strips over UDP packets


## Setup


Install requirements:
```
pip install -r requirements.txt
```

Set target IP and PORT in config/network.py:
```
PORT = 21324
IP = "192.168.0.101"
```

To send packets to WLED controller:
```
python main.py
```

To emulate WLED controller:
```
python wled_emulator.py
```

## TODO:

- Clean up imports and file structure
- Sync over multiple WLED servers
- Add live control system
- Integrate with launchpad
- Integrate with Rekordbox for automatic lighting
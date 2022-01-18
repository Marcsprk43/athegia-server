

import sys

print(sys.path)

from btlescanner import BTLEScanner

def hello_world():
    return 'Hello, Peppe8o users!'

s = BTLEScanner(service_name='scanner', uiCallback=None, emulation_mode=False)

s.scan()

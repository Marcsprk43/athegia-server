import asyncio
from btlescanner import BTLEScanner
from sensors.BTLESensorWellueSPOX2 import BTSensorWellueSPOX
import time
from threading import Thread

s = BTLEScanner(service_name='scanner', uiCallback=None, verbose=False)


t = Thread(target=s.scan, args=())
t.start()

def callback(results_dict):
    print(results_dict)

time.sleep(10)
print('starting the sensor')
sensor1 = BTSensorWellueSPOX(btle_name='VTM 20F', device_name='Pulse Oximeter',
                                scanner_instance=s, 
                                emulation_mode=False)
time.sleep(7)
asyncio.run( sensor1.loop())

print('SPO2 {}'.format(sensor1.spo2))








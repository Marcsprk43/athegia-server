import asyncio
from btlescanner import BTLEScanner
from sensors.BTLESensorTemp import BTSensorTemp
import time
from threading import Thread

s = BTLEScanner(service_name='scanner', uiCallback=None, verbose=True)


t = Thread(target=s.scan, args=())
t.start()

def callback(results_dict):
    print(results_dict)

time.sleep(1)
print('starting the sensor')
sensor1 = BTSensorTemp(device_addr='A8:1B:6A:A8:EC:18', 
                                scanner_instance=s, 
                                emulation_mode=False,
                                reading_timeout=60)

asyncio.run( sensor1.loop())

print('SPO2 {}'.format(sensor1.spo2))





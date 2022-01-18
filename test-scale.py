import asyncio
from btlescanner import BTLEScanner
from sensors.BTLESensorLibelliumScale import BTSensorLibelliumScale
import time
from threading import Thread

s = BTLEScanner(service_name='scanner', uiCallback=None, verbose=False)


t = Thread(target=s.scan, args=())
t.start()

def callback(results_dict):
    print(results_dict)

time.sleep(10)
print('starting the sensor')
sensor1 = BTSensorLibelliumScale(device_name='Electronic Scale', 
                                scanner_instance=s, 
                                emulation_mode=False,
                                reading_timeout=60)

asyncio.run( sensor1.loop())

print('SPO2 {}'.format(sensor1.spo2))





import asyncio
from btlescanner import BTLEScanner
from sensors.BTLESensorLibelliumBP import BTSensorLibelliumBP
import time
from threading import Thread

s = BTLEScanner(service_name='scanner', uiCallback=None, verbose=False)


t = Thread(target=s.scan, args=())
t.start()

def callback(results_dict):
    print(results_dict)

time.sleep(1)
print('starting the sensor')
sensor1 = BTSensorLibelliumBP(device_name='BP01', device_id=1,
                                scanner_instance=s)
time.sleep(1)
asyncio.run( sensor1.loop())

print('SPO2 {}'.format(sensor1.spo2))





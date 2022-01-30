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
sensor1 = BTSensorTemp(btle_addr='A8:1B:6A:A8:EC:18', device_name='Thermometer', device_id=2,
                                scanner_instance=s, 
                                reading_timeout=60)

asyncio.run( sensor1.loop(initial_state=1))

print('SPO2 {}'.format(sensor1.spo2))





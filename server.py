import sys
from flask import Flask
sys.path.append('/home/pi/Documents/src')
from btlescanner import BTLEScanner
import asyncio
from threading import Thread
import json

from sensors.BTLESensorWellueSPOX2 import BTSensorWellueSPOX
from sensors.BTLESensorLibelliumBP import BTSensorLibelliumBP
from sensors.BTLESensorTemp import BTSensorTemp

app = Flask(__name__)




DORMANT = 0
CONNECTING = 1
READ = 2
EXIT = 3
                        
@app.route("/")
def hello_world():
    return '<p>Hello, World!</p><p><a href="http://10.0.0.110:5000/get_status">Get Status</a></p><p><a href="http://10.0.0.110:5000/start_scan">Start Scan</a></p><p><a href="http://10.0.0.110:5000/get_data">Get Data</a></p>'

@app.route("/get_status")
def get_status():
    print('in get_status')
    return_list = []
    for sensor in sensor_list:
        return_list.append(sensor.get_status())
        
    return json.dumps(return_list)
    

@app.route("/start_scan")
def start_scan():
    print('in scanner')

    print('waiting to start scanning')
    import time
    time.sleep(.2)
    for sensor in sensor_list:
        sensor.start_reading()
    
    return "<p>scanning......</p>"

@app.route("/stop_scan")
def stop_scan():
    print('stopping ')
    s1.stop_reading()
    s2.stop_reading()

    return "<p>stopping......</p>"

@app.route("/get_data")
def get_data():
    print('in get_data')
    return_list = []
    for sensor in sensor_list:
        return_list.append(sensor.get_results())
    
    return json.dumps(return_list, indent=4)


@app.route("/terminate")
def terminate():
    print('in terminate')
    s1.terminate()
    s2.terminate()

    t.join()
    return "<p>terminating......</p>"




scanner = BTLEScanner(service_name='bt_scan', uiCallback=None, emulation_mode=False)

t_scanner = Thread(target=scanner.scan, args=())
t_scanner.start()
print('Started scanning Thread.............')

s1 = BTSensorWellueSPOX(device_name='VTM 20F', device_id=0,
                                scanner_instance=scanner)

s2 = BTSensorLibelliumBP(device_name='BP01', device_id=1,
                                scanner_instance=scanner)

s3 = BTSensorTemp(device_addr='A8:1B:6A:A8:EC:18', device_id=2,
                                scanner_instance=scanner, 
                                reading_timeout=40)


sensor_list = [s1, s2, s3]


def get_device_list():
    return sensor_list

#asyncio.gather(s1.loop(), s2.loop())
async def async_collection():
    await asyncio.gather(s1.loop(), s2.loop(), s3.loop())

def run_function():
    asyncio.run(async_collection())

#asyncio.run(async_collection())
t = Thread(target=run_function, args =())
t.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    print('serving on port 5000')
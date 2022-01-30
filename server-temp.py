#####################################################################################
#######                                                                       #######
#######            Test Bluetooth Hub and server for Temp sensor              #######
#######                                 by                                    #######
#######                          Marc van Zyl                                 #######
#######                                                                       #######
#####################################################################################

"""Bluetooh hub and server manages the bluetooth connections and exposes and interface
to read and control the bluetooth devices. The bluetooth hub consists of two 
components each running in its own thread:
   1) a bluetooth scanner that contintually scans the environment for advertising
      bluetooth devices and records a list of the device in a class list that is
      accessible to the bluetooth sensor objects
   2) a collection of bluetooth sensor objects that run asynchronously in a single
      thread. Each sensor object exposes an interface to control the connection
      to the bluetooth device and to read the status and data from the device.
      
The flask server provides the interface to the methods exposed by the bluetooth hub 
components.

The address of the server is http://127.0.0.1:5000

The following methonds are supported:
  /get_status
  /start_scan
  /stop_scan 
  /get_data
  
The results are returned as JSON objects"""

import sys
from flask import Flask
sys.path.append('/home/pi/Documents/src')
from btlescanner import BTLEScanner
import asyncio
from threading import Thread
import json
import datetime

from sensors.BTLESensorWellueSPOX2 import BTSensorWellueSPOX
from sensors.BTLESensorLibelliumBP import BTSensorLibelliumBP
from sensors.BTLESensorTemp import BTSensorTemp

app = Flask(__name__)


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))



DORMANT = 0
CONNECTING = 1
READ = 2
EXIT = 3
                        
@app.route("/")
def hello_world():
    return '<p>Hello, World!</p><p><a href="http://10.0.0.110:5000/get_status">Get Status</a></p><p><a href="http://10.0.0.110:5000/start_scan">Start Scan</a></p><p><a href="http://10.0.0.110:5000/get_data">Get Data</a></p><p><a href="http://10.0.0.110:5000/stop_scan">Stop Scan</a></p>'

@app.route("/get_status")
def get_status():
    print('in get_status')
    return_list = []
    for sensor in sensor_list:
        return_list.append(sensor.get_status())
        
    return json.dumps(return_list, default=json_serial)
    

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
    for sensor in sensor_list:
        sensor.stop_reading()

    return "<p>stopping......</p>"

@app.route("/get_data")
def get_data():
    print('in get_data')
    return_list = []
    for sensor in sensor_list:
        return_list.append(sensor.get_results())
    
    return json.dumps(return_list, indent=4, default=json_serial)


@app.route("/terminate")
def terminate():
    print('in terminate')
    for sensor in sensor_list:
        sensor.terminate()

    t.join()
    return "<p>terminating......</p>"




scanner = BTLEScanner(service_name='bt_scan', uiCallback=None, emulation_mode=False)

t_scanner = Thread(target=scanner.scan, args=())
t_scanner.start()
print('Started scanning Thread.............')


s3 = BTSensorTemp(btle_addr='A8:1B:6A:A8:EC:18', device_name='Temp', device_id=2,
                                scanner_instance=scanner, 
                                reading_timeout=40)


sensor_list = [s3]


def get_device_list():
    return sensor_list

#asyncio.gather(s1.loop(), s2.loop())
async def async_collection():
    await asyncio.gather(s3.loop())

def run_function():
    asyncio.run(async_collection())

#asyncio.run(async_collection())
t = Thread(target=run_function, args =())
t.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    print('serving on port 5000')
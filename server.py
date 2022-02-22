#####################################################################################
#######                                                                       #######
#######                      Bluetooth Hub and server                         #######
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
from flask_cors import CORS
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
CORS(app)

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

@app.route("/get_user_info")
def get_user_info():
    print('in get_user_info')
    
    return json.dumps(user_info, indent=4, default=json_serial)

@app.route("/get_device_info")
def get_device_info():
    print('in get_device_info')
    
    return json.dumps(config, indent=4, default=json_serial)

@app.route("/save_results")
def save_results():
    import firebase_admin
    from firebase_admin import credentials
    from firebase_admin import firestore

    import os


    print('in save_results')

    # collect the results
    return_list = []
    for sensor in sensor_list:
        return_list.append(sensor.get_results())
    
    results_dict = {'results':return_list}

    print('Connecting to firestore')
    try:
        # Use the JSON Certificate
        cred = credentials.Certificate('{}/{}'.format(os.getcwd(),config['FirestoreConfig']['firestore_cred_token']))

        # Use the application default credentials
        #cred = credentials.ApplicationDefault()

        firebase_admin.initialize_app(cred, {
        'projectId': config['FirestoreConfig']['firestore_project'],
        })

        db = firestore.client()
    except Exception as e:
        print('ERROR connecting to firestore db')
        print(e)
    else:

        def save_fs_document(collection, path, dict):
            """Function to save a dict to firestore"""
            try: 
                tileRef = db.document('{}/{}'.format(collection, path))
                tileRef.set(dict)
                
                return True
            except Exception as e:
                print(e)        
                return e    
        
        save_fs_document(config['FirestoreConfig']['firestore_collection'],
                    '{}/{}/{}'.format(user_info['UserUUID'],'results', datetime.datetime.now()), 
                    results_dict)

    # clean up and close the firestore app
    print('Cleaning up the firestore app')
    try:
        if firebase_admin.get_app():
            firebase_admin.delete_app(firebase_admin.get_app())
    except Exception as e:
        print('ERROR in cleaning up the firestore app')
        print(e)

    return 1



@app.route("/terminate")
def terminate():
    print('in terminate')
    for sensor in sensor_list:
        sensor.terminate()

    t.join()
    return "<p>terminating......</p>"



# Load the configurations
import os

# load the device configuration with the firestore information
with open('{}/config.json'.format(os.getcwd())) as f:
    config = json.load(f)

# load the user configuration
with open('{}/user_info.json'.format(os.getcwd())) as f:
    user_info = json.load(f)



scanner = BTLEScanner(service_name='bt_scan', uiCallback=None, emulation_mode=False)

t_scanner = Thread(target=scanner.scan, args=())
t_scanner.start()
print('Started scanning Thread.............')

s1 = BTSensorWellueSPOX(btle_name='VTM 20F', device_name='SPO2', device_id=0,
                                scanner_instance=scanner)

s2 = BTSensorLibelliumBP(btle_name='BP01', device_name='BP', device_id=1,
                                scanner_instance=scanner)

s3 = BTSensorTemp(btle_addr='A8:1B:6A:A8:EC:18', device_name='Temp', device_id=2,
                                scanner_instance=scanner, 
                                reading_timeout=40)


sensor_list = [s1, s2, s3]

# this is the event loop that will be run in the thread
def start_background_thread_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def get_device_list():
    return sensor_list

#asyncio.gather(s1.loop(), s2.loop())
async def async_collection():
    await asyncio.gather(s1.loop(), s2.loop(), s3.loop())


async def launch_all_loops(sensors) -> None:
    """Fetch all urls from the list of urls
    It is done concurrently and combined into a single coroutine"""
    tasks = [asyncio.create_task(sensor.loop()) for sensor in sensors]
    results = await asyncio.gather(*tasks)


#asyncio.run(async_collection())
loop = asyncio.new_event_loop()

t = Thread(target=start_background_thread_loop, args =(loop,))
t.start()

asyncio.run_coroutine_threadsafe(launch_all_loops(sensor_list), loop)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    print('serving on port 5000')
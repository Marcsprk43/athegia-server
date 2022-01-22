import sys
from flask import Flask
sys.path.append('/home/pi/Documents/src')
from btlescanner import BTLEScanner
import asyncio
from threading import Thread
import json

from sensors.BTLESensorDummy import BTSensorDummy

app = Flask(__name__)


DORMANT = 0
CONNECTING = 1
READ = 2
EXIT = 3

class Sensor():
    # static class variables
    
    def __init__(self, name, connect_delay=1, notify_delay=1):
        self.name = name
        self.exit = False
        self.state = DORMANT
        self.connect_delay = connect_delay
        self.notify_delay = notify_delay        
        self.return_value_count = 0
        
    def start_reading(self):
        self.state = CONNECTING
        
    def stop_reading(self):
        self.state = DORMANT
        
    def terminate(self):
        self.exit = True

    async def loop(self):
        while not self.exit:
            
            ## finite state machine
            # connect
            if self.state == CONNECTING:
                print('{}:: not connected'.format(self.name))
                print(get_device_list())
                await asyncio.sleep(self.connect_delay)
                self.state = READ
                self.return_value_count = 0
                print('{}:: connected'.format(self.name))
            
            # read
            elif self.state == READ:
                await asyncio.sleep(self.notify_delay)
                self.return_value_count += 1
                self.callback()
                if self.return_value_count > 20:
                    self.state = DORMANT

            elif self.state == DORMANT:
                await asyncio.sleep(0.5)
            
            else: 
                await asyncio.sleep(0.5)
        print('From Sensor:: Exiting {}'.format(self.name))        
                
                
    def callback(self):
        print('{}:: Callback - return_value_count_ {}'.format(self.name, self.return_value_count))
        
                        
@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/get_status")
def get_status():
    print('in get_status')
    return_string = ''
    for sensor in sensor_list:
        return_string += json.dumps(sensor.get_status())
    
    return return_string


@app.route("/start_scan")
def start_scan():
    print('in scanner')

    print('waiting to start thread in 2 seconds')
    import time
    time.sleep(2)
    for sensor in sensor_list:
        print('Starting sensor {}'.format(sensor))
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
    print('in get_status')
    return_string = ''
    for sensor in sensor_list:
        return_string += json.dumps(sensor.get_results(), indent=4)
    
    return return_string

@app.route("/terminate")
def terminate():
    print('in terminate')
    s1.terminate()
    s2.terminate()

    t.join()
    return "<p>terminating......</p>"




<<<<<<< HEAD
scanner = BTLEScanner(service_name='bt_scan', uiCallback=None, verbose=False)
=======
#scanner = BTLEScanner(service_name='bt_scan', uiCallback=None, emulation_mode=False, verbose=False)
>>>>>>> 8f9a970c5336996501f1a436d7c643797b7c7c43

#t_scanner = Thread(target=scanner.scan, args=())
#t_scanner.start()
print('Started scanning Thread.............')

sensor1_config = {
    'find_delay' : 5,
    'connect_delay' : 7,
    'read_delay' : 10,
    'read_complete_delay' : 17,
    'disconnect_delay': 19 }

sensor2_config = {
    'find_delay' : 20,
    'connect_delay' : 22,
    'read_delay' : 25,
    'read_complete_delay' : 32,
    'disconnect_delay': 34 }


s1 = BTSensorDummy(device_name='VTM 20F', device_id=0,
                                scanner_instance="fakeScanner", 
                                emulation_mode=False,
                                config=sensor1_config)

s2 = BTSensorDummy(device_name='VTM 21F', device_id=1,
                                scanner_instance=scanner, 
                                emulation_mode=False,
                                config=sensor2_config)
sensor_list = [s1,s2]

device_list = [{'name':'SPO2', 'address':'1223456789'},{'name':'BP', 'address':'aaaaaaaaaaaaaa'}]

def get_device_list():
    return device_list

#asyncio.gather(s1.loop(), s2.loop())
async def async_collection():
    await asyncio.gather(s1.loop(), s2.loop())

def run_function():
    asyncio.run(async_collection())

#asyncio.run(async_collection())
t = Thread(target =run_function, args =())
t.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
    print('serving on port 5000')
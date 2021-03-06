import sys
from flask import Flask
sys.path.append('/home/pi/Documents/src')
from btlescanner import BTLEScanner
import asyncio
from threading import Thread

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



@app.route("/scan")
def scanning():
    print('in scanner')

    print('waiting to start thread in 2 seconds')
    import time
    time.sleep(2)
    s1.start_reading()
    s2.start_reading()
    
    return "<p>scanning......</p>"

@app.route("/stop")
def stop():
    print('stopping ')
    s1.stop_reading()
    s2.stop_reading()

    return "<p>stopping......</p>"

@app.route("/val")
def val():
    print('in getValues')
    s1.return_value_count
    return "<p>S1 {}...... S2 {}</p>".format(s1.return_value_count, s2.return_value_count)

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

s1 = Sensor('test1',connect_delay=2, notify_delay=1)
s2 = Sensor('test2',connect_delay=4, notify_delay=2)

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
    app.run(host='0.0.0.0', port=5000)
    print('serving on port 5000')
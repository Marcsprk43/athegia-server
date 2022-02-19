import numpy as np
import bleak
import asyncio
import re
import datetime


class BTSensorBP():
    import numpy as np
    import bleak
    import asyncio
    import re
    import datetime

    device_name = ''
    client = None
    found_device = None
    services = None
    good_readings = 0
    number_readings = 0
    scale_user_profile = bytearray([0]*8)
    
    # Ring buffer
    buff_timestamp = None
    buff_value = None
    buff_counter = 0
    buff_size = 0
    buff_index = 0
    
    # Results
    systolic = 0.0
    diastolic = 0.0
    pulse = 0
    
    
    def __init__(self, device_name=None):
        if not device_name == None:
            self.device_name = device_name
        else:
            print("Error no device name specified")
            
    async def scan(self):
        devices = await bleak.discover()

        device_list = []

        for d in devices:
            print(d, d.rssi)
            device_list.append(d)
        return device_list
    
    def find_device(self, device_list, name):
        found_device_list = []
        for device in device_list:
            if re.search(name,device.name, flags=re.IGNORECASE):
                found_device_list.append(device)
        return found_device_list

    async def connect(self):
        
        if not self.found_device:
            print('Looking for device....')
            device_list = await self.scan()
            found_device_list = self.find_device(device_list,self.device_name)
            print('Found devices:\n{}'.format(found_device_list))
            if len(found_device_list) > 0:
                self.found_device = found_device_list[0]
            else:
                return False
        else:
            print('Device already registered')
            print(self.found_device)
            
        if not self.client:
            print('Creating BTLE client....')
            self.client = bleak.BleakClient(self.found_device.address)
        else:
            print('Using existing client')
            
        await self.client.connect()
        
        return self.client.is_connected
    
    async def connect_when_ready(self):
        tries = 16
        
        while tries > 0:
            print('Try: {}'.format(tries))
            result = await self.connect()
            if result:
                print('Connected....')
                services = await self.get_services()
                for key in services.characteristics.keys():
                  print('{} : {} {} {}'.format(key, services.get_characteristic(key).description,
                  services.get_characteristic(key).properties,
                  services.get_characteristic(key).uuid))
                return
            tries -= 1


    async def connect_and_get(self):
        await self.connect_when_ready()
        await self.get_readings(number_of_readings=1, callback=None)

    
    async def disconnect(self):
        
        if self.client:
            print('Client exists....')
            if self.client.is_connected:
                print('Client is connected....')
                await self.client.disconnect()
            return self.client.is_connected
        else:
            print('Client does not exist...')
            return False


    async def get_services(self, ):
        
        if self.client.is_connected:
            self.services = await self.client.get_services()
        else:
            print('Connect to device before reading services')
        
        return self.services
        
    def print_services(self, ):
        if not self.services == None:
            for key in self.services.characteristics.keys():

                print('{} : {}  {} {}'.format(key,self.services.get_characteristic(key).description,
                                           self.services.get_characteristic(key).properties,
                                           self.services.get_characteristic(key).uuid))
        else:
            print('Discover services with client.get_services() before printing')
        return
    
    async def notify(self, service_num, callback=None):
        if callback == None:
            cb = self.callback
        else:
            cb = callback
        await self.client.start_notify(service_num, cb)
        return True
        
    async def stop_notify(self, service_num):
        await self.client.stop_notify(service_num)
        return True

    async def get_readings(self, number_of_readings=1, callback=None):
        self.good_readings = 0
        self.number_readings = 0

        if callback == None:
            cb = self.callback
        else:
            cb = callback
        # initialize and send the command to start the pressure 
        await self.client.write_gatt_char('0000ffe1-0000-1000-8000-00805f9b34fb', bytearray([0x65]))  # initialize 
        await asyncio.sleep(.1)
        await self.client.write_gatt_char('0000ffe1-0000-1000-8000-00805f9b34fb', bytearray([0x65]))  # initialize 
        await asyncio.sleep(.1)
        await self.client.start_notify('0000ffe1-0000-1000-8000-00805f9b34fb', cb)
        
        while self.good_readings < number_of_readings:  # add timeout
            await asyncio.sleep(1)
            
        print('Found {} good readings'.format( number_of_readings))

        
        await self.client.stop_notify('0000ffe1-0000-1000-8000-00805f9b34fb')
        
        print('Done with get_readings')
        
        return True


    
    data_list=[]
    
    def init_ring_buffer(self, size):
        self.buff_size = size
        self.buff_timestamp = np.empty(size*2, dtype='datetime64[ms]')
        self.buff_value =  np.empty(size*2, dtype='float')
        self.buff_counter = 0
        self.buff_index = 0
        print('Ring buffer of {} x 2 elements initialized'.format(self.buff_size) )
        return self.buff_size
    
        
    def add_to_ring_buffer(self, time_stamp, value):
        index = int(self.buff_counter%self.buff_size)
        self.buff_timestamp[index] = time_stamp
        self.buff_value[index] = value

        self.buff_timestamp[index + self.buff_size] = time_stamp
        self.buff_value[index + self.buff_size] = value

        self.buff_counter += 1
        return self.buff_counter

        
        
    def read_ring_buffer(self):
        max_rows = min(self.buff_size, self.buff_counter)
        index = int(self.buff_counter%self.buff_size)
        return (self.buff_timestamp[(index+self.buff_size - max_rows):(index+self.buff_size)],
                self.buff_value[(index+self.buff_size - max_rows):(index+self.buff_size)])
        



    def callback(self, sender, data:bytearray ):  
        time_stamp = np.datetime64(datetime.datetime.now(),'ms')
        if (data[0] == 0x67) and (data[1] == 0x2f):   # This is the result
            self.number_readings += 1
            print('{} - '.format(sender, data), end='')
            self.data_list.append(data)
            data_point = [int(b) for b in data]


            
            # Calculations based on mySignals code
            self.systolic = (data_point[2]-48)*100 + (data_point[3]-48)*10 + (data_point[4]-48)
            self.diastolic = (data_point[6]-48)*100 + (data_point[7]-48)*10 + (data_point[8]-48)
            self.pulse = (data_point[10]-48)*100 + (data_point[11]-48)*10 + (data_point[12]-48)            
            
            if self.systolic > 80 and self.diastolic < 150:
                self.good_readings += 1
                print('\nGood readings: {} ({})'.format(self.good_readings, self.number_readings))

            print('\n')   
            print('Systolic:          {}'.format(self.systolic))
            print('Diastolic:         {}'.format(self.diastolic))
            print('Pulse:             {}'.format(self.pulse))
                                    
            


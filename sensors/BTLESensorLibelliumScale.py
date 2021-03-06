###################################################
#   Bluetooth Low Energy Sensor Class
#   based on the Bleak BTLE framework
#   by Marc van Zyl
###################################################

# for reverse engineering approach see the notebook at:
# https://drive.google.com/file/d/1-Vr0NEy-ypGBnR2Ukwu7-xShxoJlw1Do/view?usp=sharing

import asyncio
import bleak
import re
import numpy as np
import datetime


#nest_asyncio.apply()

####### ToDo #########
# 1. In the unlikely event that two BTLE devices with the same name is in the vincinty implement a pairing concept
#    using UUID identifier

class fakeClient():
    """
    This is a test class that emulates a real bluetooth device used for testing. The emulated device is a
    Wellue SPOX sensor. Only the SPO2 and Pulse readings are emulated.
    
    Parameters:
    None
    
    Returns:
    None"""

    initialized = False
    address = None
    is_connected = False
    notify = False
    # This is the fake data that will be passed to the calling object
    data = [bytearray.fromhex('fe0a5500456026eb081d'),
            bytearray.fromhex('fe0a55004760287702a7'),
            bytearray.fromhex('fe0a5500456026eb081d'),
            bytearray.fromhex('fe0a55004760287702a7'),
            bytearray.fromhex('fe0a5500456026eb081d'),
            bytearray.fromhex('fe0a55004760287702a7')
           ]
    
    def __init__(self, address):
        """Object initialization method.
        
        Parameters:
        address: the MAC address or the UUID of the bluetooth device - not used in emulation
        
        Returns:
        None"""
        self.initialized = True
        self.address = address
        print("fakeClient :: initialized to address {}".format(self.address))
        
        
    async def connect(self):
        """
        Connect to the emulator.
        
        Parameters:
        None
        """
        print('fakeClient :: connecting.....')
        await asyncio.sleep(1)
        self.is_connected = True

    async def disconnect(self):
        """
        Disconnect from the emulator.
        
        Parameters:
        None
        """
        print('fakeClient :: disconnecting.....')
        await asyncio.sleep(1)
        self.is_connected = False
                
    async def start_notify(self,service_num, cb):
        """
        Emulation of the bleak bluetooth start_notify command. It will send back 7 readings
        before terminating
        
        Parameters:
        service_num(int): the service on the bluetooth device to connect to
        cb(function): the callback function that bluetooth packets are forwarded to"""
        
        self.notify = True
        count = 0
        
        good_readings = 0 # Counter for the number of readings returned
        while good_readings<7:
            print('fakeClient :: starting notify')

            # send data to callback
            print('fakeClient :: sending - {}'.format(self.data[count]))
            good_readings = cb('fakeClient', self.data[count] )
            
            count += 1
            if count > 3:
                count = 0
                
            print('fakeClient :: sleeping - notify {}'.format(self.notify))
 
            await asyncio.sleep(1)
    
        print('fakeClient :: stopping notify')
            
    async def stop_notify(self, service_num):
        print('fakeClient :: stopping notify')
        self.notify = False
        
        
class BTSensorLibelliumScale():
    """
    Class to manage the full connection to a bluetooth device using the bleak library.
    """

    import numpy as np

    # Global class variables
    scanner_instance = None
    device_name = ''
    #device_service_number = 26   # This is from the reverse engineering
    characterisitc_UUID = '0000fff4-0000-1000-8000-00805f9b34fb'
    client = None
    found_device = None
    services = None
    good_readings = 0
    number_readings = 0

    loop_counter = 0
    
    # Key device parameters
    scale_user_profile = bytearray([0]*8)
    
    # Ring buffer - this holds the readings for pleth that streams in at about 30Hz
    buff_timestamp = None
    buff_value = None
    buff_counter = 0
    buff_size = 0
    buff_index = 0

    # loop state machine variables
    STATE_DORMANT = 0
    STATE_CONNECTING = 1
    STATE_READING = 2

    force_exit_flag = False
    # This is the main loop state variable
    state = STATE_DORMANT  # main state variable - initialize to DORMANT
   
    # this is the results dict that the flask server has access to
    results_dict = {}

  

    def __init__(self, device_name=None, device_addr=None, device_id=None,
                        scanner_instance=None, reading_timeout=40,
                        emulation_mode=False):
        """
        Constructor function that initializes the object variables.
        
        Parameters:
        device_name(str): the name of the bluetooth device
        device_addr(str): the bluetooth address or UUID of the bluetooth device
        scanner_instance(obj): a pointer to the btle scanner to access the list of devices
        emulation_mode(boolean): run in emulation mode if true
        """

        # First check that required parameters are present
        if (((not device_name == None) or (not device_addr == None))
                and (not device_id)
                and (not scanner_instance == None)):
            self.device_name = device_name   # set the class variable device name
            self.device_addr = device_addr   # set the class variable device name
            self.device_id = device_id
            self.good_readings = 0           # reset for multiple calls
            self.scanner_instance = scanner_instance
            self.stop_reading_flag = False   # flag to interrupt the reading cycle
            self.reading_timeout_sec = reading_timeout  # the timeout of the reading cycle

            if emulation_mode:
                self.emulation_mode = True
            else:
                self.emulation_mode = False

            # set the status to initialized and send it back to the app
            self.init_results_dict()


        else:
            print("Error no device name specified")


    def init_results_dict(self):
        """Simple method to reset and initialize the results_dict"""
        self.results_dict = {}
        # These are standard across all sensors
        self.results_dict['device_id'] = self.device_id
        self.results_dict['device_name'] = self.device_name
        self.results_dict['status'] = 'Initialized'
        self.results_dict['message'] = ''
        self.results_dict['finalized'] = False
        self.results_dict['connected'] = False
        # These are unique to the sensor
        self.results_dict['data'] = {}
        self.results_dict['data']['weight'] = 0
        self.results_dict['data']['body_fat_percentage'] = 0 
        self.results_dict['data']['bone_mass_percentage'] = 0
        self.results_dict['data']['muscle_mass_percentage'] = 0
        self.results_dict['data']['visceral_fat_percentage'] = 0
        self.results_dict['data']['body_water_percentage'] = 0
        self.results_dict['data']['total_readings'] = 0
        self.results_dict['data']['good_readings'] = 0

    def get_status(self):
        status_dict = {}
        status_dict['scanner_instance'] = ('{}'.format(self.scanner_instance) 
                                            if self.scanner_instace
                                            else 'None')
        status_dict['device_name'] = self.device_name
        status_dict['client'] = 'Connected' if self.client else 'None'
        status_dict['found_device'] = True if self.found_device else False
        status_dict['loop_counter'] = self.loop_counter
        # status_dict[''] = 

        # Add more here 
        
        return status_dict
    
    def start_reading(self):
        if self.state == self.STATE_DORMANT:
            self.state == self.STATE_CONNECTING
            print('{}:: Started reading cycle...'.format(self.device_name))

        else:
            print('{}:: Error cannot start reading from state {}'.format(self.device_name, self.state))
    
    def stop_reading(self):
        if self.state == self.STATE_CONNECTING:
            self.state = self.STATE_DORMANT

        if self.state == self.STATE_READING:
            self.stop_reading_flag = True

    def get_results(self):
        return self.results_dict


    def find_device(self, device_list, name):
        """
        Look for and find a particular device in a list of Bleak.device objects.
        
        Parameters:
        device_list(list of Bleak.device): the list of devices returned by this.scan()
        name(str): The name of the device found 
        
        Returns:
        found_device_list(list of Bleak.device): the list of Bleak.device objects where  
        Bleak.device.name == name
        """
        found_device_list = []
        # iterate over the devices and if the name matches append it to the found_device_list
        try:
            for device in device_list:
                if self.emulation_mode:
                    if re.search(name,device['name'], flags=re.IGNORECASE):
                        found_device_list.append(device)
                        # set the status to scanning and send it back to the app
                        self.results_dict['status'] = 'Found....'
                else:
                    
                    if re.search(name,device.name, flags=re.IGNORECASE):
                        print('{}:: Found device with name: {}'.format(self.device_name, device.name))
                        found_device_list.append(device)
                        # set the status to scanning and send it back to the app
                        self.results_dict['status'] = 'Found....'   
        except Exception as e:
            print('{}:: ERROR in find_device - device_list is probably invalid'.format(self.device_name))                 

        return found_device_list

    async def connect(self):
        """
        Core method to search for and connect to a bluetooth client. This method will scan if 
        there are no found_devices, search for the relevant device and then connect to the device.
        The connection to the device is stored in the self.client variable.
        
        Returns:
        is_connected(boolean): True if connected, False if not
        """

        # first check to see if the device was previously found
        if not self.found_device:
            device_list = self.scanner_instance.devices
            found_device_list = self.find_device(device_list,self.device_name) # search for the device

            if len(found_device_list) > 0:  # a device was found
                print("{}:: Bluetooth devices found with name: {}".format(self.device_name,self.device_name))
                self.found_device = found_device_list[0] # If there are multiple devices use the first one
                print('{}:: name: {}  btle address: {}'.format(self.device_name,
                            self.found_device.name, self.found_device.address))
            else:
                return False  # no device was found - return
        else:
            print('Device already registered')
            print(self.found_device)
            
        if not self.client:
            print('Creating BTLE client....')

            # set the status to scanning and send it back to the app
            self.results_dict['status'] = 'Connecting....'

            if not self.emulation_mode:
                print('{}:: Connecting to device with address: {}'.format(self.device_name, 
                                                                          self.found_device.address))
                try:                                                          
                    self.client = bleak.BleakClient(self.found_device.address)
                except Exception as e:
                    print('{}:: ERROR connecting to bleak.BleakClient-address: {}'.format(self.device_name, 
                                                                self.found_device.addr))
                    self.client = False

                    return False
            else:
                self.client = fakeClient(self.found_device['address'])
           
        else:
            print('Using existing client')

        # Connect to the bluetooth device 
        try:   
            await self.client.connect()
        except Exception as e:
            print('{}:: ERROR could not connect to btle client'.format(self.device_name,
                                                                self.client))
            self.client = False
            return False

        if self.client.is_connected:
            print('{}:: Successfully connected to btle client')
            # set the status to connected and send it back to the app
            self.results_dict['status'] = 'Connected....'
            self.results_dict['connected'] = True
            self.results_dict['finalized'] = False
        
        return self.client.is_connected




    def reset_variables(self):
        self.good_readings = 0
        self.number_readings = 0

        self.init_ring_buffer(300)


    async def loop(self, initial_state=STATE_CONNECTING):
        """The main loop method the implements the BTLE reader finite state machine.
        """
        self.state = initial_state

        while not self.force_exit_flag:  # this allow for the loop to be terminated
            ## Finite State Machine
            self.loop_counter += 1         # this a counter to keep track of the heartbeat

            # Idle
            if self.state == self.STATE_DORMANT:
                await asyncio.sleep(0.5)  # sleep for 0.5 and hand back to event loop

            elif self.state == self.STATE_CONNECTING:

                if not await self.connect():
                    await asyncio.sleep(0.5)    # no device found - back off for 0.5 sec
                else:                           # a device was found and connected
                    print('{}:: device found and connected'.format(self.device_name))
                    print('{}:: entering READ state.....'.format(self.device_name))
                    self.reset_variables()
                    self.state = self.STATE_READING  # advance the state

            elif self.state == self.STATE_READING:

                result, msg = await self.get_readings(self.device_service_number, 
                                                        callback=None, num_readings=7)
                if result == 1:
                    print('{}:: Successfully completed readings'.format(self.device_name))
                    self.state = self.STATE_DORMANT
                    print('{}:: Transitioning to state: {}'.format(self.device_name, self.state))
                elif result == -1:      # timeout error
                    print('{}:: Problem with readings: {}'.format(self.device_name, msg))
                    self.state = self.STATE_CONNECTING
                elif result == -2:      # stop_signal
                    print('{}:: Problem with readings: {}'.format(self.device_name, msg))
                    self.state = self.STATE_DORMANT
    
            else:
                await asyncio.sleep(0.5)





    
    async def disconnect(self):
        """
        Method to disconnect from a bluetooth client
        """
        
        if self.client:
            print('Client exists....')
            if self.client.is_connected:
                print('{}:: Client is connected....disconecting'.format(self.device_name))
                await self.client.disconnect()
                # set the status to connected and send it back to the app
                self.results_dict['status'] = 'Disconnected....'
                self.results_dict['connected'] = False
                print('{}:: BTLE Client is disconnected'.format(self.device_name))

            return self.client.is_connected
        else:
            print('Client does not exist...')
            return False


    async def get_services(self):
        """
        Interface the Bleak.client.get_services() method, which connects to a device and
        scans the GATT services and characteristics offered by the device. The resulting
        Bleak.services object is stored in a class variable

        Returns:
        services(Bleak.client.services): the object with the services and the descriptions
        """
        
        if self.client.is_connected:  # make sure we have a connection 
            self.services = await self.client.get_services()
        else:
            print('Connect to device before reading services')
        
        return self.services
        
    def print_services(self, ):
        """
        Method to print the details of the services and the characteristics to the console
        """
        if not self.services == None: # check that we have done a get_services 
            for key in self.services.characteristics.keys():  # iterate over service characteristics

                print('{} : {}  {} {}'.format(key,self.services.get_characteristic(key).description,
                                           self.services.get_characteristic(key).properties,
                                           self.services.get_characteristic(key).uuid))
        else:
            print('Discover services with client.get_services() before printing')
        return
    
    async def notify(self, service_num, callback=None):
        """
        Method to connect to a service offering a notification characteristic

        Prameters:
        service_num(int): the service identifier corresponding to the service
        callback(function): the callback function that will be called with the data when 
        the bluetooth device communicates. If callback is not specified then the 
        default callback function will be used
        """
        if callback == None:
            cb = self.default_callback
            print('Setting call back to default_callback')
        else:
            cb = callback
        await self.client.start_notify(service_num, cb)

        # set the status to connected and send it back to the app
        self.results_dict['status'] = 'Reading....'

        return True
        
    async def stop_notify(self, service_num):
        """
        Method to disconnect from a notify service
        """
        await self.client.stop_notify(service_num)
        self.results_dict['status'] = 'Connected....'

        return True


    def check_stop_reading_flag(self):
        """Method to safely stop the reading loop and reset the flag"""
        if self.stop_reading_flag:
            self.stop_reading_flag == False
            return True
        return False

    def set_user_profile(self, 
                         user_group = 1,         # user group
                         user_gender = 1,        # gender: 1=male, 0=female
                         user_level = 0,         # level 0=normal
                         user_height = 180,      # height in cm
                         user_age = 54,          # age
                         user_unit = 1):          # return units in kg
    
        user_byte0 = 0xfe      # start byte
        user_xor = 0

        self.scale_user_profile = bytearray([user_byte0,
                                        user_group,
                                        user_gender,
                                        user_level,
                                        user_height,
                                        user_age,
                                        user_unit,
                                        user_xor])


        # calculate the XOR checksum
        for ind in range(1,7):
            print('{:08b}  {:08b}'.format( self.scale_user_profile[7], self.scale_user_profile[ind]))
            self.scale_user_profile[7] = self.scale_user_profile[7] ^ self.scale_user_profile[ind]

    async def get_readings(self, service_num, callback=None, num_readings=7):
        """
        Method to get a specified number of 'good' readings from an asyncronous bluetooth notify service. 
        
        Parameters:
        service_num(int): the service identifier
        callback(function): the callback function that will be called with the data when 
        the bluetooth device communicates. If callback is not specified then the 
        default callback function will be used
        num_readings(int): the number of good readings to obtain before terminating the subscription to notify

        """

        return_code = 0  # return code to track errors
        return_msg = 'None'

        # If there is no callback function specified use default_callback
        if callback == None:
            cb = self.default_callback
        else:
            cb = callback
            
        # subscribe to the notifications
        try:
            await self.client.write_gatt_char('0000fff1-0000-1000-8000-00805f9b34fb', self.scale_user_profile)  # initialize 
            await asyncio.sleep(.1)
            await self.client.start_notify(   self.characterisitc_UUID, cb)
 
        except Exception as e:
            print('{}:: ERROR with client.start_noitify service_num={} callback={}'
                        .format(self.device_name, service_num, cb))
        else:
        
            # set up the timeout trigger
            time_out = datetime.datetime.now() + datetime.timedelta(0,self.reading_timeout_sec)
            loop_flag = True

            while loop_flag:
                if self.good_readings >= num_readings:
                    loop_flag = False
                    return_code = 1
                    return_msg = 'Success with {} readings'.format(num_readings)
                    print('{}:: Successful sensor reading'.format(self.device_name))
                elif datetime.datetime.now() > time_out:
                    loop_flag=False
                    return_msg = 'Timeout'
                    print('{}:: Timeout in sensor reading'.format(self.device_name))
                    return_code = -1
                elif self.check_stop_reading_flag():
                    loop_flag=False
                    return_msg = 'Stop reading signal'
                    print('{}:: Sensor reading interrupted with stop_reading signal'.format(self.device_name))
                    return_code = -2
                else:
                    await asyncio.sleep(.5)
                    print('{}:: mainloop :: sleep cycle - good_readings {}'.format(self.device_name,
                                                                            self.good_readings ))
            
            print('{}:: mainloop -stopping notify'.format(self.device_name))

            # Unsubscribe from notifications
            try:
                await self.client.stop_notify(self.characterisitc_UUID)
            except Exception as e:
                print('{}:: ERROR failed in unsubscribe from notify'.format(self.device_name))
                print(e)

        if return_code == 1:
            self.results_dict['status'] = 'Completed'
            self.results_dict['finalized'] = True
        else:
            self.results_dict['status'] = 'Failed'
            self.results_dict['finalized'] = False
            
            

        try:
            await self.client.disconnect()
            
        except Exception as e:
                print('{}:: ERROR failed in btle lient disconnect'.format(self.device_name))
                print(e)

        self.results_dict['connected'] = False

        return return_code, return_msg


    
    data_list=[]
    
    def init_ring_buffer(self, size):
        """
        Initialize the ring buffer and create the Numpy array in memory. This simple ring buffer
        is twice the lenght of the ring (2*N) and all values are written at 2 locations n and n+N. This 
        makes retrieval really simple by slicing the numpy array from n+1:n+N+1. The buffer stores the 
        values and a timestamp in datetime64[ms] format

        Parameters
        size(int): the lenghth of the ring buffer

        Returns:
        buff_size(int): the buffer size
        """
        self.buff_size = size
        self.buff_timestamp = np.empty(size*2, dtype='datetime64[ms]')
        self.buff_value =  np.empty(size*2, dtype='float')
        self.buff_counter = 0
        self.buff_index = 0
        print('Ring buffer of {} x 2 elements initialized'.format(self.buff_size) )
        return self.buff_size
    
        
    def add_to_ring_buffer(self, time_stamp, value):
        """
        Add a data point and associated time_stamp to the ring buffer.
        
        Parameters:
        time_stamp(datetime64[ms]): the time stamp
        value(float): the value to be stored
        
        Returns:
        buff_counter(int): the number of values stored
        """
        index = int(self.buff_counter%self.buff_size)
        self.buff_timestamp[index] = time_stamp
        self.buff_value[index] = value

        self.buff_timestamp[index + self.buff_size] = time_stamp
        self.buff_value[index + self.buff_size] = value

        self.buff_counter += 1
        return self.buff_counter

        
        
    def read_ring_buffer(self):
        """
        Read the last N values from the ringBuffer
        
        Returns:
        timestamp_array(numpy.array [N,1]) of timestamps
        values_array(numpy.array [N,1]) of values
        """
        max_rows = min(self.buff_size, self.buff_counter)
        index = int(self.buff_counter%self.buff_size)
        return (self.buff_timestamp[(index+self.buff_size - max_rows):(index+self.buff_size)],
                self.buff_value[(index+self.buff_size - max_rows):(index+self.buff_size)])
        

    def default_callback(self, sender, data:bytearray ):  
        """
        The default callback function for the device. The callback function is passed a bytearray with the
        bluetooth packet received from the device. This function then processes and decodes the packet 
        and extracts the data.
        
        Parameters:
        sender(str): a string describing the sender
        data(bytearray): the packet data
        
        Returns:
        good_readings(int): the number of good readings received
        """
        time_stamp = np.datetime64(datetime.datetime.now(),'ms')
        if (data[0] == 0xcf):   # This is a weight measurement
            self.number_readings += 1
            print('{} - '.format(sender, data), end='')
            self.data_list.append(data)
            data_point = [int(b) for b in data]

            # array indices of data in raw_data_point
            WEIGHT_H = 4
            WEIGHT_L = 5
            BODY_FAT_H = 6
            BODY_FAT_L = 7
            BONE_MASS = 8
            MUSCLE_MASS_H = 9
            MUSCLE_MASS_L = 10
            VISCERAL_FAT = 11
            WATER_H = 12
            WATER_L = 13
            CALORIES_H = 14
            CALORIES_L = 15    
            
            # Calculations based on mySignals code

            weight = (data_point[WEIGHT_H]*256 + data_point[WEIGHT_L])/10

            body_fat_percentage = (data_point[BODY_FAT_H]*256 + data_point[BODY_FAT_L])/10

            bone_mass_percentage = data_point[BONE_MASS]*100/weight

            muscle_mass_percentage = (data_point[MUSCLE_MASS_H]*256 + data_point[MUSCLE_MASS_L])/10

            visceral_fat_percentage = data_point[VISCERAL_FAT]

            water_percentage = (data_point[WATER_H]*256 + data_point[WATER_L])/10

            calories = (data_point[CALORIES_H]*256 + data_point[CALORIES_L])/10
            
            
            if weight > 20 and weight <250:
                self.good_readings += 1
                print('\nGood readings: {} ({})'.format(self.good_readings, self.number_readings))

            print('\n')   
            print('Weight:            {}'.format(weight))
            print('Body fat %:        {}'.format(body_fat_percentage))
            print('Bone mass %:       {}'.format(bone_mass_percentage))
            print('Muscle mass %:     {}'.format(muscle_mass_percentage))
            print('Visceral fat %:    {}'.format(visceral_fat_percentage))
            print('Body water %:      {}'.format(water_percentage))
            print('Calories Kcal:     {}'.format(calories))

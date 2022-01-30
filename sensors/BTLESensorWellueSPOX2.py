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

        
class BTSensorWellueSPOX():
    """
    Class to manage the full connection to a bluetooth device using the bleak library.
    """

    import numpy as np

    # Global class variables
    scanner_instance = None
    btle_name = None
    btle_addr = None
    device_service_number = 26   # This is from the reverse engineering
    client = None
    found_device = None
    services = None
    good_readings = 0
    number_readings = 0

    loop_counter = 0
    
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


    def __init__(self, btle_name=None, btle_addr=None, device_name=None, device_id=None,
                        scanner_instance=None, reading_timeout=20):
        """
        Constructor function that initializes the object variables.
        
        Parameters:
        btle_name(str): the name of the bluetooth device
        btle_addr(str): the bluetooth address or UUID of the bluetooth device
        scanner_instance(obj): a pointer to the btle scanner to access the list of devices
        emulation_mode(boolean): run in emulation mode if true
        """

        print('{}:: Initializing instance of BTSensorWellueSPOX'.format(btle_name))
        # First check that required parameters are present
        if (((not btle_name == None) or (not btle_addr == None))
                and (not device_id == None)
                and (not scanner_instance == None)):
            self.btle_name = btle_name   # set the class variable device name
            self.init_ring_buffer(300)       # create the ring buffer for the pleth at 30Hz this is 10 seconds
            self.good_readings = 0           # reset for multiple calls
            self.device_id = device_id
            if device_name:
                self.device_name = device_name
            else:
                self.device_name = btle_name
            self.scanner_instance = scanner_instance
            self.stop_reading_flag = False   # flag to interrupt the reading cycle
            self.reading_timeout_sec = reading_timeout  # the timeout of the reading cycle

            # set the status to initialized and send it back to the app
            self.init_results_dict()

        else:
            print("{}:: Error no device name specified".format(btle_name))
            print('btle_name: {}'.format(btle_name))
            print('btle_addr: {}'.format(btle_addr))
            print('device_id  : {}'.format(device_id))
            print('device_name: {}'.format(device_name))
            print('scanner_instance: {}'.format(scanner_instance))

    def reset_variables(self):
        """Method to reset variables and ring buffer"""
        self.init_results_dict()
        self.init_ring_buffer(300)
        self.good_readings = 0


    def init_results_dict(self):
        """Simple method to reset and initialize the results_dict"""
        self.results_dict = {}
        # These are standard across all sensors
        self.results_dict['device_id'] = self.device_id
        self.results_dict['btle_name'] = self.btle_name
        self.results_dict['status'] = 'Initialized'
        self.results_dict['message'] = ''
        self.results_dict['finalized'] = False
        self.results_dict['connected'] = False
        # These are unique to the sensor
        self.results_dict['data'] = {}
        self.results_dict['data']['spo2'] = 0
        self.results_dict['data']['pulse'] = 0 
        self.results_dict['data']['timestamp'] = 0        
        self.results_dict['data']['good_readings'] = 0
        self.results_dict['data']['total_readings'] = 0


    def get_status(self):
        status_dict = {}
        status_dict['scanner_instance'] = ('{}'.format(self.scanner_instance) 
                                            if self.scanner_instance
                                            else 'None')
        status_dict['btle_name'] = self.btle_name
        status_dict['client'] = 'Connected' if self.client else 'None'
        status_dict['found_device'] = True if self.found_device else False
        status_dict['loop_counter'] = self.loop_counter
        status_dict['state'] = self.state

        # status_dict[''] = 

        # Add more here 
        
        return status_dict


    def start_reading(self):
        if self.state == self.STATE_DORMANT:
            self.client = None
            self.reset_variables()
            self.state = self.STATE_CONNECTING
            self.stop_reading_flag = False
            print('{} Entering into connecting state'.format(self.btle_name))
        else:
            print('{} ERROR:: Cannot enter into connecting state - existing state is {}'.format(self.btle_name, self.state))

    def stop_reading(self):
        if self.state == self.STATE_CONNECTING:
            self.state = self.STATE_DORMANT
            print('{} Entering into dormant state - existing state is {}'.format(self.btle_name, self.state))

            self.found_device = False

        elif self.state == self.STATE_READING:
            self.stop_reading_flag = True

        else:
            print('{} ERROR:: Cannot enter into dormant state - existing state is {}'.format(self.btle_name, self.state))

    def get_results(self):
        return self.results_dict
    
    def find_device(self, device_list, name=None, addr=None):
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
                if name:
                    if re.search(name,device.name, flags=re.IGNORECASE):
                        print('{}:: Found device with name: {}'.format(self.btle_name, device.name))
                        found_device_list.append(device)
                        # set the status to scanning and send it back to the app
                        self.results_dict['status'] = 'DeviceFound'   
                else:
                    if re.search(addr,device.address, flags=re.IGNORECASE):
                        print('{}:: Found device with address: {}'.format(self.btle_addr, device.address))
                        found_device_list.append(device)
                        # set the status to scanning and send it back to the app
                        self.results_dict['status'] = 'DeviceFound'  
        except Exception as e:
            print('{}:: ERROR in find_device - device_list is probably invalid'.format(self.btle_name))                 

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
            if self.btle_name:
                found_device_list = self.find_device(device_list,name=self.btle_name) # search for the device
            else:
                found_device_list = self.find_device(device_list,addr=self.btle_addr) # search for the device

            if len(found_device_list) > 0:  # a device was found
                print("{}:: Bluetooth devices found with name: {}".format(self.btle_name,self.btle_name))
                self.found_device = found_device_list[0] # If there are multiple devices use the first one
                print('{}:: name: {}  btle address: {}'.format(self.btle_name,
                            self.found_device.name, self.found_device.address))
            else:
                return False  # no device was found - return
        else:
            print('Device already registered')
            print(self.found_device)
            
        if not self.client:
            print('Creating BTLE client....')

            # set the status to scanning and send it back to the app
            self.results_dict['status'] = 'Connecting'

            print('{}:: Connecting to device with address: {}'.format(self.btle_name, 
                                                                        self.found_device.address))
            try:                                                          
                self.client = bleak.BleakClient(self.found_device.address)
            except Exception as e:
                print('{}:: ERROR connecting to bleak.BleakClient-address: {}'.format(self.btle_name, 
                                                            self.found_device.addr))

                if self.client:
                    await self.client.disconnect()

                self.client = False

                return False

           
        else:
            print('Using existing client')

        # Connect to the bluetooth device
        if not self.client.is_connected:
            try:   
                await self.client.connect()
            except Exception as e:
                print('{}:: ERROR could not connect to btle client'.format(self.btle_name,
                                                                    self.client))
                await self.client.disconnect()
                self.results_dict['connected'] = False
                await asyncio.sleep(1)
                self.client = False
                return False

            if self.client.is_connected:
                print('{}:: Successfully connected to btle client')
                # set the status to connected and send it back to the app
                self.results_dict['status'] = 'Connected'
                self.results_dict['connected'] = True
                self.results_dict['completed'] = False
        else:
            print('{}:: Using existing connection to client'.format(self.btle_name))
            # set the status to connected and send it back to the app
            self.results_dict['status'] = 'Connected'
            self.results_dict['connected'] = True
            self.results_dict['completed'] = False
        
        return self.client.is_connected




    async def loop(self, initial_state=STATE_DORMANT):
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
                    print('{}:: device found and connected'.format(self.btle_name))
                    print('{}:: entering READ state.....'.format(self.btle_name))
                    self.reset_variables()
                    self.state = self.STATE_READING  # advance the state

            elif self.state == self.STATE_READING:

                result, msg = await self.get_readings(self.device_service_number, 
                                                        callback=None, num_readings=7)
                self.results_dict['message'] = msg
                if result == 1:
                    print('{}:: Successfully completed readings'.format(self.btle_name))
                    self.state = self.STATE_DORMANT
                    print('{}:: Transitioning to state: {}'.format(self.btle_name, self.state))
                elif result == -1:      # timeout error
                    print('{}:: Problem with readings: {}'.format(self.btle_name, msg))
                    self.state = self.STATE_CONNECTING
                elif result == -2:      # stop_signal
                    print('{}:: Problem with readings: {}'.format(self.btle_name, msg))
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
                print('{}:: Client is connected....disconecting'.format(self.btle_name))
                while self.client.is_connected:
                    print('{}:: Disconnecting from btle device'.format(self.btle_name))
                    await self.client.disconnect()
                # set the status to connected and send it back to the app
                self.results_dict['status'] = 'Disconnected'
                self.results_dict['connected'] = False
                print('{}:: BTLE Client is disconnected'.format(self.btle_name))
                self.client = None
                self.found_device = False
                self.state = self.STATE_DORMANT

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
        self.results_dict['status'] = 'Reading'

        return True
        
    async def stop_notify(self, service_num):
        """
        Method to disconnect from a notify service
        """
        await self.client.stop_notify(service_num)
        self.results_dict['status'] = 'Connected'

        return True


    def check_stop_reading_flag(self):
        """Method to safely stop the reading loop and reset the flag"""
        if self.stop_reading_flag:
            self.stop_reading_flag == False
            return True
        return False


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
            await self.client.start_notify(service_num, cb)
        except Exception as e:
            print('{}:: ERROR with client.start_noitify service_num={} callback={}'
                        .format(self.btle_name, service_num, cb))
        else:
        
            # set up the timeout trigger
            time_out = datetime.datetime.now() + datetime.timedelta(0,self.reading_timeout_sec)
            loop_flag = True

            while loop_flag:
                if self.good_readings >= num_readings:
                    loop_flag = False
                    return_code = 1
                    return_msg = 'Success with {} readings'.format(num_readings)
                    print('{}:: Successful sensor reading'.format(self.btle_name))
                elif datetime.datetime.now() > time_out:
                    loop_flag=False
                    return_msg = 'Timeout'
                    print('{}:: Timeout in sensor reading'.format(self.btle_name))
                    return_code = -1
                elif self.check_stop_reading_flag():
                    loop_flag=False
                    return_msg = 'Stop reading signal'
                    print('{}:: Sensor reading interrupted with stop_reading signal'.format(self.btle_name))
                    return_code = -2
                else:
                    await asyncio.sleep(.5)
                    print('{}:: mainloop :: sleep cycle - good_readings {}'.format(self.btle_name,
                                                                            self.good_readings ))
            
            print('{}:: mainloop -stopping notify'.format(self.btle_name))

            # Unsubscribe from notifications
            try:
                await self.client.stop_notify(service_num)
                await asyncio.sleep(1)
            except Exception as e:
                print('{}:: ERROR failed in unsubscribe from notify'.format(self.btle_name))
                print(e)

        if return_code == 1:
            self.results_dict['status'] = 'Completed'
            self.results_dict['finalized'] = True
        else:
            self.results_dict['status'] = 'Failed'
            self.results_dict['finalized'] = False

        try:
            print('{}:: disconnecting from btle client'.format(self.btle_name))
            await self.disconnect()
            await asyncio.sleep(1)
        except Exception as e:
                print('{}:: ERROR failed in btle lient disconnect'.format(self.btle_name))
                print(e)
        else:
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

        # first check what kind of message this is 
        if (data[0] == 0xfe) and (data[1] == 0x0a):   # This is a SPO2 and pulse rate message

            spox_results_dict = {}
            self.number_readings += 1 #increment the reading counter
            print('{} - '.format(sender, data), end='')

            self.data_list.append(data)   # append the data on list (for averages later)

            # This section decodes the data from hexadecimal into decimal and binary and prints
            # the values to the console
            int_data = []
            # print the simple hex string
            for b in data:
                int_data.append(b)
                print('{:02x}:'.format(b), end='')
           
            print()
            # print the hex, decimal and binary values of each byte
            for b in data:
                print('{}({})[{:b}] '.format(hex(b), b, b), end='')
            
            # save the latest pulse and spo2 values to variables
            pulse = int(data[4])
            spo2 = int(data[5])

           
            print('#### Pulse: {}  SPO2: {}'.format(pulse,spo2))


            # simple tests to ensure the readings are "good"
            if pulse > 20 and pulse <110:
                if spo2 > 50 and spo2 <=100:
                    self.good_readings += 1
                    print('\nGood readings: {} ({})'.format(self.good_readings, self.number_readings))

            print('\n')   
            # Update the device status dict
            self.results_dict['status'] = 'Reading'
            self.results_dict['data']['spo2'] = spo2
            self.results_dict['data']['pulse'] = pulse   
            self.results_dict['data']['timestamp'] = datetime.datetime.now()   
            self.results_dict['data']['good_readings'] = self.good_readings
            self.results_dict['data']['total_readings'] = self.number_readings
        
            return self.good_readings

           
            
        elif  (data[0] == 0xfe) and ((data[1] == 0x08) or (data[1] == 0x09)):  # this is a pleth message
            # parse the message            
            pleth = float(data[3])
            
            # add to ring buffer
            total_pleth_readings = self.add_to_ring_buffer(time_stamp, pleth)

            self.results_dict['data']['total_pleth_readings'] = total_pleth_readings
          

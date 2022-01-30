###################################################
#   Bluetooth Low Energy Sensor Class
#   based on the Bleak BTLE framework
#   by Marc van Zyl
###################################################

# for reverse engineering approach see the notebook at:
# https://drive.google.com/file/d/1-Vr0NEy-ypGBnR2Ukwu7-xShxoJlw1Do/view?usp=sharing

import asyncio
from app import CONNECTING
import bleak
import re
import numpy as np
import datetime

        
class BTSensorDummy():
    """
    Class to manage the full connection to a bluetooth device using the bleak library.
    """

    import numpy as np


    # loop state machine variables
    STATE_DORMANT = 0
    STATE_CONNECTING = 1
    STATE_READING = 2




    

    def __init__(self, device_name=None, device_addr=None, device_id=None,
                        scanner_instance=None, reading_timeout=10,
                        emulation_mode=False, config=False):
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
                and (not scanner_instance == None)):
            self.device_name = device_name   # set the class variable device name
            self.good_readings = 0           # reset for multiple calls
            self.device_id = device_id
            self.scanner_instance = scanner_instance
            self.stop_reading_flag = False   # flag to interrupt the reading cycle
            self.reading_timeout_sec = reading_timeout  # the timeout of the reading cycle

            # set the status to initialized and send it back to the app
            self.init_results_dict()

            self.con = config

            self.client = None
            self.found_device = None
            self.loop_counter = 0
            self.force_exit_flag = False
            self.state = self.STATE_DORMANT  # main state variable
            # this is the results dict that the flask server has access to
            self.results_dict = {}
            self.readings = 0

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
        self.results_dict['data']['spo2'] = 0
        self.results_dict['data']['pulse'] = 0 
        self.results_dict['data']['good_readings'] = 0
        self.results_dict['data']['total_readings'] = 0


    def get_status(self):

        status_dict = {}
        status_dict['device_name'] = self.results_dict['device_id']
        status_dict['scanner_instance'] = ('{}'.format(self.scanner_instance) 
                                            if self.scanner_instance
                                            else 'None')
        status_dict['device_name'] = self.device_name
        status_dict['client'] = 'Connected' if self.client else 'None'
        status_dict['found_device'] = True if self.found_device else False
        status_dict['loop_counter'] = self.loop_counter
        status_dict['state'] = self.state

        # status_dict[''] = 

        # Add more here 
        
        return status_dict


    def start_reading(self):
        if self.state == self.STATE_DORMANT:
            self.reset_variables()
            self.state = self.STATE_CONNECTING
            self.reading_start_time = datetime.datetime.now()  #  Get the start reading time
            print('{} Entering into connecting state'.format(self.device_name))
        else:
            print('{} ERROR:: Cannot enter into connecting state - existing state is {}'.format(self.device_name, self.state))

    def stop_reading(self):
        if self.state in [self.STATE_CONNECTING, self.STATE_READING]:
            self.state = self.STATE_DORMANT
            print('{} Entering into dormant state'.format(self.device_name))
        else:
            print('{} ERROR:: Cannot enter into dormant state - existing state is {}'.format(self.device_name, self.state))

    def get_results(self):

        print('State:: {}'.format(self.state))

        if self.state == self.STATE_DORMANT:
            results_dict = { "device_id": self.device_id, 
                            "device_name": self.device_name, 
                            "status": "Initialized", 
                            "state":0,
                            "message": "", 
                            "finalized": False, 
                            "connected": False, 
                            "data": { "spo2": 0, 
                                      "pulse": 0, 
                                      "good_readings": 0, 
                                      "total_readings": 0 } 
                            }
            return results_dict

        # into state = 1 connecting
        elif self.reading_start_time + datetime.timedelta(seconds=self.con['find_delay']) >  datetime.datetime.now():


            results_dict = { "device_id": self.device_id, 
                            "device_name": self.device_name, 
                            "status": "Initialized", 
                            "state":1,
                            "message": "", 
                            "finalized": False, 
                            "connected": False, 
                            "data": { "spo2": 0, 
                                    "pulse": 0, 
                                    "good_readings": 0, 
                                    "total_readings": 0 } }
            return results_dict

        # into device found trying to connect - conecting phase
        elif self.reading_start_time + datetime.timedelta(seconds=self.con['connect_delay']) >  datetime.datetime.now():
            
            results_dict = { "device_id": self.device_id, 
                            "device_name": self.device_name, 
                            "status": 'Connecting....', 
                            "state":1,
                            "message": "", 
                            "finalized": False, 
                            "connected": False, 
                            "data": { "spo2": 0, 
                                    "pulse": 0, 
                                    "good_readings": 0, 
                                    "total_readings": 0 } }
            return results_dict

        # into device found trying to connect - conecting phase
        elif self.reading_start_time + datetime.timedelta(seconds=self.con['read_delay']) >  datetime.datetime.now():
            
            results_dict = { "device_id": self.device_id, 
                            "device_name": self.device_name, 
                            "status": 'Connecting....', 
                            "state":1,
                            "message": "", 
                            "finalized": False, 
                            "connected": False, 
                            "data": { "spo2": 0, 
                                    "pulse": 0, 
                                    "good_readings": 0, 
                                    "total_readings": 0 } }
            return results_dict

        # into device connected staring read
        elif self.reading_start_time + datetime.timedelta(seconds=self.con['read_complete_delay']) >  datetime.datetime.now():

            self.readings = int((datetime.datetime.now() 
                        - self.reading_start_time - datetime.timedelta(seconds=self.con['read_delay'])).total_seconds())

            if self.readings % 2:  # this oscillates between the two readings
                results_dict = { "device_id": self.device_id, 
                                "device_name": self.device_name, 
                                "status": 'Connected....', 
                                "state":2,
                                "message": "", 
                                "finalized": False, 
                                "connected": True, 
                                "data": { "spo2": 99, 
                                        "pulse": 62, 
                                        "good_readings": self.readings, 
                                        "total_readings": self.readings } }
            else:
                results_dict = { "device_id": self.device_id, 
                                "device_name": self.device_name, 
                                "status": 'Connected....', 
                                "state":2,
                                "message": "", 
                                "finalized": False, 
                                "connected": True, 
                                "data": { "spo2": 98, 
                                        "pulse": 63, 
                                        "good_readings": self.readings, 
                                        "total_readings": self.readings } }
            return results_dict

        # readings complete  disconnect_delay
        elif self.reading_start_time + datetime.timedelta(seconds=self.con['disconnect_delay']) >  datetime.datetime.now():
            results_dict = { "device_id": self.device_id, 
                            "device_name": self.device_name, 
                            "status": 'Connected....', 
                            "state":2,
                            "message": "", 
                            "finalized": True, 
                            "connected": True, 
                            "data": { "spo2": 98, 
                                    "pulse": 63, 
                                    "good_readings": self.readings, 
                                    "total_readings": self.readings } }
            return results_dict

        else:

            results_dict = { "device_id": self.device_id, 
                            "device_name": self.device_name, 
                            "status": 'Disconnected....', 
                            "state":1,
                            "message": "", 
                            "finalized": True, 
                            "connected": False, 
                            "data": { "spo2": 98, 
                                    "pulse": 63, 
                                    "good_readings": self.readings, 
                                    "total_readings": self.readings } }
            return results_dict
    

    def reset_variables(self):
        self.init_results_dict()
        self.readings = 0
        
    async def loop(self, initial_state=STATE_DORMANT):
        """The main loop method the implements the BTLE reader finite state machine.
        """
        self.state = initial_state

        while not self.force_exit_flag:  # this allow for the loop to be terminated
            ## Finite State Machine
            self.loop_counter += 1         # this a counter to keep track of the heartbeat

            await asyncio.sleep(0.5)

    def check_stop_reading_flag(self):
        """Method to safely stop the reading loop and reset the flag"""
        if self.stop_reading_flag:
            self.stop_reading_flag == False
            return True
        return False





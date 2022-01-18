###################################################
#   Bluetooth Low Energy Sensor Class
#   based on the Bleak BTLE framework
#   by Marc van Zyl
###################################################

import time
import bleak
import re

import numpy as np
import datetime
import asyncio


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
    
    
    def __init__(self, address):
        """Object initialization method.
        
        Parameters:
        address: the MAC address or the UUID of the bluetooth device - not used in emulation
        
        Returns:
        None"""
        self.initialized = True
        self.address = address
        print("fakeClient :: initialized to address {}".format(self.address))

    def discover(self):    
        ### fake device
        time.sleep(2)

        devices = [{'name':'VTM 20F',
                    'address':'4049E3BE-AF4C-4BCB-AFB4-E6F1F5158595',
                    'rssi':-99
                },
                  {'name':'VTM 21F',
                    'address':'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
                    'rssi':-99
                }]
        return devices


class BTLEScanner():
    """
    Class to manage the full connection to a bluetooth device using the bleak library.
    """

    import time 

    # Static class variables - becuase they are created outside of the initialization
    service_name = ''
    found_devices = True
    new_scan = False      # flag to indicate new scan has completed
    devices = []
    running = False
    verbose=True
     
    # this is the results dict that is passed back in the guiCallback
    ui_callback_dict = {}

    def __init__(self, service_name=None, uiCallback=None, 
                       emulation_mode=False, verbose=True):
        """
        Constructor function that initializes the object variables.
        
        Parameters:
        device_name(str): the name of the bluetooth device
        uiCallback(function): the callback function that is used to return the values to the application
         """

        # First check that both parameter are present
        if (not service_name == None):
            self.service_name = service_name # store the service_name in a class variable
            self.uiCallback = uiCallback     # store the uiCallback in a class variable
            self.running = True              # this is the flag to terminate the thread
            self.verbose = verbose
            if emulation_mode:
                self.emulation_mode = True
                self.fake_client = fakeClient('4049E3BE-AF4C-4BCB-AFB4-E6F1F5158595')

            else:
                self.emulation_mode = False
        else:
            print("{}:: Error no device name specified".format(self.service_name))

        # set the status to initialized and send it back to the app
        if (not self.uiCallback == None):
            self.ui_callback_dict.clear()
            self.ui_callback_dict[self.service_name] = {}
            self.ui_callback_dict[self.service_name]['status'] = 'Initialized....'
            self.ui_callback_dict[self.service_name]['connected'] = False

            print("{}:: Set up callback to: {}".format(self.service_name,self.uiCallback))
            # send the message
            self.uiCallback(self.ui_callback_dict)

    def terminate(self):
        self.running = False   
        print('{}:: Teminating '.format(self.service_name))  


    def scan(self):
        """
        Requests a scan of all bluetooth devices in advertising mode.

        Prameters: 
        None

        Returns:
        device_list(list): list of Bleak.device objects (one for each found device)
        """

        while self.running:
            print("{}:: Starting scan for bluetooth devices".format(self.service_name))
            # set the status to scanning and send it back to the app
            if (not self.uiCallback == None):
                self.ui_callback_dict[self.service_name]['status'] = 'Scanning....'
                self.uiCallback(self.ui_callback_dict)

            devices = None

            if not self.emulation_mode:
                devices = asyncio.run( bleak.discover() )  # Bleak command
            else:
                devices = self.fake_client.discover()


            device_list = []

            # Unpack the Bleak.devices object into a list of Bleak.device
            if devices:
                for d in devices:
                    if (not self.emulation_mode) and self.verbose:
                        print(d, d.rssi)   # print the RSSI to the console for fun
                    device_list.append(d)
                
                # update the class variable
                self.devices = devices
                self.found_devices = True
            else:
                self.devices = []
                self.found_devices = False

            print("{}::End scan for bluetooth devices".format(self.service_name))
            # set the status to scanning and send it back to the app
            if (not self.uiCallback == None):
                self.ui_callback_dict[self.service_name]['status'] = 'Scanning....'
                self.uiCallback(self.ui_callback_dict)

            print("{}:: Sleeping".format(self.service_name))
            time.sleep(2)

        return 1
           


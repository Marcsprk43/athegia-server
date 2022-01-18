import asyncio
import bleak
import re

import numpy as np

import datetime


async def scan():
    devices = await bleak.discover()
    
    device_list = []
    
    for d in devices:
        print(d, d.rssi)
        device_list.append(d)
    return device_list


def find_device(device_list, name):
    found_device_list = []
    for device in device_list:
        if re.search(name,device.name, flags=re.IGNORECASE):
            found_device_list.append(device)
    return found_device_list

async def main_func():    
    devices = await bleak.discover()
    print(devices)

    found_devices = find_device(devices, 'Electronic Scale')

    if len(found_devices):
        device = bleak.BleakClient(found_devices[0])


        print('Connecting')
        await asyncio.sleep(3)
        await device.connect()

        print('rssi =  {}'.format(await device.get_rssi()))

        print('getting services')

        services = await device.get_services()

        for key in services.characteristics.keys():

            print('{} : {}  {} {}'.format(key,services.get_characteristic(key).description,
                                    services.get_characteristic(key).properties,
                                    services.get_characteristic(key).uuid))

        print('Sleeping for 4 seconds')
        time.sleep(4)   # from arduio code

        user_byte0 = 0xfe      # start byte
        user_group = 1         # user group
        user_gender = 1        # gender: 1=male, 0=female
        user_level = 0         # level 0=normal
        user_height = 180      # height in cm
        user_age = 54          # age
        user_unit = 1          # return units in kg
        user_xor = 0

        scale_user_profile = bytearray([user_byte0,
                                        user_group,
                                        user_gender,
                                        user_level,
                                        user_height,
                                        user_age,
                                        user_unit,
                                        user_xor])


        # calculate the XOR checksum
        for ind in range(1,7):
            print('{:08b}  {:08b}'.format( scale_user_profile[7], scale_user_profile[ind]))
            scale_user_profile[7] = scale_user_profile[7] ^ scale_user_profile[ind]


        if device.is_connected:
            print('writing to gatt char')
            await device.start_notify('0000fff4-0000-1000-8000-00805f9b34fb', callback)

        else:
            print('Could not connect to scale')


        print('Sleeping for 1 seconds')
        time.sleep(1)   # from arduio code
        
        await device.write_gatt_char('0000fff1-0000-1000-8000-00805f9b34fb', scale_user_profile)  # initialize

        

        for i in range(20):
            print('{} .. '.format(i))
            await asyncio.sleep(1)   # from arduio code


        print('Disconnecting....')
        await device.disconnect()

    else:
        print('Device not found!')

if __name__ == '__main__':
    asyncio.run(main_func())
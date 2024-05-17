# Athegia: At-Home Medical Monitoring System for Senior Citizens

**By Marc van Zyl**  
**McIntosh High School (11th Grade)**  
**May 2022**

## Overview

Athegia is an innovative at-home medical monitoring system designed to help senior citizens with chronic conditions monitor their health metrics easily and consistently. By integrating multiple low-cost Bluetooth-enabled sensors, Athegia collects biometric data and securely stores it in a cloud-based platform for analysis by healthcare professionals.

## Impact

Chronic diseases are a significant health burden, especially for senior citizens. Athegia addresses this by providing a simple, non-app-based solution that encourages regular monitoring through habit stacking, ultimately aiming to reduce hospitalizations and improve the quality of life for seniors.

## Device overview

## Device Overview

Athegia consists of a physical prototype, Bluetooth server software, a graphical user interface, and a cloud analytics platform. The physical device houses a Raspberry Pi and a touchscreen, and it connects to various Bluetooth biometric sensors. The server software manages data collection from these sensors and communicates with the cloud platform. The GUI allows users to interact with the system, while the cloud analytics platform stores and processes the data for healthcare professionals.

## Installation Instructions

First, connect any display to a raspberry pi. 

Inside of the Models folder I have uploaded a 3D-printed housing for the Pi and the screen, though you may use any that work for you.

You will need to install [NodeJS](https://nodejs.org/en/download/package-manager) and [Angular](https://angular.io/guide/setup-local) for the frontend interface.

Clone this repository into the Documents folder. Do the same with the [athegia-frontend](https://github.com/Marcsprk43/athegia-frontend) repository. 

Here you will need to make a FireStore database and provide the OAuth keys to the database service JSON.

Next, we need to setup the auto-start on boot. There are many ways to do this, but after much trial and error, I found that this way worked for me:

Enable autologin to pi user if already not. In addition, since you will not be able to easily access the pi once the autostart is in place, you can enable SSH through this same menu
Run: sudo raspi-config
Choose option: 1 System Options
Choose option: S5 Boot / Auto Login
Choose option: autologin to pi user
Select Finish, and reboot the Raspberry Pi.

Copy autostart folder in /home/pi/.config folder. ".config" is a hidden folder in /home/pi/

Restart the pi and let it boot!

Currently, only 4 devices are supported (one of which I created myself and cannot be bought). Support for more would be greatly appreciated!

## Prototypes

### Physical Prototype

#### Prototype 1

- **Description:** Basic enclosure for Raspberry Pi and touchscreen.
- **Materials:** Raspberry Pi, Raspberry Pi touchscreen, 3D PLA material.
- **Evaluation:** Functional but lacks aesthetic appeal and proper connector placement.

#### Prototype 2

- **Description:** Enhanced design for demonstration purposes.
- **Materials:** Same as Prototype 1 with improved layout.
- **Evaluation:** Simple and functional but aesthetically unappealing.

#### Prototype 3

- **Description:** Clean and simple design with no bezel and rounded edges.
- **Materials:** 3D PLA material, Raspberry Pi, touchscreen, power cord.
- **Evaluation:** Positive feedback from users and healthcare professionals.

### Bluetooth Server Software

#### Reverse Engineering Process

- **Tools Used:**
  - Wireshark for Bluetooth sniffing.
  - Python libraries: Bleak, Asyncio, Numpy, Pandas, Matplotlib.
- **Devices:**
  - Berrymed Pulse Oximeter
  - Wellue Pulse Oximeter
  - PT3SBT Non-contact thermometer
  - MySignals Body composition scale
  - Beurer BF70 Body Fat Scale
  - Contact Bluetooth Thermometer
  - Full Automatic Blood Pressure Monitor

#### Developing the Python Bluetooth Server

- **Iteration 1: Framework Creation**
  - Developed `BTLEScanner` and `BTLESensor` classes.
  - Implemented a simple Flask web server for communication.
- **Iteration 2: Multiple Devices with Asyncio**
  - Managed multiple devices using asynchronous coroutines.
- **Iteration 3: Improved Thread Management**
  - Addressed issues with coroutine management by using individual threads.
- **Iteration 4: Final Refinements**
  - Added sleep functions for stability.
  - Integrated secure data transmission to Google Cloud Platform.

### Graphical User Interface

#### Version 1: PySimpleGUI

- **Goal:** Simple GUI for testing.
- **Features:** Weather station view, sensor readings.
- **Evaluation:** Easy to code but limited in functionality and layout management.

#### Version 2: Angular

- **Goal:** Robust and dynamic GUI using Angular.
- **Features:** Weather station landing page, sensor readings, customizable landing pages.
- **Evaluation:** Positive feedback, highly functional and extendable.

### Cloud Analytics Platform

- **Platform:** Google Cloud Platform (GCP)
- **Components:**
  - **Data Storage:** Firestore database for secure data storage.
  - **Analytics:** BigQuery for data analysis, integrated with Google DataStudio.
  - **Data Upload:** Custom Google Cloud Function to handle data upload via HTTP POST requests.

## Conclusion

Athegia successfully integrates multiple Bluetooth sensors into a single, user-friendly platform that encourages consistent health monitoring for seniors. The device's design, combined with its cloud-based analytics and habit-stacking approach, has the potential to significantly reduce hospitalizations and improve the quality of life for chronic disease patients.

## Future Work

- **Pilot Testing:** Produce 50-100 devices for real-user testing.
- **Software Review:** Engage security experts to validate stability and security.
- **Feature Expansion:** Add support for additional Bluetooth devices and more customizable landing page options.

## Appendices

### Inspiration

The inspiration for Athegia stemmed from a noticeable gap in the current landscape of medical technology. While there are numerous app-based solutions for health monitoring, many of these are not user-friendly for senior citizens. According to the Pew Research Center, only 61% of senior citizens own a smartphone, and many find app interfaces confusing and difficult to navigate. This presents a significant barrier to consistent health monitoring for seniors with chronic diseases.Chronic diseases account for 70% of all deaths in the US, with senior citizens being the most affected. Despite the availability of advanced biometric sensors, seniors often struggle to use multiple apps to monitor their health metrics. I witnessed this firsthand with my grandmother, who found it challenging to take consistent, accurate readings from various health devices post-surgery.Athegia was developed to address this gap by creating a simple, non-app-based platform that integrates multiple Bluetooth sensors into one user-friendly device. This system leverages habit stacking, a proven behavioral design technique, to encourage regular monitoring, thereby aiming to reduce hospitalizations and improve the overall quality of life for senior citizens with chronic conditions.

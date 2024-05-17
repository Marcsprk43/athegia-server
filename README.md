# Athegia: At-Home Medical Monitoring System for Senior Citizens

**By Marc van Zyl**  
**McIntosh High School (11th Grade)**  
**May 2022**

## Overview

Athegia is an innovative at-home medical monitoring system designed to help senior citizens with chronic conditions monitor their health metrics easily and consistently. By integrating multiple low-cost Bluetooth-enabled sensors, Athegia collects biometric data and securely stores it in a cloud-based platform for analysis by healthcare professionals.

## Impact

Chronic diseases are a significant health burden, especially for senior citizens. Athegia addresses this by providing a simple, non-app-based solution that encourages regular monitoring through habit stacking, ultimately aiming to reduce hospitalizations and improve the quality of life for seniors.

## Components

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

### Background Research

[Details on chronic disease statistics, the problem with current monitoring systems, and the market analysis.]

### Reference List

[A complete list of references and resources used in the development of Athegia.]

---

## Suggestions for Images

1. **Physical Prototype Section:**
   - Prototype 1, 2, and 3 images showing the design evolution.
2. **Bluetooth Server Software:**
   - Diagrams of the server architecture and workflow.
3. **Graphical User Interface:**
   - Screenshots of PySimpleGUI and Angular versions.
4. **Cloud Analytics Platform:**
   - Diagrams showing data flow from device to GCP.

These images will help illustrate the progress and functionality of Athegia, making the README more engaging and informative.

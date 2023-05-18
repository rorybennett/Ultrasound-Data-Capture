# Ultrasound Data Capture

Grab frames from an ultrasound system display port and sync with IMU (inertial measurement unit) data.
This project was created as part of continuing research into volume estimation based on
ultrasound images and orientation data. This project is designed to run on a Windows laptop.

## Hardware Considerations

This project was compiled with specific hardware in mind, but it is not entirely limited to the hardware
used. There are 2 devices (beyond the computer used to run the software) that are needed:

1. A video signal source.
2. A bluetooth IMU device.

### 1. Video Signal Source

The format of the video signal should not matter, as long as it is converted to a USB signal
(e.g. HDMI/DVI/VGA-to-USB). If the program is run on a system with a webcam, the webcam can be used
as a video signal source.

During testing a Canon Aplio i700's HDMI output was used as the video signal source, as well as various
easily available video sources (laptops, computers, etc.).

### 2. Bluetooth IMU

This project makes the assumption that a WITMOTION IMU is available, and is set up to connect to,
and communicate with, such an IMU.

WITMOTION has a range of sensors, and not all of them may work with this software.

During testing the
[BWT901CL 9-axis](https://www.wit-motion.com/9-axis/witmotion-bluetooth-2-0-mult.html)
bluetooth sensor was used.

## Overview of Program Functionality

### Basic Operation: Video Source Connection

To connect to a video signal select: 'Signal Source' -> 'Connect to Source' -> '#'.

The program will attempt to connect to a video signal at '#' if it is available.
At the time of writing there was no sure-fire way of naming the signal sources.
'0' was normally the webcam (laptop) and ' # > 0 ' was for signals coming through a USB port.

The dimensions of the video signal are initially set to 1920x1080 (full HD) and if that is not possible
(according to OpenCV) then some other default dimension is used. The dimension used is displayed on the
screen below the signal display. This dimension is the dimension that the images are saved as. If the
signal dimension is 1920x1080, then the saved .png images will be 1920x1080 images. The dimensions can
also be changed to varying values in the 'Signal Source' -> 'Change Signal Dimensions' menu item.

### Basic Operation: IMU Connection

To connect to a WITMOTION IMU select menu 'IMU' -> 'Connect'.

A second window will pop up where you can choose the COM port and baud rate.

Take Note: It is possible for the program to 'connect' to a COM port that does not belong to the IMU.
Once a connection is successful ensure that there are IMU acceleration values appearing in the main
window and that the orientation plot shows an expected orientation for the IMU. If you are sure that
the correct COM port is being used and there is a problem with the orientation plot, ensure that the
IMU has been set up to send quaternion data as that is used to calculate orientation.

Once connected, the return rate of the IMU can be set and the accelerometer can be calibrated in the
'IMU' menu item.

### Basic Operation: Saving data

Frames from the video/input signal (USB-port) are stored with data streamed from an IMU device (bluetooth)
and the results stored as:

- A series of .png files, each .png corresponding to a frame from the input signal. The name of the
  .png files start with the recorded frame number, followed by a timestamp based on the system time that
  they were read from the input signal.
- A data.txt file containing the IMU data for each frame, following a csv format. Each row
  corresponds to a .png frame, with the first value of the row matching the name of a .png frame.
- The data.txt file lines follow the following
  format: [frame_name,acceleration_data,quaternion_data,signal_dimensions,depth]
    - frame_name: Corresponds to the .png image saved.
    - acceleration_data: Acceleration data of frame.
    - quaternion_data: Quaternion data of frame.
    - signal_dimensions: Dimensions of saved frame.
    - depth: Default scan depth (depth of ultrasound image).

The default scan depth is stored for later editing, as the depth could potentially change on a
per-frame basis.

To save a single frame click the 'Save Frame' button. No IMU data is recorded with this, more of a
debugging function.

To start a recording click the 'Start Recording' button. This will start saving frames as .png images
and IMU data in the data.txt file. If no IMU is connected, the images are still saved and the IMU data is
assumed to be zero.


## WITMOTION IMU Settings

The IMU sensor must be connected to the laptop/computer via bluetooth so that the COM ports are assigned.
I am pretty sure that if the IMU is connected via a USB port it should still work, but I have not tested
this much. Using WITMOTION's own software, acceleration data, quaternion data, and time data must be 
enabled. This is the only data of interest in this project. More sensor readings are available and 
their acquisition is fairly straightforward should you want to change the code a little.

# NB

- WITMOTION does not have any official Python support. The following library was used to enable
  communication with the IMU: [https://pypi.org/project/witmotion/](https://pypi.org/project/witmotion/).
- Opening a menu while a signal source is connected causes a delay in the signal display. I cannot
  solve this at the moment. Just wait until the display signal catches up, it can take a little while.
- This project/program is run directly from PyCharm, and if any other libraries are required an error
  message will be shown.
- IMU data is stored in a variable during recording, and once the recording is stopped, timestamps are
  compared to match the IMU data with the frame.
- The program now stores the frames and IMU data in memory while recording, and when the recording is finished
  all the in-memory data is saved to disk. This was done to increase the speed at which frames could
  be grabbed (write operations tend to be quite slow) but it also results in a much higher memory usage.
  Do not run a recording for too long, otherwise the system will run out of available RAM (depending on available 
  memory). Try and keep recordings below 1 to 2 minutes.
- Recordings are now saved in a separate process, so the main screen can continue to operate as normal while the data 
  is being saved.
- The IMU that was used during this project becomes incredibly unstable in a hospital environment, with more than
  half the data being lost during a recording. A USB connection to the IMU can circumvent this, without changing
  how the program is used (USB serial connections show up in the Bluetooth connection pop-up).


# Problems

- As of 03/Mar/2023 there is a memory leak when the video signal is 1920x1080. It has something to do with the MJPG 
  format of the OpenCV class.
- ~~As of 01/Aug/2022 the plotting should be disabled when recording a signal.~~ This has been fixed. The plotting
  is now initially disabled and takes place on a separate process to the main process. The orientation plot is displayed 
  in a new window when enabled. This has removed the need for blit and should no longer slow the frame grabbing down.
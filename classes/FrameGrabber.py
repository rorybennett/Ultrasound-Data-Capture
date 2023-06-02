"""
FrameGrabber class for handling the OpenCV portion of the program. Frames from a USB connection are returned as
greyscale images.
are .
"""

import cv2 as cv

import constants as c


class FrameGrabber:
    """
    Class to handle the grabbing/capture of frames from a video signal that has been converted to a USB compatible
    signal (or the device's webcam/cameras) by using OpenCV's VideoCapture library. The width and height of the
    video signal can be set as well as the frame rate of the video signal. When setting these values, if OpenCv
    determines that the width, height, and/or frame rate are incompatible with the video signal it will set its
    own values. Once a SignalGrabber object is connected, frames can be requested. If a frame is successfully
    read by OpenCV a successful Boolean flag is returned with the frame. Changing the video source requires that
    the current signal be released, and a new call to connect() be made.
    """

    def __init__(self, signal_source=0, width=c.DEFAULT_SIGNAL_DIMENSIONS[0], height=c.DEFAULT_SIGNAL_DIMENSIONS[1],
                 fps=c.DEFAULT_FRAME_RATE):
        """
        Initialising of a SignalGrabber object. Connection is not made until connect() method is
        explicitly called. Initial parameter instantiation.

        Args:
            signal_source (int, optional): Integer source of video signal. Defaults to 0.
            width (int, optional): Requested pixel width of video signal. Defaults to 640.
            height (int, optional): Requested pixel height of video signal. Defaults to 480.
            fps (int, optional): Requested frame rate of video signal. Defaults to 100.
        """
        self.fps = fps  # Frame rate of the signal, not really used
        self.signalSource = signal_source  # Source of video signal
        self.width = width  # Pixel width of signal
        self.height = height  # Pixel height of signal
        self.sourceFps = fps  # Frame rate of signal
        self.is_connected = False  # Is the signal currently being streamed

        self.vid = cv.VideoCapture()  # VideoCapture object

    def __del__(self):
        """
        On object delete, release the VideoCapture device.
        """
        self.is_connected = False
        if self.vid and self.vid.isOpened():
            self.vid.release()
            print('FrameGrabber released.')

    def connect(self):
        """
        Attempt to create a VideoCapture object. First attempt to disconnect the object using self.disconnect().
        If the object is successfully created the MJPG codec is used and the dimensions and frame rate are set
        (via the setProperties() method). At a future date the codec may need to be changed to improve performance
        (frame rate).
        """
        try:
            # Disconnect.
            self.disconnect()

            print(f'Attempting to connect to source: {self.signalSource}, '
                  f'with dimensions: {self.width}x{self.height}...', end=' ')
            self.vid.open(self.signalSource, cv.CAP_DSHOW)
            if not self.vid.isOpened():
                print(f'Could not open source: {self.signalSource}.')
                return

            print(f'Connected to source {self.signalSource}.')
            self.is_connected = True

            # Set the signal properties
            self.set_grabber_properties(self.width, self.height, self.fps)
        except Exception as e:
            print(f'Error connecting to source: {e}')

    def disconnect(self):
        """
        Function to disconnect signal source. This releases the self.vid device and sets the self.isConnected
        variable to False, so no new frames are read.
        """
        if self.is_connected:
            print(f'Source connected: {self.is_connected}. Attempting to release current source...')
            self.vid.release()
            self.is_connected = False
            print(f'Source {self.signalSource} has been released.')

    def set_grabber_properties(self, width, height, fps=60) -> bool:
        """
        Set the properties of the FrameGrabber object. If the object is connected attempt to change the signal
        dimensions, else just change the instance variables. The setting of the frame rate (fps) is not monitored as
        OpenCV cannot return a frame rate from a VideoCapture object reliably.

        Args:
            width (int): Requested pixel width of video signal.
            height (int): Requested pixel height of video signal.
            fps (int, optional): Requested frame rate of video signal. Defaults to 100.

        Returns:
            success_flag (bool): True if the width and height were set to the requested values, else False.
        """
        success_flag = False

        self.width = width
        self.height = height
        self.fps = fps
        if self.is_connected:
            print(f'Attempting to set FrameGrabber dimensions to {width}x{height} at {fps}fps...', end=' ')

            # Attempt to set video source width and height, if cv is unable to use given
            # dimension, smaller default dimensions will be used.
            self.vid.set(cv.CAP_PROP_FRAME_WIDTH, self.width)
            self.vid.set(cv.CAP_PROP_FRAME_HEIGHT, self.height)

            # Set capture frame rate.
            self.vid.set(cv.CAP_PROP_FPS, self.fps)

            # Set video codec. "MJPG" appears to be much faster than default.
            # This codec appears to cause a memory leak with higher resolutions
            fourcc_1 = cv.VideoWriter_fourcc(*"MJPG")
            self.vid.set(cv.CAP_PROP_FOURCC, fourcc_1)

            # Set width and height to source width and height. This can be used to test if
            # the new dimensions were set properly.
            self.width = int(self.vid.get(cv.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.vid.get(cv.CAP_PROP_FRAME_HEIGHT))

            if self.width == width or self.height == height:
                print(f'Dimensions correctly set to {self.width}x{self.height}.\n')
                success_flag = True
            else:
                print(f'An error occurred setting dimensions. Default dimensions of '
                      f'{self.width}x{self.height}  were used.')
        else:
            print('FrameGrabber is not connected.')

        return success_flag

    def get_frame(self) -> (bool, any):
        """
        Attempt to read the next available frame from the video source. As soon as the frame is read by OpenCv it
        is returned, along with a Boolean success flag to indicate whether the read was successful or not. The returned
        frame is converted from BGR to GRAY before being returned.

        Returns:
            success_flag (bool): Read success_flag. True if frame read, else False.
            frame (image): Returned image id read was successful.
        """
        if self.is_connected:
            success_flag, frame = self.vid.read()
            # Return boolean success flag and current frame
            if success_flag:
                return success_flag, cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            else:
                self.is_connected = False
                return success_flag, None
        else:
            print('FrameGrabber is not connected. Call connect() before get_frame().')
            return False, None

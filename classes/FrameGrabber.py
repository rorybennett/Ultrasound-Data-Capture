import cv2 as cv


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

    def __init__(self, signalSource=0, width=640, height=480, fps=100):
        """
        Initialising of a SignalGrabber object. Connection is not made until connect() method is
        explicitly called. Initial parameter instantiation.

        Args:
            signalSource (int, optional): Integer source of video signal. Defaults to 0.
            width (int, optional): Requested pixel width of video signal. Defaults to 640.
            height (int, optional): Requested pixel height of video signal. Defaults to 480.
            fps (int, optional): Requested frame rate of video signal. Defaults to 100.
        """

        self.fps = fps
        self.signalSource = signalSource  # Source of video signal
        self.width = width  # Pixel width of signal
        self.height = height  # Pixel height of signal
        self.sourceFps = fps  # Frame rate of signal
        self.isConnected = False  # Is the signal currently being streamed

        self.vid = None  # VideoCapture object

    def __del__(self):
        """
        On object delete, release the VideoCapture device.
        """
        self.isConnected = False
        if self.vid.isOpened():
            self.vid.release()
            print('FrameGrabber released.')

    def connect(self):
        """
        Attempt to create a VideoCapture object. If the object is successfully created the MJPG
        codec is used and the dimensions and frame rate are set (via the setProperties() method).
        At a future date the codec may need to be changed to improve performance (frame rate).
        """
        try:
            print(f'Checking if FrameGrabber at {self.signalSource} is already open...')
            if self.isConnected:
                print(f'{self.isConnected}. Attempting to release current source: ({self.signalSource})...')
                self.vid.release()
                self.isConnected = False
            else:
                print(f'{self.isConnected}. No previous connection open.')

            print(
                f'Attempting to connect to source: {self.signalSource}, with dimensions: {self.width}x{self.height}...')
            self.vid = cv.VideoCapture(self.signalSource, cv.CAP_DSHOW)
            if not self.vid.isOpened():
                raise

            print(f'Connected to source {self.signalSource}.')
            self.isConnected = True

            # Set the signal properties
            self.setGrabberProperties(self.width, self.height, self.fps)
        except Exception as e:
            print(f'Error connecting to source: {e}')
            raise

    def setGrabberProperties(self, width, height, fps=100) -> bool:
        """
        Set the properties of the FrameGrabber object. If the object is connected attempt to change the signal
        dimensions, else just change the instance variables. The setting of the frame rate (fps) is not monitored as
        OpenCV cannot return a frame rate from a VideoCapture object reliably.

        Args:
            width (int): Requested pixel width of video signal.
            height (int): Requested pixel height of video signal.
            fps (int, optional): Requested frame rate of video signal. Defaults to 100.

        Returns:
            successFlag (bool): True if the width and height were set to the requested values, else False.
        """
        successFlag = False

        self.width = width
        self.height = height
        self.fps = fps
        if self.isConnected:
            print(f'Attempting to set FrameGrabber dimensions to {width}x{height} at {fps}fps...')

            # Attempt to set video source width and height, if cv is unable to use given
            # dimension, smaller default dimensions will be used.
            self.vid.set(cv.CAP_PROP_FRAME_WIDTH, self.width)
            self.vid.set(cv.CAP_PROP_FRAME_HEIGHT, self.height)

            # Set capture frame rate.
            self.vid.set(cv.CAP_PROP_FPS, self.fps)

            # Set width and height to source width and height. This can be used to test if
            # the new dimensions were set properly.
            self.width = int(self.vid.get(cv.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.vid.get(cv.CAP_PROP_FRAME_HEIGHT))

            # Set video codec. "MJPG" appears to be much faster than default.
            fourcc = cv.VideoWriter_fourcc('M', 'J', 'P', 'G')
            self.vid.set(cv.CAP_PROP_FOURCC, fourcc)
            if self.width == width or self.height == height:
                print(f'Dimensions correctly set to {self.width}x{self.height}.')
                successFlag = True
            else:
                print(f'An error occurred setting dimensions. Default dimensions of '
                      f'{self.width}x{self.height}  were used.')
        else:
            print('FrameGrabber is not connected.')

        return successFlag

    def getFrame(self) -> (bool, any):
        """
        Attempt to read the next available frame from the video source. As soon as the frame is read by OpenCv it
        is returned, along with a Boolean success flag to indicate whether the read was successful or not. The returned
        frame is converted from BGR to GRAY before being returned.

        Returns:
            successFlag (bool): Read successFlag. True if frame read, else False.
            frame (image): Returned image id read was successful.
        """
        if self.isConnected:
            successFlag, frame = self.vid.read()
            # Return boolean success flag and current frame
            if successFlag:
                return successFlag, cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            else:
                self.isConnected = False
                return successFlag, None
        else:
            print('FrameGrabber is not connected. Call connect() before getFrame().')
            return False, None

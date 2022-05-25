import Utils
from datetime import datetime as dt
import IMU
import FrameGrabber

import PySimpleGUI as sg


class DataCaptureDisplay():
    def __init__(self):
        # Create initial directories for storing data.
        self.singleFramesPath, self.videosPath = Utils.createInitialDirectories()
        # Record state of the program.
        self.enableRecording = False
        # Counter for labelling frame number in a recording.
        self.frameGrabCounter = 0
        # Time variables used to estimate frame rate of program.
        self.fpsCalc1 = dt.now().timestamp()
        self.fpsCalc2 = dt.now().timestamp()
        # IMU object instantiated with default values.
        self.imu = IMU.IMU()
        # Display FrameGrabber results.
        self.enableDisplay = True
        # Enable plot updates
        self.enablePlotting = True
        # FrameGrabber object instantiated with default values.
        self.frameGrabber = FrameGrabber.FrameGrabber()
        # Initial search for system COM ports.
        self.availableComPorts = IMU.availableComPorts()

        self.layout = self.createLayout()



    def createLayout(self):
        pass

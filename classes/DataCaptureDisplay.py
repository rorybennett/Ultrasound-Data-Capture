import Utils
from datetime import datetime as dt
from classes import IMU
from classes import FrameGrabber

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

        self.window = sg.Window('Ultrasound Data Capture', self.layout, finalize=True)

        self.run()

        self.close()

    def createLayout(self):
        imuColumnLayout = [
            [sg.Text('IMU Orientation Plot', size=(40, 1), justification='center', font='Helvetica 20')],
            [sg.Canvas(size=(500, 500), key='-CANVAS-PLOT-')],
            [sg.Text('Select Azimuth')],
            [sg.Slider(range=(0, 360), default_value=30, size=(40, 10), orientation='h', key='-SLIDER-AZIMUTH-',
                       enable_events=True)],
            [sg.Text('IMU Controls', size=(40, 1), justification='center', font='Helvetica 20')],
            [sg.Button('', image_source='icons/refresh_icon.png', image_subsample=3, border_width=2,
                       key='-BUTTON-COM-REFRESH-')]
        ]

        layout = [[sg.Column(imuColumnLayout, element_justification='center')]]

        return layout

    def run(self):
        """
        Main loop for displaying the GUI and reacting to events, in standard PySimpleGUI fashion.
        """
        while True:
            event, values = self.window.read(timeout=0)

            if event == sg.WIN_CLOSED:
                break

            if event == '-SLIDER-AZIMUTH-':
                self.setAzimuth(values['-SLIDER-AZIMUTH-'])

            if event == '-BUTTON-COM-REFRESH-':
                self.refreshComPorts()

    def setAzimuth(self, azimuth):
        """
        Set the azimuth of the plot to the slider value. This allows for aligning the plot to the user's orientation
        since the IMU orientation is based on magnetic north.
        Args:
            azimuth:
        """
        print(f'The azimuth will be set to: {azimuth}')

    def refreshComPorts(self):
        """
        Refresh the available COM ports. The list of available COM ports is updated as well as the drop down menu/list.
        """
        print('Refresh the available com ports.')

    def close(self):
        """
        Delete references to IMU and FrameGrabber objects for garbage collection. This ensures the resources are freed
        up for future use. Only called as the program is shutting down.
        """
        del self.imu
        del self.frameGrabber

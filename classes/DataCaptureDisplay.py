import utils as ut
from classes import IMU
from classes import FrameGrabber
import styling as st
import constants as c

import PySimpleGUI as sg
from datetime import datetime as dt


class DataCaptureDisplay():
    def __init__(self):
        # Create initial directories for storing data.
        self.singleFramesPath, self.videosPath = ut.createInitialDirectories()
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
            [sg.Text('IMU Orientation Plot', size=(40, 1), justification='center', font=st.HEADING_FONT)],
            [sg.Canvas(key='-CANVAS-PLOT-', size=(500, 500))],
            [sg.Text('Select Azimuth')],
            [sg.Slider(key='-SLIDER-AZIMUTH-', range=(0, 360), default_value=30, size=(40, 10), orientation='h',
                       enable_events=True)],
            [sg.Text('IMU Controls', size=(40, 1), justification='center', font=st.HEADING_FONT,
                     pad=((0, 0), (20, 5)))],
            [sg.Button(key='-BUTTON-COM-REFRESH-', button_text='', image_source='icons/refresh_icon.png',
                       image_subsample=4, border_width=3),
             sg.Combo(key='-COMBO-COM-PORT-', values=self.availableComPorts, size=7, font=st.COMBO_FONT,
                      enable_events=True, readonly=True),
             sg.Text('Baud Rate:', justification='right', font=st.DESC_FONT, pad=((20, 0), (0, 0))),
             sg.Combo(key='-COMBO-BAUD-RATE-', values=c.COMMON_BAUD_RATES, size=7, font=st.COMBO_FONT,
                      enable_events=True, readonly=True),
             sg.Button(key='-BUTTON-IMU-CONNECT-', button_text='Connect to IMU', font=st.BUTTON_FONT, border_width=3,
                       pad=((40, 0), (0, 0)))],

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

            if event == '-COMBO-COM-PORT-':
                self.setComPort(values['-COMBO-COM-PORT-'])

            if event == '-COMBO-BAUD-RATE-':
                self.setBaudRate(values['-COMBO-BAUD-RATE-'])

            if event == '-BUTTON-IMU-CONNECT-':
                self.toggleImuConnect()

    def setAzimuth(self, azimuth):
        """
        Set the azimuth of the plot to the slider value. This allows for aligning the plot to the user's orientation
        since the IMU orientation is based on magnetic north.

        Args:
            azimuth (int): Azimuth to set the displayed plot to.
        """
        print(f'The azimuth will be set to: {azimuth}')

    def refreshComPorts(self):
        """
        Refresh the available COM ports. The list of available COM ports is updated as well as the drop down menu/list.
        """
        print('Refresh the available com ports.')

    def setComPort(self, comPort):
        """
        Set the COM port of the IMU to the value given. The IMU may not always be able to connect to the given COM port,
        or it may connect but receive no data. Both of these problems indicate that the incorrect COM port was chosen.

        Args:
            comPort (str): Com port to set the IMU to.
        """
        print(f'Will set the COM port of the IMU to: {comPort}.')

    def setBaudRate(self, baudRate):
        """
        Set the baud rate of the IMU to the given value.

        Args:
            baudRate (int): Baud rate used by the IMU for communication.
        """
        print(f'Will set the baud rate of the IMU to: {baudRate}.')

    def close(self):
        """
        Delete references to IMU and FrameGrabber objects for garbage collection. This ensures the resources are freed
        up for future use. Only called as the program is shutting down.
        """
        del self.imu
        del self.frameGrabber

    def toggleImuConnect(self):
        """
        Toggles the connection state of the IMU object. If the IMU is connected, it will be disconnected, else it will
        be connected using the values set in the Combo boxes or using the default initialisation values.
        """
        print(f'IMU connected: {self.imu.isConnected}, will be swapped.')

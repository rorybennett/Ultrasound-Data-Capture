"""
A Python script for testing the battery life of an IMU by recording data until the IMU dies.
"""
from classes import IMU
import styling as st
import constants as c

import PySimpleGUI as sg
from datetime import datetime as dt
from pathlib import Path
import witmotion as wm

# Location of refresh icon, stored for main program.
refreshIcon = str(Path().absolute().parent) + '\\icons\\refresh_icon.png'


class ImuBatterLifeTest:
    def __init__(self):
        # COM ports available on the system.
        self.availableComPorts = IMU.availableComPorts()
        # Number of messages received from the IMU device during a test.
        self.imuTestCounter = 0
        # Layout creation.
        self.layout = self.createLayout()
        # IMU object and associated variables.
        self.imu = None
        self.comPort = 'COM3'
        self.baudRate = 115200
        self.quaternion = None
        # Connection state of the IMU.
        self.isConnected = False
        # Create main window for display.
        self.window = sg.Window('IMU Battery Tester', self.layout, finalize=True)
        # Display loop.
        while True:
            event, values = self.window.read(0)
            # Close window event (exit).
            if event == sg.WIN_CLOSED:
                break
            # Refresh available COM ports.
            if event == '-BUTTON-COM-REFRESH-':
                self.refreshComPorts()
            # Combo of available COM ports.
            if event == '-COMBO-COM-PORT-':
                self.comPort = values['-COMBO-COM-PORT-']
            # Combo of available baud rates.
            if event == '-COMBO-BAUD-RATE-':
                self.baudRate = int(values['-COMBO-BAUD-RATE-'])
            # Toggle IMU connection.
            if event == '-BUTTON-IMU-CONNECT-':
                self.toggleImuConnect()
        # Close IMU connections manually.
        print('Program closing down...')
        if self.isConnected:
            self.imu.ser.close()
            self.imu.close()

    def createLayout(self):
        """
        Create the layout for the program.

        Returns:
            layout (list): 2D list used by PySimpleGUI as the layout format.
        """
        imuLayout = [
            [sg.Text('IMU Controls', size=(40, 1), justification='center', font=st.HEADING_FONT,
                     pad=((0, 0), (0, 20)))],
            [sg.Button(key='-BUTTON-COM-REFRESH-', button_text='', image_source=refreshIcon,
                       image_subsample=4, border_width=3),
             sg.Combo(key='-COMBO-COM-PORT-', values=self.availableComPorts, size=7, font=st.COMBO_FONT,
                      enable_events=True, readonly=True),
             sg.Text('Baud Rate:', justification='right', font=st.DESC_FONT, pad=((20, 0), (0, 0))),
             sg.Combo(key='-COMBO-BAUD-RATE-', values=c.COMMON_BAUD_RATES, size=7, font=st.COMBO_FONT,
                      enable_events=True, readonly=True)],
            [sg.Button(key='-BUTTON-IMU-CONNECT-', button_text='Connect IMU', size=(15, 1), font=st.BUTTON_FONT,
                       border_width=3, pad=((0, 0), (20, 20)))],
            [sg.Text('Return Rate:', justification='right', font=st.DESC_FONT, pad=((20, 0), (0, 0))),
             sg.Combo(key='-COMBO-RETURN-RATE-', values=c.IMU_RATE_OPTIONS, size=7, font=st.COMBO_FONT,
                      enable_events=True, readonly=True, disabled=True),
             sg.Button(key='-BUTTON-IMU-CALIBRATE-', button_text='Calibrate Acc', size=(15, 1),
                       font=st.BUTTON_FONT, border_width=3, pad=((40, 0), (0, 0)), disabled=True),
             ]
        ]

        imuPlotLayout = [
            [sg.Text('IMU Orientation Plot', size=(40, 1), justification='center', font=st.HEADING_FONT)],
            [sg.Canvas(key='-CANVAS-PLOT-', size=(500, 500))]
        ]

        imuRatePlot = [
            [sg.Text('IMU Return Rate Plot', size=(40, 1), justification='center', font=st.HEADING_FONT)],
            [sg.Canvas(key='-CANVAS-PLOT-', size=(500, 500))]
        ]

        testControlLayout = [
            [sg.Button(key='-BUTTON-TEST-START-', button_text='Start', font=st.BUTTON_FONT, border_width=3,
                       pad=((0, 10), (20, 20)), disabled=True),

             sg.Button(key='-BUTTON-TEST-STOP-', button_text='Stop', font=st.BUTTON_FONT, border_width=3,
                       pad=((0, 10), (20, 20)), disabled=True)]
        ]

        layout = [
            [sg.Column(imuLayout, element_justification='center', vertical_alignment='top', justification='c')],
            [sg.HSep(pad=((0, 10), (10, 20)))],
            [sg.Column(imuPlotLayout, element_justification='center', vertical_alignment='top'),
             sg.Column(imuRatePlot, element_justification='center', vertical_alignment='top')],
            [sg.HSep(pad=((0, 10), (10, 20)))],
            [sg.Column(testControlLayout, element_justification='center', vertical_alignment='top', justification='c')]
        ]

        return layout

    def refreshComPorts(self):
        """
        Refresh the available COM ports. The list of available COM ports is updated as well as the drop-down menu/list.
        """
        self.availableComPorts = IMU.availableComPorts()
        self.window['-COMBO-COM-PORT-'].update(values=self.availableComPorts)

    def toggleImuConnect(self):
        """
        Toggles the connection state of the IMU. If the IMU is connected, it will be disconnected, else it will
        be connected using the values set in the Combo boxes.
        """

        # If imu is not connected it must be connected, else disconnected.
        if not self.isConnected:
            print(f'Attempting to connect to {self.comPort} at {self.baudRate}...')
            try:
                self.imu = wm.IMU(self.comPort, self.baudRate)
                self.imu.subscribe(self.imuCallback)
                self.isConnected = True
            except Exception as e:
                print(f'Error connecting to IMU: {e}.')
                self.isConnected = False
        else:
            print(f'Disconnecting from {self.comPort} as {self.baudRate}...')
            self.imu.close()
            self.imu.ser.close()
            self.isConnected = False
        # Set element states
        self.window['-COMBO-COM-PORT-'].update(disabled=True if self.isConnected else False)
        self.window['-COMBO-BAUD-RATE-'].update(disabled=True if self.isConnected else False)
        self.window['-BUTTON-IMU-CONNECT-'].update(
            button_color='#ff2121' if self.isConnected else sg.DEFAULT_BUTTON_COLOR,
            text='Disconnect IMU' if self.isConnected else 'Connect IMU'
        )
        self.window['-COMBO-RETURN-RATE-'].update(disabled=True if not self.isConnected else False)
        self.window['-BUTTON-IMU-CALIBRATE-'].update(disabled=True if not self.isConnected else False)

    def imuCallback(self, msg):
        """
        Callback subscribed to the IMU object. Called whenever a new dataset is ready to be read. This callback is
        activated for every value sent by the IMU (Acceleration, Quaternion, Angle, ..etc) and not just for each
        serial packet. Only quaternion messages are read here, and the counter only increases when a quaternion
        message is read.

        Args:
            msg (String): The type of dataset that is newly available.
        """
        msg_type = type(msg)

        if msg_type is wm.protocol.AccelerationMessage:
            pass
        elif msg_type is wm.protocol.QuaternionMessage:
            self.quaternion = self.imu.get_quaternion()
            self.imuTestCounter += 1
        elif msg_type is wm.protocol.AngleMessage:
            pass


ImuBatterLifeTest()

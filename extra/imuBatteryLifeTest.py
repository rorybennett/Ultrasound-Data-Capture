"""
A Python script for testing the battery life of an IMU by recording data until the IMU dies.
"""
from classes import IMU
import styling as st
import constants as c

import PySimpleGUI as sg
from datetime import datetime as dt
from pathlib import Path

refreshIcon = str(Path().absolute().parent) + '\\icons\\refresh_icon.png'


class ImuBatterLifeTest:

    def __init__(self):

        self.availableComPorts = IMU.availableComPorts()

        self.layout = self.createLayout()

        self.window = sg.Window('IMU Battery Tester', self.layout, finalize=True)

        while True:
            event, values = self.window.read(0)

            if event == sg.WIN_CLOSED:
                break

        print('Program closing down...')

    def createLayout(self):
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


ImuBatterLifeTest()

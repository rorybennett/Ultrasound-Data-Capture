"""
A Python script for testing the battery life of an IMU by recording data until the IMU dies.
"""
from classes import IMU
import styling as st

import PySimpleGUI as sg
from datetime import datetime as dt


def main():

    layout = createLayout()


def createLayout():
    imuLayout = [
        [sg.Text('IMU Controls', size=(40, 1), justification='center', font=st.HEADING_FONT,
                 pad=((0, 0), (0, 20)))],
        [sg.Button(key='-BUTTON-COM-REFRESH-', button_text='', image_source='icons/refresh_icon.png',
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

    layout = [
        [imuLayout],
        [sg.Column(imuPlotLayout, element_justification='center', vertical_alignment='top'),
         sg.Column(imuRatePlot, element_justification='center', vertical_alignment='top')]
    ]

    return layout


if __name__ == '__main__':
    main()

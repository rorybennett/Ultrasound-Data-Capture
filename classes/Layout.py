"""
Class for handling all layouts used in DataCaptureDisplay. This class is intended to clean up the DataCaptureDisplay
class to make the code more readable. Future layout updates should be easier with the separation.
"""
import constants as c
import styling as st
import PySimpleGUI as sg


class Layout:
    def __init__(self, menu):
        self.menu = menu

    def getMainWindowLayout(self):
        """
        Create the main window layout. This layout is split into a Video/Signal section and an IMU section.

        Video/Signal:       Contains a display that shows the signal when connected, and has controls for
                            saving/recording frames.
        IMU:                Contains a display that shows the orientation of the IMU.
        """
        videoControlsLayout1 = [
            [sg.Button(key='-BUTTON-SNAPSHOT-', button_text='Save Frame', size=(15, 1), font=st.BUTTON_FONT,
                       border_width=3, pad=((0, 0), (20, 0)), disabled=True)],
            [sg.Button(key='-BUTTON-RECORD-TOGGLE-', button_text='Start Recording', size=(15, 1),
                       font=st.BUTTON_FONT,
                       border_width=3, pad=((0, 0), (20, 0)), disabled=True)]
        ]

        videoControlsLayout2 = [
            [sg.Text(text='GUI Frame Rate: ', justification='right', font=st.DESC_FONT),
             sg.Text(key='-TEXT-GUI-RATE-', text='0', justification='left', font=st.DESC_FONT,
                     size=(4, 1))],
            [sg.Text(text='Signal Frame Rate: ', justification='right', font=st.DESC_FONT),
             sg.Text(key='-TEXT-SIGNAL-RATE-', text='0', justification='left', font=st.DESC_FONT,
                     size=(4, 1))]
        ]

        displayColumnLayout = [
            [sg.Text('Video Signal', size=(40, 1), justification='center', font=st.HEADING_FONT)],
            [sg.Image(key='-IMAGE-FRAME-', size=c.DEFAULT_DISPLAY_DIMENSIONS, background_color='#000000')],
            [sg.Text(text=f'Display Dimensions: {c.DEFAULT_DISPLAY_DIMENSIONS}.', font=st.DESC_FONT,
                     justification='left', expand_x=True),
             sg.Text(key='-TEXT-SIGNAL-DIMENSIONS-', text='Signal Dimensions: ', font=st.DESC_FONT)],
            [sg.Button(key='-BUTTON-DISPLAY-TOGGLE-', button_text='Disable Display', size=(15, 1),
                       font=st.BUTTON_FONT,
                       border_width=3, pad=((0, 0), (10, 0)))],
            [sg.HSep(pad=((10, 0), (10, 20)))],
            [sg.Text('Video Signal Controls', size=(40, 1), justification='center', font=st.HEADING_FONT,
                     pad=((0, 0), (0, 20)))],
            [sg.Column(videoControlsLayout1, element_justification='center', expand_x=True),
             sg.Column(videoControlsLayout2, element_justification='center', expand_x=True)]

        ]

        imuColumnLayout = [
            [sg.Text('IMU Orientation Plot', size=(40, 1), justification='center', font=st.HEADING_FONT)],
            [sg.Canvas(key='-CANVAS-PLOT-', size=(500, 500))],
            [sg.Text('Select Azimuth', font=st.DESC_FONT, pad=((0, 0), (12, 0)))],
            [sg.Slider(key='-SLIDER-AZIMUTH-', range=(0, 360), default_value=c.DEFAULT_AZIMUTH, size=(40, 10),
                       orientation='h', enable_events=True)],
            [sg.Text('Acceleration values:', font=st.DESC_FONT, pad=((0, 0), (12, 0))),
             sg.Text(key='-TEXT-ACCELERATION-X-', text='', font=st.DESC_FONT, justification='right', size=(8, 1),
                     pad=((0, 0), (12, 0))),
             sg.Text(key='-TEXT-ACCELERATION-Y-', text='', font=st.DESC_FONT, justification='right', size=(8, 1),
                     pad=((0, 0), (12, 0))),
             sg.Text(key='-TEXT-ACCELERATION-Z-', text='', font=st.DESC_FONT, justification='right', size=(8, 1),
                     pad=((0, 0), (12, 0)))],
            [sg.Button(key='-BUTTON-PLOT-TOGGLE-', button_text='Disable Plotting', size=(15, 1),
                       font=st.BUTTON_FONT,
                       border_width=3, pad=((0, 0), (10, 0)))],
            [sg.HSep(pad=((0, 10), (10, 20)))]
        ]

        return [[sg.Menu(key='-MENU-', menu_definition=self.menu.getMenu()),
                 sg.Column(displayColumnLayout, element_justification='center',
                           vertical_alignment='top'),
                 sg.Column(imuColumnLayout, element_justification='center', vertical_alignment='top')]]

    def getImuWindowLayout(self, availableComPorts, comPort, baudRate) -> list:
        """
        Function that creates the layout for the IMU connection window.

        Args:
            availableComPorts (list): A list of available COM ports.
            comPort (string): Default COM port to show in COMBO box.
            baudRate (int): Default baud rate to show in COMBO box.

        Returns:
            list used for layout.
        """
        return [
            [sg.Button(key='-BUTTON-COM-REFRESH-', button_text='', image_source='icons/refresh_icon.png',
                       image_subsample=4, border_width=3, pad=((0, 10), (20, 0))),
             sg.Combo(key='-COMBO-COM-PORT-', values=availableComPorts, size=7, font=st.COMBO_FONT,
                      enable_events=True, readonly=True, default_value=comPort, pad=((0, 0), (20, 0))),
             sg.Text('Baud Rate:', justification='right', font=st.DESC_FONT, pad=((20, 0), (20, 0))),
             sg.Combo(key='-COMBO-BAUD-RATE-', values=c.COMMON_BAUD_RATES, size=7, font=st.COMBO_FONT,
                      enable_events=True, readonly=True, default_value=baudRate, pad=((0, 0), (20, 0)))],
            [sg.HSeparator(pad=((10, 10), (20, 20)))],
            [sg.Button(key='-BUTTON-IMU-CONNECT-', button_text='Connect', border_width=3, font=st.BUTTON_FONT)]
        ]

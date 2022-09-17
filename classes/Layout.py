"""
Class for handling all layouts used in DataCaptureDisplay. This class is intended to clean up the DataCaptureDisplay
class to make the code more readable. Future layout updates should be easier with the separation.

There is one primary layout, a layout for plotting the probe orientation, and an IMU connection layout.

"""
import constants as c
import styling as st
import PySimpleGUI as sg


def getPlottingWindowLayout() -> list:
    """
    Create the plotting window layout and return it.

    Returns:
        layout (list): Layout in list form.
    """
    layout = [
        [sg.Canvas(k='-CANVAS-PLOT-', size=(500, 500))]
    ]

    return layout


def getImuWindowLayout(availableComPorts, comPort, baudRate) -> list:
    """
    Create the layout for the IMU connection window.

    Args:
        availableComPorts (list): A list of available COM ports.
        comPort (string): Default COM port to show in COMBO box.
        baudRate (int): Default baud rate to show in COMBO box.

    Returns:
        layout (list): Layout in the form of a list.
    """
    layout = [
        [sg.Button(k='-BTN-COM-REFRESH-', button_text='', image_source='icons/refresh_icon.png',
                   image_subsample=4, border_width=3, pad=((0, 10), (20, 0))),
         sg.Combo(k='-COMBO-COM-PORT-', values=availableComPorts, size=7, font=st.FONT_COMBO,
                  enable_events=True, readonly=True, default_value=comPort, pad=((0, 0), (20, 0))),
         sg.Text('Baud Rate:', justification='right', font=st.FONT_DESCR, pad=((20, 0), (20, 0))),
         sg.Combo(k='-COMBO-BAUD-RATE-', values=c.COMMON_BAUD_RATES, size=7, font=st.FONT_COMBO,
                  enable_events=True, readonly=True, default_value=baudRate, pad=((0, 0), (20, 0)))],
        [sg.HSeparator(pad=((10, 10), (20, 20)))],
        [sg.Button(k='-BTN-IMU-CONNECT-', button_text='Connect', border_width=3, font=st.FONT_BTN)]
    ]

    return layout


class Layout:
    def __init__(self, menu):
        self.menu = menu

    def getInitialLayout(self) -> list:
        """
        Create the initial layout. Editing is disabled in this layout. There are three primary sections to this layout:

        1. Display Row:         Contains the Image element where the frame is displayed and the Canvas where the
                                orientation plot is displayed.
        2. Record Row:          Contains buttons and text views that enable recording functions and recording details to
                                be displayed.
        3. Miscellaneous Row:   A final row to show some extra information about what is happening in the window.

        Returns:
            layout (list): Layout in the form of a list.
        """
        displayRow = self.__createDisplayRow()

        recordRow = self.__createRecordRow()

        miscellaneousRow = self.__createMiscellaneousRow()

        layout = [
            [sg.Menu(k='-MENU-', menu_definition=self.menu.getMenu())],
            [displayRow],
            [sg.HSep(pad=((0, 0), (0, 10)))],
            [recordRow],
            [sg.HSep(pad=((0, 0), (0, 10)))],
            [miscellaneousRow]
        ]

        return layout

    def __createDisplayRow(self) -> list:
        """
        Create the display row of the main window. This contains the image that displays frames and the plot that
        shows the orientation of the IMU, along with some buttons and text information. The frame is displayed
        using an Image element when recording from a signal.

        Returns:
            layout (list): Layout in the form of a list.
        """
        displayColumn = [
            [sg.Image(k='-IMAGE-FRAME-', size=c.DISPLAY_DIMENSIONS, background_color='#000000',
                      pad=(0, 0))],
            [sg.Text(k='-TXT-SIGNAL-DIMENSIONS-', text='Signal Dimensions: ', font=st.FONT_INFO, expand_x=True,
                     justification='left', pad=(0, 0)),
             sg.Text(text=' Signal FPS: ', justification='right', font=st.FONT_INFO, pad=(0, 0)),
             sg.Text(k='-TXT-SIGNAL-RATE-', text='0', justification='center', font=st.FONT_INFO, size=(3, 1),
                     pad=(0, 0))]
        ]

        imuColumn = [
            [sg.Text('IMU Accelerations', font=st.FONT_DESCR, pad=((5, 0), (10, 0)))],
            [sg.Text(k='-TXT-IMU-ACC-', text='', font=st.FONT_DESCR, justification='center', expand_x=True,
                     size=(25, 1))],
            [sg.Button(k='-BTN-PLOT-TOGGLE-', button_text='Enable Plotting', size=(15, 1),
                       font=st.FONT_BTN, border_width=3, pad=((0, 0), (0, 5)))],
            [sg.Button(k='-BTN-DISPLAY-TOGGLE-', button_text='Disable Display', size=(15, 1),
                       font=st.FONT_BTN,
                       border_width=3, pad=((0, 0), (5, 0)), button_color=st.COL_BTN_ACTIVE)]
        ]

        layout = [
            [sg.pin(sg.Column(k='-COL-EDIT-FALSE-', layout=displayColumn, vertical_alignment='top')),
             sg.Column(imuColumn, vertical_alignment='top', element_justification='center')]
        ]

        return layout

    def __createRecordRow(self) -> list:
        """
        Create the record row of the main window. This contains the recording buttons and details about the current
        recording session.

        Returns:
            layout (list): Layout in the form of a list.
        """
        recordStartColumn = [
            [sg.Text(text='Record Start', font=st.FONT_DESCR)],
            [sg.Text(k='-TXT-RECORD-START-', text='--:--:--', font=st.FONT_DESCR, size=(12, 1),
                     justification='center')]
        ]

        recordEndColumn = [
            [sg.Text(text='Record End', font=st.FONT_DESCR)],
            [sg.Text(k='-TXT-RECORD-END-', text='--:--:--', font=st.FONT_DESCR, size=(12, 1), justification='center')]
        ]

        recordElapsedColumn = [
            [sg.Text(text='Elapsed Time', font=st.FONT_DESCR)],
            [sg.Text(k='-TXT-RECORD-ELAPSED-', text='--:--:--', font=st.FONT_DESCR, size=(12, 1),
                     justification='center')]
        ]

        recordFramesColumn = [
            [sg.Text(text='Frames saved', font=st.FONT_DESCR)],
            [sg.Text(k='-TXT-FRAMES-SAVED-', text='0', font=st.FONT_DESCR, size=(12, 1), justification='center')]
        ]

        layout = [
            [sg.Button(k='-BTN-SNAPSHOT-', button_text='Save Frame', size=(15, 1), font=st.FONT_BTN,
                       border_width=3, pad=((0, 20), (0, 0)), disabled=True),
             sg.Button(k='-BTN-RECORD-TOGGLE-', button_text='Start Recording', size=(15, 1), font=st.FONT_BTN,
                       border_width=3, pad=((0, 0), (0, 0)), disabled=True),
             sg.Column(recordStartColumn, element_justification='center', pad=(0, 0)),
             sg.Column(recordEndColumn, element_justification='center', pad=(0, 0)),
             sg.Column(recordElapsedColumn, element_justification='center', pad=(0, 0)),
             sg.Column(recordFramesColumn, element_justification='center', pad=(0, 0))]
        ]

        return layout

    def __createMiscellaneousRow(self) -> list:
        """
        Create the bottom row of the main window. This shows extra information about what is happening during the
        running of the program.

        Returns:
            layout (list): Layout in the form of a list.
        """
        frameRateDetails = [
            [sg.Text(text='GUI: ', justification='right', font=st.FONT_INFO, pad=(0, 0), relief=sg.RELIEF_SUNKEN,
                     border_width=2),
             sg.Text(k='-TXT-GUI-RATE-', text='0', justification='center', font=st.FONT_INFO,
                     size=(4, 1), pad=(0, 0), relief=sg.RELIEF_SUNKEN, border_width=2),
             sg.Text(text=' Resize: ', justification='right', font=st.FONT_INFO, pad=(0, 0), relief=sg.RELIEF_SUNKEN,
                     border_width=2),
             sg.Text(k='-TXT-RESIZE-RATE-', text='0', justification='center', font=st.FONT_INFO,
                     size=(3, 1), pad=(0, 0), relief=sg.RELIEF_SUNKEN, border_width=2)]
        ]

        layout = [
            [frameRateDetails]
        ]

        return layout

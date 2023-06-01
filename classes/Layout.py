"""
Class for handling all layouts used in DataCaptureDisplay. This class is intended to clean up the DataCaptureDisplay
class to make the code more readable. Future layout updates should be easier with the separation.

There is one primary layout, a layout for plotting the probe orientation, and an IMU connection layout.

"""
from pathlib import Path

import PySimpleGUI as Psg

import constants as c
import styling as st


def plotting_layout() -> list:
    """
    Create the plotting window layout and return it.

    Returns:
        layout (list): Layout in list form.
    """
    layout = [
        [Psg.Canvas(k='-CANVAS-PLOT-', s=(350, 350))]
    ]

    return layout


def imu_layout(com_ports, com_port, baud_rate) -> list:
    """
    Create the layout for the IMU connection window.

    Args:
        com_ports (list): A list of available COM ports.
        com_port (string): Default COM port to show in COMBO box.
        baud_rate (int): Default baud rate to show in COMBO box.

    Returns:
        layout (list): Layout in the form of a list.
    """
    layout = [
        [Psg.B(k='-B-COM-REFRESH-', button_text='', border_width=3, p=((0, 10), (20, 20)),
               image_source=str(Path().absolute().parent) + '\\icons\\refresh_icon.png', image_subsample=4),
         Psg.Combo(k='-COMBO-COM-PORT-', values=com_ports, font=st.FONT_COMBO,
                   readonly=True, default_value='Select COM Port...', s=40, p=((0, 0), (20, 20)))],
        [Psg.T('Baud Rate:', justification='right', font=st.FONT_DESCR, p=((20, 0), (20, 0))),
         Psg.Combo(k='-COMBO-BAUD-RATE-', values=c.COMMON_BAUD_RATES, s=7, font=st.FONT_COMBO,
                   readonly=True, default_value=baud_rate, p=((0, 0), (20, 0)))],
        [Psg.HSep(p=((10, 10), (20, 20)))],
        [Psg.B(k='-B-IMU-CONNECT-', button_text='Connect', border_width=3, font=st.FONT_BTN)]
    ]

    return layout


class Layout:
    def __init__(self, menu):
        self.menu = menu

    def get_initial_layout(self) -> list:
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
        display_row = self.__create_display_row()

        miscellaneous_row = self.__create_miscellaneous_row()

        layout = [
            [Psg.Menu(k='-M-', menu_definition=self.menu.get_menu())],
            [display_row],
            [Psg.HSep(p=((0, 0), (0, 10)))],
            [miscellaneous_row]
        ]

        return layout

    def __create_display_row(self) -> list:
        """
        Create the display row of the main window. This contains the image that displays frames and the plot that
        shows the orientation of the IMU, along with some buttons and text information. The frame is displayed
        using an Image element when recording from a signal.

        Returns:
            layout (list): Layout in the form of a list.
        """
        display_column = [
            [Psg.Image(k='-IMAGE-FRAME-', s=c.DISPLAY_DIMENSIONS, background_color='#000000',
                       p=((0, 0), (5, 10)))],
            [Psg.T(k='-T-SIGNAL-DIMENSIONS-', text='Signal Dimensions: ', font=st.FONT_INFO, expand_x=True,
                   justification='left', p=(0, 0)),
             Psg.T(text=' Signal FPS: ', justification='right', font=st.FONT_INFO, p=(0, 0)),
             Psg.T(k='-T-SIGNAL-RATE-', text='0 fps', justification='center', font=st.FONT_INFO, s=(7, 1),
                   p=(0, 0))]
        ]

        imu_column = [
            [Psg.T('IMU Data', font=st.FONT_DESCR + ' underline', p=((5, 0), (5, 0)))],
            [Psg.Col(element_justification='center', layout=[[
                Psg.T(k='-T-IMU-AX-', text=f'Ax: ', font=st.FONT_DESCR, expand_x=True, s=(7, 1)),
                Psg.T(k='-T-IMU-AY-', text=f'Ay: ', font=st.FONT_DESCR, expand_x=True, s=(7, 1)),
                Psg.T(k='-T-IMU-AZ-', text=f'Az: ', font=st.FONT_DESCR, expand_x=True, s=(7, 1))]]
                     )],
            [Psg.HSep(p=((0, 0), (0, 10)))],
            [Psg.B(k='-B-PLOT-TOGGLE-', button_text='Show Orientation', s=(15, 1),
                   font=st.FONT_BTN, border_width=3, p=((0, 0), (0, 5)))],
            [Psg.B(k='-B-DISPLAY-TOGGLE-', button_text='Disable Display', s=(15, 1),
                   font=st.FONT_BTN, border_width=3, p=((0, 0), (5, 10)), button_color=st.COL_BTN_ACTIVE)],
            [Psg.HSep(p=((0, 0), (0, 10)))],
            [Psg.T(text='Recording Started', font=st.FONT_DESCR)],
            [Psg.T(k='-T-RECORD-START-', text='--:--:--', font=st.FONT_DESCR, s=(12, 1),
                   justification='center')],
            [Psg.T(text='Elapsed Time', font=st.FONT_DESCR)],
            [Psg.T(k='-T-RECORD-ELAPSED-', text='--:--:--', font=st.FONT_DESCR, s=(12, 1),
                   justification='center')],
            [Psg.T(text='Frames To Save', font=st.FONT_DESCR)],
            [Psg.T(k='-T-FRAMES-SAVED-', text='0', font=st.FONT_DESCR, s=(12, 1), justification='center')],
            [Psg.T(text='Patient Identifier', font=st.FONT_DESCR)],
            [Psg.I(k='-I-PATIENT-', font=st.FONT_DESCR, s=(12, 1), justification='center')],
            [Psg.T(text='Scan Plane', font=st.FONT_DESCR)],
            [Psg.Col(element_justification='left', layout=[
                [Psg.R(k='-R-TA-', font=st.FONT_DESCR, group_id='SCAN-TYPE', text='Transabdominal')],
                [Psg.R(k='-R-TP-', font=st.FONT_DESCR, group_id='SCAN-TYPE', text='Transperineal')],
                [Psg.R(k='-R-O-', font=st.FONT_DESCR, group_id='SCAN-TYPE', text='Other', default=True)]])],
            [Psg.B(k='-B-RECORD-TOGGLE-', button_text='Start Recording', s=(15, 1), font=st.FONT_BTN,
                   border_width=3, p=((0, 0), (5, 0)), disabled=True)]
        ]

        layout = [
            [Psg.pin(Psg.Column(k='-COL-EDIT-FALSE-', layout=display_column, vertical_alignment='top')),
             Psg.Column(imu_column, vertical_alignment='top', element_justification='center')]
        ]

        return layout

    def __create_miscellaneous_row(self) -> list:
        """
        Create the bottom row of the main window. This shows extra information about what is happening during the
        running of the program.

        Returns:
            layout (list): Layout in the form of a list.
        """
        frame_rate_details = [
            [Psg.T(text=' GUI: ', justification='right', font=st.FONT_INFO, p=(0, 0), relief=Psg.RELIEF_SUNKEN,
                   border_width=2),
             Psg.T(k='-T-GUI-RATE-', text='0', justification='center', font=st.FONT_INFO,
                   s=(4, 1), p=(0, 0), relief=Psg.RELIEF_SUNKEN, border_width=2),
             Psg.T(text=' Resize: ', justification='right', font=st.FONT_INFO, p=(0, 0), relief=Psg.RELIEF_SUNKEN,
                   border_width=2),
             Psg.T(k='-T-RESIZE-RATE-', text='0', justification='center', font=st.FONT_INFO,
                   s=(7, 1), p=(0, 0), relief=Psg.RELIEF_SUNKEN, border_width=2),
             Psg.T(text=' Memory: ', justification='right', font=st.FONT_INFO, p=(0, 0), relief=Psg.RELIEF_SUNKEN,
                   border_width=2),
             Psg.T(k='-T-MEMORY-', text='0 fps', justification='center', font=st.FONT_INFO,
                   s=(9, 1), p=(0, 0), relief=Psg.RELIEF_SUNKEN, border_width=2)
             ]
        ]

        layout = [
            [frame_rate_details]
        ]

        return layout

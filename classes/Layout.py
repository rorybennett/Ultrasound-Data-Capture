"""
Class for handling all layouts used in DataCaptureDisplay. This class is intended to clean up the DataCaptureDisplay
class to make the code more readable. Future layout updates should be easier with the separation.

There are two primary layouts. Since PySimpleGUI is not dynamic it is not really possible to swap out layouts. As such,
when going into and out of editing mode the window is closed and a new window with the required layout is opened.

Currently, two functions are available:
    1. getInitialLayout     -       Returns the initial layout. This layout does not have editing details on display.
    2. getEditingLayout     -       Returns the layout with editing elements available. The recording elements are
                                    now removed.
"""
import constants as c
import styling as st
import PySimpleGUI as sg

# Keys used for the basic navigation of frames.
NAVIGATION_KEYS = [
    '-BUTTON-NAV-PPP-',
    '-BUTTON-NAV-PP-',
    '-BUTTON-NAV-P-',
    '-BUTTON-NAV-N-',
    '-BUTTON-NAV-NN-',
    '-BUTTON-NAV-NNN-'
]


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
            [sg.Menu(key='-MENU-', menu_definition=self.menu.getMenu())],
            [displayRow],
            [sg.HSep(pad=((0, 0), (0, 10)))],
            [recordRow],
            [sg.HSep(pad=((0, 0), (0, 10)))],
            [miscellaneousRow]
        ]

        return layout

    def getEditingLayout(self) -> list:
        """
        Create the editing layout. Recording is disabled in this layout. There are three primary sections to this layout:

        1. Display Row:         Contains the Image element where the frame is displayed and the Canvas where the
                                orientation plot is displayed.
        2. Editing Row:         Contains buttons and text views that enable editing functions and editing details to
                                be displayed.
        3. Miscellaneous Row:   A final row to show some extra information about what is happening in the window.

        Returns:
            layout (list): Layout in the form of a list.
        """
        displayRow = self.__createDisplayRow(enableEditing=True)

        editRow = self.__createEditingRow()

        miscellaneousRow = self.__createMiscellaneousRow()

        layout = [
            [sg.Menu(key='-MENU-', menu_definition=self.menu.getMenu())],
            [displayRow],
            [sg.HSep(pad=((0, 0), (0, 10)))],
            [editRow],
            [sg.HSep(pad=((0, 0), (0, 10)))],
            [miscellaneousRow]
        ]

        return layout

    def __createEditingRow(self) -> list:
        """
        Create the editing row of the main window. This is a work in progress.

        Returns:
            layout (list): Layout in the form of a list.
        """
        selectColumn = [
            [sg.Text('Select Recording', font=st.DESC_FONT, pad=((0, 0), (0, 10)), justification='center',
                     expand_x=True)],
            [sg.HSeparator()],
            [sg.Combo(key='-COMBO-RECORDINGS-', size=21, font=st.COMBO_FONT_SMALL, values=[], enable_events=True,
                      readonly=True)]
        ]

        detailsColumn = [
            [sg.Text('Recording Details', font=st.DESC_FONT, pad=((0, 0), (0, 10)), expand_x=True,
                     justification='center')],
            [sg.HSeparator()],
            [sg.Text('Date:', font=st.DESC_FONT, pad=((0, 0), (0, 0)), justification='left', size=(10, 1)),
             sg.Text(key='-TEXT-DETAILS-DATE-', font=st.DESC_FONT, justification='right', size=(12, 2))],
            [sg.Text('Duration:', font=st.DESC_FONT, pad=((0, 0), (0, 0)), justification='left', size=(10, 1)),
             sg.Text(key='-TEXT-DETAILS-DURATION-', font=st.DESC_FONT, expand_x=True, justification='right')],
            [sg.Text('Frames:', font=st.DESC_FONT, pad=((0, 0), (0, 0)), justification='left'),
             sg.Text(key='-TEXT-DETAILS-FRAMES-', font=st.DESC_FONT, expand_x=True, justification='right')],
            [sg.Text('IMU Data Points:', font=st.DESC_FONT, pad=((0, 0), (0, 0)), justification='left'),
             sg.Text(key='-TEXT-DETAILS-POINTS-', font=st.DESC_FONT, expand_x=True, justification='right')],
            [sg.Text('Estimated FPS:', font=st.DESC_FONT, pad=((0, 0), (0, 0)), justification='left'),
             sg.Text(key='-TEXT-DETAILS-FPS-', font=st.DESC_FONT, expand_x=True, justification='right')]
        ]

        navigationColumn = [
            [sg.Text('Navigation', font=st.DESC_FONT, pad=((0, 0), (0, 10)), expand_x=True,
                     justification='center')],
            [sg.HSeparator()],
            [sg.Button(key=NAVIGATION_KEYS[0], button_text='-10', size=(3, 1), font=st.BUTTON_FONT_SMALL,
                       border_width=3, disabled=True),
             sg.Button(key=NAVIGATION_KEYS[1], button_text='-5', size=(3, 1), font=st.BUTTON_FONT_SMALL, border_width=3,
                       disabled=True),
             sg.Button(key=NAVIGATION_KEYS[2], button_text='-1', size=(3, 1), font=st.BUTTON_FONT_SMALL, border_width=3,
                       disabled=True),
             sg.Button(key=NAVIGATION_KEYS[3], button_text='+1', size=(3, 1), font=st.BUTTON_FONT_SMALL, border_width=3,
                       disabled=True),
             sg.Button(key=NAVIGATION_KEYS[4], button_text='+5', size=(3, 1), font=st.BUTTON_FONT_SMALL, border_width=3,
                       disabled=True),
             sg.Button(key=NAVIGATION_KEYS[5], button_text='+10', size=(3, 1), font=st.BUTTON_FONT_SMALL,
                       border_width=3, disabled=True),
             ],
            [sg.Text('Go to frame:', font=st.DESC_FONT, pad=((0, 0), (0, 0)), expand_x=True, justification='left'),
             sg.Input(key='-INPUT-NAV-GOTO-', font=st.DESC_FONT, justification='center', size=(9, 1), disabled=True)]
        ]

        editingDetails1 = [
            [sg.Button(key='-BUTTON-OFFSET-TOP-', button_text='Set Top Offset', font=st.BUTTON_FONT_SMALL,
                       expand_x=True, disabled=True, border_width=3)],
            [sg.Button(key='-BUTTON-OFFSET-BOTTOM-', button_text='Set Bottom Offset', font=st.BUTTON_FONT_SMALL,
                       expand_x=True, disabled=True, border_width=3)],
            [sg.Button(key='-BUTTON-OFFSET-LEFT-', button_text='Set Left Offset', font=st.BUTTON_FONT_SMALL,
                       expand_x=True, disabled=True, border_width=3)],
            [sg.Button(key='-BUTTON-OFFSET-RIGHT-', button_text='Set Right Offset', font=st.BUTTON_FONT_SMALL,
                       expand_x=True, disabled=True, border_width=3)],
            [sg.Text('Frame Scan Depth:', font=st.DESC_FONT, pad=((0, 0), (0, 0)), expand_x=True, justification='left'),
             sg.Input(key='-INPUT-EDIT-DEPTH-', font=st.DESC_FONT, justification='center', size=(9, 1), disabled=True)],
            [sg.Text('Set All Scan Depths:', font=st.DESC_FONT, pad=((0, 0), (0, 0)), expand_x=True, justification='left'),
             sg.Input(key='-INPUT-EDIT-DEPTHS-', font=st.DESC_FONT, justification='center', size=(9, 1), disabled=True)]
        ]

        editingDetails2 = [
            [sg.Button(key='-BUTTON-POINTS-', button_text='Add Points', font=st.BUTTON_FONT_SMALL, disabled=True,
                       expand_x=True, border_width=3)]
        ]

        editingDetailsColumn = [
            [sg.Text('Editing Details', font=st.DESC_FONT, pad=((0, 0), (0, 10)), expand_x=True,
                     justification='center')],
            [sg.HSeparator()],
            [sg.Column(editingDetails1, vertical_alignment='top'),
             sg.Column(editingDetails2, vertical_alignment='top')]

        ]

        layout = [
            [sg.Column(selectColumn, vertical_alignment='top'),
             sg.Column(detailsColumn),
             sg.Column(navigationColumn, vertical_alignment='top'),
             sg.Column(editingDetailsColumn, expand_x=True, vertical_alignment='top', pad=(0, 0))],
            [sg.Text('Path:', font=st.INFO_TEXT, pad=((0, 0), (0, 0))),
             sg.Text(key='-TEXT-DETAILS-PATH-', font=st.INFO_TEXT + ' underline', text_color='blue',
                     click_submits=True)]
        ]

        return layout

    def __createDisplayRow(self, enableEditing: bool = False) -> list:
        """
        Create the display row of the main window. This contains the image that displays frames and the plot that
        shows the orientation of the IMU, along with some buttons and text information. The frame is displayed
        using an Image element when recording form a signal, and a Graph element during editing, based on
        enableEditing.

        Args:
            enableEditing (bool): If editing is enabled changes to the display column are made.

        Returns:
            layout (list): Layout in the form of a list.
        """
        if enableEditing:
            displayColumn = [
                [sg.Graph(key='-GRAPH-FRAME-', canvas_size=c.DEFAULT_DISPLAY_DIMENSIONS, background_color='#000000',
                          pad=(0, 0), graph_bottom_left=(0, 0), graph_top_right=c.DEFAULT_DISPLAY_DIMENSIONS,
                          enable_events=True)],
                [sg.Text(key='-TEXT-NAV-CURRENT-', text='____/____', font=st.INFO_TEXT, justification='right',
                         expand_x=True)]
            ]
        else:
            displayColumn = [
                [sg.Image(key='-IMAGE-FRAME-', size=c.DEFAULT_DISPLAY_DIMENSIONS, background_color='#000000',
                          pad=(0, 0))],
                [sg.Text(key='-TEXT-SIGNAL-DIMENSIONS-', text='Signal Dimensions: ', font=st.INFO_TEXT, expand_x=True,
                         justification='left', pad=(0, 0)),
                 sg.Text(text=' Signal FPS: ', justification='right', font=st.INFO_TEXT, pad=(0, 0)),
                 sg.Text(key='-TEXT-SIGNAL-RATE-', text='0', justification='center', font=st.INFO_TEXT, size=(3, 1),
                         pad=(0, 0))]
            ]

        imuColumn = [
            [sg.Text('IMU Acc:', font=st.DESC_FONT, pad=((5, 0), (10, 0))),
             sg.Text(key='-TEXT-ACCELERATION-X-', text='', font=st.DESC_FONT, justification='right', size=(8, 1),
                     pad=((0, 0), (10, 0))),
             sg.Text(key='-TEXT-ACCELERATION-Y-', text='', font=st.DESC_FONT, justification='right', size=(8, 1),
                     pad=((0, 0), (10, 0))),
             sg.Text(key='-TEXT-ACCELERATION-Z-', text='', font=st.DESC_FONT, justification='right', size=(8, 1),
                     pad=((0, 0), (10, 0)))],
            [sg.Canvas(key='-CANVAS-PLOT-')],
            [sg.Slider(key='-SLIDER-AZIMUTH-', range=(0, 360), default_value=c.DEFAULT_AZIMUTH, size=(30, 10),
                       orientation='h', enable_events=True, pad=((0, 0), (0, 15)))],
            [sg.Button(key='-BUTTON-PLOT-TOGGLE-', button_text='Disable Plotting', size=(15, 1), font=st.BUTTON_FONT,
                       border_width=3, pad=((0, 0), (0, 5)), button_color=st.BUTTON_ACTIVE)],
            [sg.Button(key='-BUTTON-DISPLAY-TOGGLE-', button_text='Disable Display', size=(15, 1), font=st.BUTTON_FONT,
                       border_width=3, pad=((0, 0), (5, 0)), button_color=st.BUTTON_ACTIVE)]
        ]

        layout = [
            [sg.pin(sg.Column(key='-COL-EDIT-FALSE-', layout=displayColumn, vertical_alignment='top')),
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
            [sg.Text(text='Record Start', font=st.DESC_FONT)],
            [sg.Text(key='-TEXT-RECORD-START-', text='--:--:--', font=st.DESC_FONT, size=(12, 1),
                     justification='center')]
        ]

        recordEndColumn = [
            [sg.Text(text='Record End', font=st.DESC_FONT)],
            [sg.Text(key='-TEXT-RECORD-END-', text='--:--:--', font=st.DESC_FONT, size=(12, 1), justification='center')]
        ]

        recordElapsedColumn = [
            [sg.Text(text='Elapsed Time', font=st.DESC_FONT)],
            [sg.Text(key='-TEXT-RECORD-ELAPSED-', text='--:--:--', font=st.DESC_FONT, size=(12, 1),
                     justification='center')]
        ]

        recordFramesColumn = [
            [sg.Text(text='Frames saved', font=st.DESC_FONT)],
            [sg.Text(key='-TEXT-FRAMES-SAVED-', text='0', font=st.DESC_FONT, size=(12, 1), justification='center')]
        ]

        layout = [
            [sg.Button(key='-BUTTON-SNAPSHOT-', button_text='Save Frame', size=(15, 1), font=st.BUTTON_FONT,
                       border_width=3, pad=((0, 20), (0, 0)), disabled=True),
             sg.Button(key='-BUTTON-RECORD-TOGGLE-', button_text='Start Recording', size=(15, 1), font=st.BUTTON_FONT,
                       border_width=3, pad=((0, 0), (0, 0)), disabled=True),
             sg.Column(recordStartColumn, element_justification='center', pad=(0, 0)),
             sg.Column(recordEndColumn, element_justification='center', pad=(0, 0)),
             sg.Column(recordElapsedColumn, element_justification='center', pad=(0, 0)),
             sg.Column(recordFramesColumn, element_justification='center', pad=(0, 0))]
        ]

        return layout

    def getImuWindowLayout(self, availableComPorts, comPort, baudRate) -> list:
        """
        Function that creates the layout for the IMU connection window.

        Args:
            availableComPorts (list): A list of available COM ports.
            comPort (string): Default COM port to show in COMBO box.
            baudRate (int): Default baud rate to show in COMBO box.

        Returns:
            layout (list): Layout in the form of a list.
        """
        layout = [
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

        return layout

    def __createMiscellaneousRow(self) -> list:
        """
        Create the bottom row of the main window. This shows extra information about what is happening during the
        running of the program.

        Returns:
            layout (list): Layout in the form of a list.
        """
        frameRateDetails = [
            [sg.Text(text='GUI: ', justification='right', font=st.INFO_TEXT, pad=(0, 0), relief=sg.RELIEF_SUNKEN,
                     border_width=2),
             sg.Text(key='-TEXT-GUI-RATE-', text='0', justification='center', font=st.INFO_TEXT,
                     size=(4, 1), pad=(0, 0), relief=sg.RELIEF_SUNKEN, border_width=2),
             sg.Text(text=' Resize: ', justification='right', font=st.INFO_TEXT, pad=(0, 0), relief=sg.RELIEF_SUNKEN,
                     border_width=2),
             sg.Text(key='-TEXT-RESIZE-RATE-', text='0', justification='center', font=st.INFO_TEXT,
                     size=(3, 1), pad=(0, 0), relief=sg.RELIEF_SUNKEN, border_width=2)]
        ]

        layout = [
            [frameRateDetails]
        ]

        return layout

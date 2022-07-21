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
NAV_KEYS = [
    '-BTN-NAV-PPP-',
    '-BTN-NAV-PP-',
    '-BTN-NAV-P-',
    '-BTN-NAV-N-',
    '-BTN-NAV-NN-',
    '-BTN-NAV-NNN-'
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
            [sg.Menu(k='-MENU-', menu_definition=self.menu.getMenu())],
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
            [sg.Menu(k='-MENU-', menu_definition=self.menu.getMenu())],
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
            [sg.Text('Select Recording', font=st.FONT_DESCR, pad=((0, 0), (0, 10)), justification='center',
                     expand_x=True)],
            [sg.HSeparator()],
            [sg.Combo(k='-COMBO-RECORDINGS-', size=21, font=st.FONT_COMBO_SMALL, values=[], enable_events=True,
                      readonly=True)]
        ]

        detailsColumn = [
            [sg.Text('Recording Details', font=st.FONT_DESCR, pad=((0, 0), (0, 10)), expand_x=True,
                     justification='center')],
            [sg.HSeparator()],
            [sg.Text('Date:', font=st.FONT_DESCR, pad=((0, 0), (0, 0)), justification='left', size=(10, 1)),
             sg.Text(k='-TXT-DETAILS-DATE-', font=st.FONT_DESCR, justification='right', size=(12, 2))],
            [sg.Text('Duration:', font=st.FONT_DESCR, pad=((0, 0), (0, 0)), justification='left', size=(10, 1)),
             sg.Text(k='-TXT-DETAILS-DURATION-', font=st.FONT_DESCR, expand_x=True, justification='right')],
            [sg.Text('IMU Data Points:', font=st.FONT_DESCR, pad=((0, 0), (0, 0)), justification='left'),
             sg.Text(k='-TXT-DETAILS-POINTS-', font=st.FONT_DESCR, expand_x=True, justification='right')],
            [sg.Text('Estimated FPS:', font=st.FONT_DESCR, pad=((0, 0), (0, 0)), justification='left'),
             sg.Text(k='-TXT-DETAILS-FPS-', font=st.FONT_DESCR, expand_x=True, justification='right')]
        ]

        navigationColumn = [
            [sg.Text('Navigation', font=st.FONT_DESCR, pad=((0, 0), (0, 10)), expand_x=True,
                     justification='center')],
            [sg.HSeparator()],
            [sg.Button(k=NAV_KEYS[0], button_text='-10', size=(3, 1), font=st.FONT_BTN_SMALL, border_width=3,
                       disabled=True),
             sg.Button(k=NAV_KEYS[1], button_text='-5', size=(3, 1), font=st.FONT_BTN_SMALL, border_width=3,
                       disabled=True),
             sg.Button(k=NAV_KEYS[2], button_text='-1', size=(3, 1), font=st.FONT_BTN_SMALL, border_width=3,
                       disabled=True),
             sg.Button(k=NAV_KEYS[3], button_text='+1', size=(3, 1), font=st.FONT_BTN_SMALL, border_width=3,
                       disabled=True),
             sg.Button(k=NAV_KEYS[4], button_text='+5', size=(3, 1), font=st.FONT_BTN_SMALL, border_width=3,
                       disabled=True),
             sg.Button(k=NAV_KEYS[5], button_text='+10', size=(3, 1), font=st.FONT_BTN_SMALL,
                       border_width=3, disabled=True)
             ],
            [sg.Text('Go to frame:', font=st.FONT_DESCR, expand_x=True, justification='left'),
             sg.Input(k='-INP-NAV-GOTO-', font=st.FONT_DESCR, justification='center', size=(9, 1), disabled=True)]
        ]

        editingDetails1 = [
            [sg.Button(k='-BTN-OFFSET-TOP-', button_text='Set Top Offset', font=st.FONT_BTN_SMALL,
                       expand_x=True, disabled=True, border_width=3)],
            [sg.Button(k='-BTN-OFFSET-BOTTOM-', button_text='Set Bottom Offset', font=st.FONT_BTN_SMALL,
                       expand_x=True, disabled=True, border_width=3)],
            [sg.Button(k='-BTN-OFFSET-LEFT-', button_text='Set Left Offset', font=st.FONT_BTN_SMALL,
                       expand_x=True, disabled=True, border_width=3)],
            [sg.Button(k='-BTN-OFFSET-RIGHT-', button_text='Set Right Offset', font=st.FONT_BTN_SMALL,
                       expand_x=True, disabled=True, border_width=3)]
        ]

        editingDetails2 = [
            [sg.Button(k='-BTN-POINTS-', button_text='Add Points', font=st.FONT_BTN_SMALL, disabled=True,
                       expand_x=True, border_width=3)],
            [sg.Button(k='-BTN-CLEAR-FRAME-', button_text='Clear Frame', font=st.FONT_BTN_SMALL, disabled=True,
                       expand_x=True, border_width=3)],
            [sg.Button(k='-BTN-CLEAR-ALL-', button_text='Clear All', font=st.FONT_BTN_SMALL, disabled=True,
                       expand_x=True, border_width=3)],
            [sg.Text(k='-TXT-TOTAL-POINTS-', text='Total Points: ', font=st.FONT_DESCR, expand_x=True,
                     justification='center', size=(17, 1))]
        ]

        editingDetails3 = [
            [sg.Text('Scan Depth [mm]:', font=st.FONT_DESCR, expand_x=True, justification='left'),
             sg.Input(k='-INP-EDIT-DEPTH-', font=st.FONT_DESCR, justification='center', size=(9, 1),
                      disabled=True)],
            [sg.Text('All Scan Depths [mm]:', font=st.FONT_DESCR, expand_x=True, justification='left'),
             sg.Input(k='-INP-EDIT-DEPTHS-', font=st.FONT_DESCR, justification='center', size=(9, 1),
                      disabled=True)],
            [sg.Text('IMU Offset [mm]:', font=st.FONT_DESCR, expand_x=True, justification='left'),
             sg.Input(k='-INP-IMU-OFFSET-', font=st.FONT_DESCR, justification='center', size=(9, 1),
                      disabled=True)]
        ]

        editingDetails4 = [
            [sg.Button(k='-BTN-BULLET-L-', button_text='Bullet Length', font=st.FONT_BTN_SMALL, expand_x=True,
                       disabled=True, border_width=3)],
            [sg.Button(k='-BTN-BULLET-W-', button_text='Bullet Width', font=st.FONT_BTN_SMALL, expand_x=True,
                       disabled=True, border_width=3)],
            [sg.Button(k='-BTN-BULLET-H-', button_text='Bullet Height', font=st.FONT_BTN_SMALL, expand_x=True,
                       disabled=True, border_width=3)],
            [sg.Button(k='-BTN-BULLET-CLEAR-', button_text='Clear Bullet', font=st.FONT_BTN_SMALL, expand_x=True,
                       disabled=True, border_width=3)],
            [sg.Button(k='-BTN-BULLET-PRINT-', button_text='Print Bullet', font=st.FONT_BTN_SMALL, expand_x=True,
                       disabled=True, border_width=3)]
        ]

        editingDetails5 = [
            [sg.Button(k='-BTN-ELLIPSE-1-', button_text='2D Ellipse', font=st.FONT_BTN_SMALL, expand_x=True,
                       disabled=True, border_width=3)],
            [sg.Button(k='-BTN-ELLIPSE-2-', button_text='3D Ellipse', font=st.FONT_BTN_SMALL, expand_x=True,
                       disabled=True, border_width=3)],
        ]

        editingDetailsColumn = [
            [sg.Text('Editing Details', font=st.FONT_DESCR, pad=((0, 0), (0, 10)), expand_x=True,
                     justification='center')],
            [sg.HSeparator()],
            [sg.Column(editingDetails1, vertical_alignment='top', pad=(0, 0)),
             sg.Column(editingDetails2, vertical_alignment='top', pad=(0, 0)),
             sg.Column(editingDetails3, vertical_alignment='top', pad=(0, 0)),
             sg.Column(editingDetails4, vertical_alignment='top', pad=(0, 0)),
             sg.Column(editingDetails5, vertical_alignment='top', pad=(0, 0)),
             ]
        ]

        layout = [
            [sg.Column(selectColumn, vertical_alignment='top', pad=(0, 0)),
             sg.Column(detailsColumn, vertical_alignment='top', pad=(0, 0)),
             sg.Column(navigationColumn, vertical_alignment='top', pad=(0, 0)),
             sg.Column(editingDetailsColumn, expand_x=True, vertical_alignment='top', pad=(0, 0))],
            [sg.Text('Path:', font=st.FONT_INFO, pad=((0, 0), (0, 0))),
             sg.Text(k='-TXT-DETAILS-PATH-', font=st.FONT_INFO + ' underline', text_color='blue',
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
                [sg.Graph(k='-GRAPH-FRAME-', canvas_size=c.DISPLAY_DIMENSIONS, background_color='#000000',
                          pad=(0, 0), graph_bottom_left=(0, 0), graph_top_right=c.DISPLAY_DIMENSIONS,
                          enable_events=True)],
                [sg.Text(k='-TXT-NAV-CURRENT-', text='____/____', font=st.FONT_DESCR, justification='right',
                         expand_x=True)]
            ]

            imuColumn = [
                [sg.Text('Frame Orientation', font=st.FONT_DESCR, pad=((0, 0), (10, 0)), expand_x=True,
                         justification='center')],
                [sg.Text(k='-TXT-ANGLES-', text='', font=st.FONT_DESCR, justification='center', expand_x=True,
                         pad=((0, 0), (10, 0)))],
                [sg.Canvas(k='-CANVAS-PLOT-')]
            ]
        else:
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
                [sg.Text(k='-TXT-IMU-ACC-', text='', font=st.FONT_DESCR, justification='center', expand_x=True)],
                [sg.Canvas(k='-CANVAS-PLOT-')],
                [sg.Slider(k='-SLIDER-AZIMUTH-', range=(0, 360), default_value=c.AZIMUTH, size=(30, 10),
                           orientation='h', enable_events=True, pad=((0, 0), (0, 15)))],
                [sg.Button(k='-BTN-PLOT-TOGGLE-', button_text='Disable Plotting', size=(15, 1),
                           font=st.FONT_BTN,
                           border_width=3, pad=((0, 0), (0, 5)), button_color=st.COL_BTN_ACTIVE)],
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

    def getImuWindowLayout(self, availableComPorts, comPort, baudRate) -> list:
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

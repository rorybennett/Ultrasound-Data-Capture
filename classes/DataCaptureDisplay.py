"""
Main class for capturing frames from the output of an ultrasound scanner and adding IMU orientation data to the frames.
Once a recording has been made, it can be edited. Editing involves setting the scan depth, marking the offset between
the top of the frame and the start of the scan, and adding data points that will be used in volume estimation.
"""
import styling as st
import utils as ut
from classes import IMU
from classes import FrameGrabber
import constants as c
from classes import Menu
from classes import Layout
from classes.RecordingDetails import RecordingDetails

import PySimpleGUI as sg
import time
from matplotlib.figure import Figure
from concurrent.futures import ThreadPoolExecutor


class DataCaptureDisplay:
    def __init__(self):
        # Create initial directories for storing data.
        self.singleFramesPath, self.videosPath = ut.createInitialDirectories()
        # Menu object.
        self.menu = Menu.Menu()
        # Layout object.
        self.layout = Layout.Layout(self.menu)
        # Record state of the program.
        self.enableRecording = False
        # Directory where recorded frames are stored.
        self.currentRecordingPath = None
        # Path to data.txt file where IMU data of recording is saved.
        self.currentDataFilePath = None
        # File for saving IMU data of recording.
        self.currentDataFile = None
        # Save a single frame.
        self.saveSingleFrame = False
        # Counter for labelling frame number in a recording.
        self.frameGrabCounter = 1
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
        # Plotting variables: axis, points, lines, fig_agg, and bg set to None until initialised.
        self.ax = None
        self.pointData = None
        self.lineData = None
        self.fig_agg = None
        self.bg = None
        # Threading executor.
        self.threadExecutor = ThreadPoolExecutor()
        # Recording variables for storing (signal and IMU).
        self.frameRaw = None
        self.acceleration = None
        self.quaternion = None
        # Is frame available for resize?
        self.resizeFrame = False
        # Must the frame be saved?
        self.saveFrame = False
        # Time a recording was started.
        self.recordStartTime = None
        # Editing state.
        self.enableEditing = False
        # RecordingDetails object.
        self.recordingDetails = None
        # Do Graph clicks add data points?
        self.enableDataPoints = False
        # Should a Graph click change the offset?
        self.enableOffsetChangeTop = False
        self.enableOffsetChangeBottom = False

        # IMU connect window
        self.windowImuConnect = None

        self.windowMain = sg.Window('Ultrasound Data Capture', self.layout.getMainWindowLayout(), finalize=True)

        # Enter key bindings for input elements.
        self.windowMain['-INPUT-NAV-GOTO-'].bind('<Return>', '_Enter')
        self.windowMain['-INPUT-EDIT-DEPTH-'].bind('<Return>', '_Enter')

        # Create the initial plot.
        self.createPlot(c.DEFAULT_AZIMUTH)

        self.run()

    def run(self):
        """
        Main loop/thread for displaying the GUI and reacting to events, in standard PySimpleGUI fashion.
        """
        while True:
            guiFps1 = time.time()
            # Update recording times.
            if self.enableRecording:
                self.updateTimes()
            # Update IMU values if present.
            if self.imu.isConnected and self.imu.acceleration:
                self.windowMain['-TEXT-ACCELERATION-X-'].update(f'{self.imu.acceleration[0]:.4f}')
                self.windowMain['-TEXT-ACCELERATION-Y-'].update(f'{self.imu.acceleration[1]:.4f}')
                self.windowMain['-TEXT-ACCELERATION-Z-'].update(f'{self.imu.acceleration[2]:.4f}')

            event, values = self.windowMain.read(timeout=100)

            if event in [sg.WIN_CLOSED, 'None']:
                # On window close clicked.
                self.close()
                break

            # Event for updating Image frame (recording).
            if event == '-UPDATE-IMAGE-FRAME-':
                self.windowMain['-IMAGE-FRAME-'].update(data=values[event])

            # Event for updating Graph frame (editing).
            if event == '-UPDATE-GRAPH-FRAME-':
                self.windowMain['-GRAPH-FRAME-'].draw_image(data=values[event],
                                                            location=(0, c.DEFAULT_DISPLAY_DIMENSIONS[1]))

            # Signal source menu events.
            if event.endswith('::-MENU-SIGNAL-CONNECT-'):
                self.setSignalSourceAndConnect(int(event.split('::')[0]))
            elif event.endswith('::-MENU-SIGNAL-DISCONNECT-'):
                self.frameGrabber.disconnect()
                self.updateMenus()
            elif event.endswith('::-MENU-SIGNAL-DIMENSIONS-'):
                self.changeSignalDimensions(event.split('::')[0].split('x'))

            # IMU menu events.
            if event.endswith('::-MENU-IMU-CONNECT-'):
                self.showImuConnectWindow()
            elif event.endswith('::-MENU-IMU-DISCONNECT-'):
                self.imu.disconnect()
                self.updateMenus()
            elif event.endswith('::-MENU-IMU-RATE-'):
                self.imu.setReturnRate(float(event.split('Hz')[0]))
            elif event.endswith('::-MENU-IMU-CALIBRATE-'):
                self.imu.calibrateAcceleration()

            # Signal Display Events.
            if event == '-BUTTON-DISPLAY-TOGGLE-':
                self.toggleDisplay()
            elif event == '-BUTTON-SNAPSHOT-':
                ut.saveSingleFrame(self.frameRaw, f'{self.singleFramesPath}\\{int(time.time() * 1000)}.png')
            elif event == '-BUTTON-RECORD-TOGGLE-':
                self.toggleRecording()

            # IMU Display Events.
            if event == '-SLIDER-AZIMUTH-':
                self.setAzimuth(int(values['-SLIDER-AZIMUTH-']))
            elif event == '-BUTTON-PLOT-TOGGLE-':
                self.togglePlotting()

            # Thread events.
            if event == '-THREAD-SIGNAL-RATE-':
                self.windowMain['-TEXT-SIGNAL-RATE-'].update(f'{values[event]}')
            elif event == '-THREAD-RESIZE-RATE-':
                self.windowMain['-TEXT-RESIZE-RATE-'].update(f'{values[event]}')
            elif event == '-THREAD-FRAMES-SAVED-':
                self.windowMain['-TEXT-FRAMES-SAVED-'].update(f'{values[event]}')
            elif event == '-THREAD-PLOT-':
                self.fig_agg.blit(self.ax.bbox)
                self.fig_agg.flush_events()

            # Editing events.
            if event == '-BUTTON-EDIT-TOGGLE-':
                self.toggleEditing()
            elif event == '-COMBO-RECORDINGS-':
                self.selectRecordingForEdit(values[event])
            elif event == '-TEXT-DETAILS-PATH-' and self.recordingDetails:
                ut.openWindowsExplorer(self.recordingDetails.path)
            elif event in Layout.NAVIGATION_KEYS:
                self.navigateFrames(event.split('-')[-2])
            elif event == '-INPUT-NAV-GOTO-' + '_Enter':
                self.navigateFrames(values['-INPUT-NAV-GOTO-'])
            elif event == '-BUTTON-OFFSET-TOP-':
                self.toggleChangingOffsetTop()
            elif event == '-BUTTON-OFFSET-BOTTOM-':
                self.toggleChangingOffsetBottom()
            elif event == '-INPUT-EDIT-DEPTH-' + '_Enter':
                self.recordingDetails.changeScanDepth(values['-INPUT-EDIT-DEPTH-'])
            elif event == '-BUTTON-POINTS-':
                self.toggleAddingDataPoints()
            elif event == '-GRAPH-FRAME-':
                self.onGraphFrameClicked(values[event])

            # GUI frame rate estimate.
            guiDt = time.time() - guiFps1
            guiFps = int(1 / guiDt) if guiDt > 0.00999 else '100+'

            self.windowMain['-TEXT-GUI-RATE-'].update(f'{guiFps}' if not self.enableEditing else '0')

    def onGraphFrameClicked(self, point):
        """
        Click handler function for when the Graph frame element is clicked. If enableDataPoints then a new data point
        is added or removed (if within proximity of existing point) to the frame, if enableOffsetChangeTop then the
        vertical portion of the point is used as the new top offset value, if enableOffsetChangeBottom then the vertical
        portion of the point is used as the new bottom offset value.

        Args:
            point: Coordinates of where the Graph element was clicked.
        """

        if self.enableDataPoints:
            self.recordingDetails.addRemovePointData(point)
            self.windowMain.write_event_value('-UPDATE-GRAPH-FRAME-',
                                              self.recordingDetails.getCurrentFrameAsBytes())
        elif self.enableOffsetChangeTop:
            self.recordingDetails.changeOffsetTop(c.DEFAULT_DISPLAY_DIMENSIONS[1] - point[1])
            self.windowMain.write_event_value('-UPDATE-GRAPH-FRAME-',
                                              value=self.recordingDetails.getCurrentFrameAsBytes())
        elif self.enableOffsetChangeBottom:
            self.recordingDetails.changeOffsetBottom(c.DEFAULT_DISPLAY_DIMENSIONS[1] - point[1])
            self.windowMain.write_event_value('-UPDATE-GRAPH-FRAME-',
                                              value=self.recordingDetails.getCurrentFrameAsBytes())

    def navigateFrames(self, navCommand):
        """
        Call the navigateFrames function of the RecordingDetails object to change the current frame as required,
        then update the window with the new details after the frame. The navCommand is a string that can either be
        converted to an integer for a specific frame number or a navigation command:
            str -   String representation of frame number.
            PPP -   Move back 10 frames.
            PP  -   Move back 5 frames.
            P   -   Move back 1 frame.
            N   -   Move forward 1 frame.
            NN  -   Move forward 5 frames.
            NNN -   Move forward 10 frames.

        Args:
            navCommand (str): String representation of the navigation command.
        """
        self.recordingDetails.navigateFrames(navCommand)

        # Set element states.
        self.windowMain['-TEXT-NAV-CURRENT-'].update(
            f'{self.recordingDetails.currentFramePosition}/{self.recordingDetails.frameCount}')
        self.windowMain['-INPUT-EDIT-DEPTH-'].update(
            f'{self.recordingDetails.depths[self.recordingDetails.currentFramePosition - 1]}')

        self.windowMain.write_event_value('-UPDATE-GRAPH-FRAME-', value=self.recordingDetails.getCurrentFrameAsBytes())

    def selectRecordingForEdit(self, videoDirectory: str):
        """
        Update main window to allow editing of the selected recording. This creates the recordingDetails object and
        sets the elements to the correct states. The first frame from the recording is shown in the display and
        the details of the recording are displayed.

        Args:
            videoDirectory (str): Directory name where the recording is stored.
        """
        print(f'Create editing data for: {videoDirectory}')
        self.recordingDetails = RecordingDetails(self.videosPath, videoDirectory)
        self.enableOffsetChangeTop = False
        self.enableOffsetChangeBottom = False
        self.enableDataPoints = False

        # self.recordingDetails.plotDataPointsOnAxis(self.ax)

        # Set element states
        self.windowMain['-TEXT-DETAILS-DATE-'].update(self.recordingDetails.date)
        self.windowMain['-TEXT-DETAILS-PATH-'].update(self.recordingDetails.path)
        self.windowMain['-TEXT-DETAILS-DURATION-'].update(
            time.strftime('%H:%M:%S', time.localtime(self.recordingDetails.duration / 1000)))
        self.windowMain['-TEXT-DETAILS-FRAMES-'].update(self.recordingDetails.frameCount)
        self.windowMain['-TEXT-DETAILS-POINTS-'].update(self.recordingDetails.imuCount)
        self.windowMain['-TEXT-DETAILS-FPS-'].update(self.recordingDetails.fps)
        [self.windowMain[i].update(disabled=False) for i in Layout.NAVIGATION_KEYS]
        self.windowMain['-INPUT-NAV-GOTO-'].update(disabled=False)
        self.windowMain['-TEXT-NAV-CURRENT-'].update(
            f'{self.recordingDetails.currentFramePosition}/{self.recordingDetails.frameCount}')
        self.windowMain['-BUTTON-OFFSET-TOP-'].update(disabled=False, button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BUTTON-OFFSET-BOTTOM-'].update(disabled=False, button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-INPUT-EDIT-DEPTH-'].update(
            f'{self.recordingDetails.depths[self.recordingDetails.currentFramePosition - 1]}', disabled=False)
        self.windowMain['-BUTTON-POINTS-'].update(disabled=False, button_color=sg.DEFAULT_BUTTON_COLOR)

        self.windowMain.write_event_value('-UPDATE-GRAPH-FRAME-', value=self.recordingDetails.getCurrentFrameAsBytes())

    def toggleChangingOffsetTop(self):
        """
        Toggle the state of self.enableOffsetChangeTop to enable or disable changing of the top frame offset value.
        """
        self.enableOffsetChangeTop = not self.enableOffsetChangeTop
        self.enableOffsetChangeBottom = False
        self.enableDataPoints = False
        # Set element states.
        self.windowMain['-BUTTON-OFFSET-TOP-'].update(
            button_color=st.BUTTON_ACTIVE if self.enableOffsetChangeTop else sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BUTTON-OFFSET-BOTTOM-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BUTTON-POINTS-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)

    def toggleChangingOffsetBottom(self):
        """
        Toggle the state of self.enableOffsetChangeTop to enable or disable changing of the top frame offset value.
        """
        self.enableOffsetChangeBottom = not self.enableOffsetChangeBottom
        self.enableOffsetChangeTop = False
        self.enableDataPoints = False
        # Set element states.
        self.windowMain['-BUTTON-OFFSET-BOTTOM-'].update(
            button_color=st.BUTTON_ACTIVE if self.enableOffsetChangeBottom else sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BUTTON-OFFSET-TOP-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BUTTON-POINTS-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)

    def toggleAddingDataPoints(self):
        """
        Toggle the state of self.enableDataPoints to enable or disable adding data points to a frame.
        """
        self.enableDataPoints = not self.enableDataPoints
        self.enableOffsetChangeTop = False
        self.enableOffsetChangeBottom = False
        # Set element states.
        self.windowMain['-BUTTON-POINTS-'].update(
            button_color=st.BUTTON_ACTIVE if self.enableDataPoints else sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BUTTON-OFFSET-TOP-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BUTTON-OFFSET-BOTTOM-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)

    def toggleEditing(self):
        """
        Function to toggle the editing state of the program. When in editing state, the Signal Source and IMU menu items
        are disabled. The FrameGrabber object and IMU are disconnected and the plot is cleared. Some buttons are
        disabled and some are reset to default values. The display and plot are enabled for consistency.
        """
        self.enableEditing = not self.enableEditing
        # Hide the view that is not being used and show the view that is.
        self.windowMain['-COL-EDIT-TRUE-'].update(visible=self.enableEditing)
        self.windowMain['-COL-EDIT-FALSE-'].update(visible=not self.enableEditing)

        # Enable/Disable plotting for consistency.
        self.enablePlotting = False if self.enableEditing else True
        self.fig_agg.restore_region(self.bg)
        self.windowMain.write_event_value('-THREAD-PLOT-', None)

        # Enable the frame display for consistency.
        self.enableDisplay = True
        self.recordingDetails = None
        print(f'Entering editing mode: {self.enableEditing}')
        # Editing has been enabled.
        if self.enableEditing:
            if self.frameGrabber.isConnected:
                self.frameGrabber.disconnect()
            if self.imu.isConnected:
                self.imu.disconnect()
            time.sleep(0.5)

        # Set element states.
        self.updateMenus()
        # Recording elements.
        self.windowMain['-BUTTON-SNAPSHOT-'].update(disabled=True)
        self.windowMain['-BUTTON-RECORD-TOGGLE-'].update(disabled=True)
        # Plotting and display elements.
        self.windowMain['-BUTTON-DISPLAY-TOGGLE-'].update(button_color=st.BUTTON_ACTIVE,
                                                          text='Disable Display',
                                                          disabled=True if self.enableEditing else False)
        self.windowMain['-BUTTON-PLOT-TOGGLE-'].update(button_color=st.BUTTON_ACTIVE,
                                                       text='Disable Plotting',
                                                       disabled=True if self.enableEditing else False)
        # Editing elements
        self.windowMain['-BUTTON-EDIT-TOGGLE-'].update(
            text='End Editing' if self.enableEditing else 'Start Editing',
            button_color=st.BUTTON_ACTIVE if self.enableEditing else sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-COMBO-RECORDINGS-'].update(
            values=ut.getRecordingDirectories(self.videosPath) if self.enableEditing else [],
            disabled=False if self.enableEditing else True)
        [self.windowMain[i].update(disabled=True) for i in Layout.NAVIGATION_KEYS]
        self.windowMain['-INPUT-NAV-GOTO-'].update('', disabled=True)
        self.windowMain['-TEXT-NAV-CURRENT-'].update('____/____')
        self.windowMain['-BUTTON-OFFSET-TOP-'].update(disabled=True, button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BUTTON-OFFSET-BOTTOM-'].update(disabled=True, button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-INPUT-EDIT-DEPTH-'].update('', disabled=True)
        self.windowMain['-BUTTON-POINTS-'].update(disabled=True, button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-TEXT-DETAILS-DATE-'].update('')
        self.windowMain['-TEXT-DETAILS-PATH-'].update('')
        self.windowMain['-TEXT-DETAILS-DURATION-'].update('')
        self.windowMain['-TEXT-DETAILS-FRAMES-'].update('')
        self.windowMain['-TEXT-DETAILS-POINTS-'].update('')
        self.windowMain['-TEXT-DETAILS-FPS-'].update('')

        self.windowMain.write_event_value(key='-UPDATE-IMAGE-FRAME-',
                                          value=ut.pngAsBytes('icons/blank_background.png'))
        self.windowMain.write_event_value(key='-UPDATE-GRAPH-FRAME-',
                                          value=ut.pngAsBytes('icons/blank_background.png'))
        # todo: clear plot when i have access to an imu to test it

    def getFramesThread(self):
        """
        Thread for acquiring frames from FrameGrabber object. Removed from main thread to provide a more consistent
        frame rate from the signal source. As soon as a frame is acquired from the FrameGrabber object the currently
        stored IMU values are copied to local variables. This may result in a slight time delay between the frame
        and its associated IMU values, but for now it should be accurate enough. Threads seem to cause trouble
        if the while loop does nothing.

        if self.enableRecording is True, the current frame will be saved with the IMU data available.

        If self.enableDisplay is True, the new frame will be resized and displayed in the main GUI.

        This thread will run as long as the self.frameGrabber object is connected to a signal source. On disconnect
        of the signal source the thread will be closed. Joining the thread to the parent thread does not seem
        to be necessary.
        """
        print('Thread starting up: getFramesThread.')
        while True:
            # End thread if frameGrabber not connected.
            if not self.frameGrabber.isConnected:
                break
            signalFps1 = time.time()
            # Grab frame.
            res, self.frameRaw = self.frameGrabber.getFrame()
            # Successful frame read?
            if res:
                # Update data from IMU object.
                self.acceleration = self.imu.acceleration if self.imu.isConnected else [0, 0, 0]
                self.quaternion = self.imu.quaternion if self.imu.isConnected else [0, 0, 0, 0]
                # Signal frame rate estimate.
                signalDt = time.time() - signalFps1
                signalFps = int(1 / signalDt) if signalDt != 0 else 100
                self.windowMain.write_event_value(key='-THREAD-SIGNAL-RATE-', value=signalFps)
                # Record frames?
                if self.enableRecording:
                    self.saveFrame = True

                # Display enabled?
                if self.enableDisplay:
                    self.resizeFrame = True

        print('-------------------------------------------\nThread closing down: '
              'getFramesThread.\n-------------------------------------------')
        self.windowMain.write_event_value(key='-THREAD-SIGNAL-RATE-', value=0)

    def resizeFramesThread(self):
        """
        Thread for resizing a frame to be displayed in the GUI window. Removed from main thread to prevent blocking when
        resizing the frame. This is quite CPU heavy and affects all return rates. This thread is limited in its
        speed by the sleep call in the while loop. Currently, this thread is capped at 1/0.033=30Hz, any frames
        that are received during this threads sleep time are skipped over and not displayed to the user. This
        does not affect the saving of frames.


        This thread will run as long as the self.frameGrabber object is connected to a signal source, but will only
        resize a frame if the self.frameRawNew variable is set to True in the getFramesThread. On disconnect
        of the signal source the thread will be closed. Joining the thread to the parent thread does not seem
        to be necessary.
        """
        print('Thread starting up: resizeFramesThread.')
        while self.frameGrabber.isConnected:
            if self.resizeFrame:
                self.resizeFrame = False
                resizeFps1 = time.time()
                resizedFrame = ut.resizeFrame(self.frameRaw, c.DEFAULT_DISPLAY_DIMENSIONS, ut.INTERPOLATION_NEAREST)
                frameBytes = ut.frameToBytes(resizedFrame)
                self.windowMain.write_event_value(key='-UPDATE-IMAGE-FRAME-', value=frameBytes)
                # Resize frame rate estimate.
                resizeFpsDt = time.time() - resizeFps1
                resizeFps = int(1 / resizeFpsDt)
                self.windowMain.write_event_value(key='-THREAD-RESIZE-RATE-', value=resizeFps)
            else:
                self.windowMain.write_event_value(key='-THREAD-RESIZE-RATE-', value=0)

            # Sleep thread.
            time.sleep(0.03)

        print('-------------------------------------------\nThread closing down: '
              'resizeFramesThread.\n-------------------------------------------')
        self.windowMain.write_event_value(key='-THREAD-RESIZE-RATE-', value=0)

    def saveFramesThread(self):
        """
        Thread for recording frames and IMU data as a series of frames. The getFramesThread checks if recording is
        enabled, if it is then the getFramesThread sets the self.saveFrame variable to True. When the self.saveFrame
        variable is True in the saveFramesThread the frame and IMU data is recorded. The IMU data will most
        likely be out of sync with the frames, but only marginally.

        This thread will run as long as the self.frameGrabber object is connected to a signal source, but will only
        save a frame if the self.saveFrame variable is set to True in the getFramesThread. On disconnect
        of the signal source the thread will be closed. Joining the thread to the parent thread does not seem
        to be necessary.
        """
        print('Thread starting up: saveFramesThread.\n')
        while self.frameGrabber.isConnected:
            if self.saveFrame:
                self.saveFrame = False
                frameName = f'{self.frameGrabCounter}-{int(time.time() * 1000)}'
                self.record(frameName, self.frameRaw, self.acceleration, self.quaternion)
                self.frameGrabCounter += 1
                self.windowMain.write_event_value(key='-THREAD-FRAMES-SAVED-', value=self.frameGrabCounter)
            else:
                # When not recording the empty while loop causes issues for the controlling process.
                time.sleep(0.001)

        print('-------------------------------------------\nThread closing down: '
              'saveFramesThread.\n-------------------------------------------')

    def plottingThread(self):
        """
        Thread for plotting the orientation of the IMU. Moved to a thread as having it in the main run loop of the
        main window was causing major delays. This thread will be limited to a fairly low frame rate and will call
        an event in the main window when the plot is ready.

        NB: When the main menu is open the system freezes. This delays the video signal for some reason. If the
        menu is open for 5 seconds, then the video signal will be delayed for 5 seconds. Once a delay is introduced
        you need to disable plotting.
        """
        print('Thread starting up: plottingThread.\n')
        while self.imu.isConnected:
            # Only plot if plotting is enabled, the IMU is connected, and a quaternion value is available.
            if self.enablePlotting and self.imu.quaternion:
                self.fig_agg.restore_region(self.bg)
                self.ax = ut.plotOrientationOnAxis(self.ax, self.imu.quaternion, self.pointData, self.lineData)
                self.windowMain.write_event_value('-THREAD-PLOT-', None)

            time.sleep(0.1)
        print('-------------------------------------------\nThread closing down: '
              'plottingThread.\n-------------------------------------------')

    def record(self, frameName, frame, acceleration, quaternion):
        """
        Save a frame as part of a series of frames to be stitched together at a later stage. The frame is saved as a
        .png in the currentRecordingPath and the currentDataFile is updated with the relevant IMU data. The dimensions
        come from the frameGrabber signal and the depth is 150 as default.

        Args:
            frameName (str): Name of the frame, without extension. Based on time.
            frame (Image): CV2 image.
            acceleration (3D list): Acceleration returned by the imu object.
            quaternion (4D list): Quaternion returned by the imu object.
        """
        try:
            self.currentDataFile.write(f'{frameName},:'
                                       f'acc[,{acceleration[0]},{acceleration[1]},{acceleration[2]},]'
                                       f'q[,{quaternion[0]},{quaternion[1]},{quaternion[2]},{quaternion[3]},]'
                                       f'dimensions[,{self.frameGrabber.width},{self.frameGrabber.height},]'
                                       f'depth[,{c.DEFAULT_SCAN_DEPTH},]\n')
            ut.saveSingleFrame(frame, f'{self.currentRecordingPath}\\{frameName}.png')
        except Exception as e:
            print(f'Error recording a frame or recording to data.txt: {e}.')

    def toggleDisplay(self):
        """
        Toggle whether the display should be updated or not. Disabling the display can give a moderate frame rate boost,
        especially when recording frames.
        """
        self.enableDisplay = not self.enableDisplay
        self.windowMain['-BUTTON-DISPLAY-TOGGLE-'].update(
            text='Disable Display' if self.enableDisplay else 'Enable Display',
            button_color=sg.DEFAULT_BUTTON_COLOR if not self.enableDisplay else st.BUTTON_ACTIVE)

    def setSignalSourceAndConnect(self, signalSource):
        """
        Set the source of the video signal then attempt to connect to the new source.

        Args:
            signalSource (int): Location of the video signal source as an integer, representing a USB port or webcam.
        """
        # Set source.
        self.frameGrabber.signalSource = signalSource
        # Attempt to connect to source (internally disconnect if currently connected).
        self.frameGrabber.connect()
        # Start frame threads.
        self.threadExecutor.submit(self.getFramesThread)
        self.threadExecutor.submit(self.resizeFramesThread)
        self.threadExecutor.submit(self.saveFramesThread)
        # Update menus.
        self.updateMenus()
        # Set element states.
        self.windowMain['-BUTTON-SNAPSHOT-'].update(disabled=False if self.frameGrabber.isConnected else True)
        self.windowMain['-BUTTON-RECORD-TOGGLE-'].update(disabled=False if self.frameGrabber.isConnected else True)
        self.windowMain['-TEXT-SIGNAL-DIMENSIONS-'].update(
            f'Signal Dimensions: {(self.frameGrabber.width, self.frameGrabber.height)}.')

    def updateTimes(self):
        """
        Update the displayed times related to a recording that is currently taking place. The start time is initially
        set, and its GUI element updated, in the self.toggleRecording method. Only the end time and elapsed time
        are calculated and updated here. The main thread currently does not do too much so time updates will be
        left on the main thread for now.
        """
        endTime = time.time()
        elapsedTime = endTime - self.recordStartTime
        # Set element states.
        self.windowMain['-TEXT-RECORD-END-'].update(time.strftime('%H:%M:%S', time.localtime(endTime)))
        self.windowMain['-TEXT-RECORD-ELAPSED-'].update(time.strftime('%H:%M:%S', time.localtime(elapsedTime)))

    def toggleRecording(self):
        """
        Toggle whether recording is enabled or not. When in the recording state various elements are disabled.
        """
        self.enableRecording = not self.enableRecording
        print(f'Enable Recording: {self.enableRecording}')

        # Create video directory for saving frames.
        if self.enableRecording:
            self.currentRecordingPath, self.currentDataFilePath = ut.createRecordingDirectory(self.videosPath)
            self.currentDataFile = open(self.currentDataFilePath, 'w')
            self.frameGrabCounter = 1
            self.recordStartTime = time.time()
            self.windowMain['-TEXT-RECORD-START-'].update(time.strftime('%H:%M:%S'))
        else:
            print(f'Closing data file {self.currentDataFilePath}...')
            self.currentDataFile.close()

        # Set element states.
        self.windowMain['-BUTTON-RECORD-TOGGLE-'].update(
            button_color=st.BUTTON_ACTIVE if self.enableRecording else sg.DEFAULT_BUTTON_COLOR,
            text='Stop Recording' if self.enableRecording else 'Start Recording')
        self.windowMain['-BUTTON-SNAPSHOT-'].update(disabled=True if self.enableRecording else False)
        self.windowMain['-BUTTON-EDIT-TOGGLE-'].update(disabled=True if self.enableRecording else False)

    def createPlot(self, azimuth):
        """
        Instantiate the initial plotting variables: The Figure and the axis, and the 2 plot parameters that store the
        line and point data. This is also called when changing the azimuth of the plot as the entire canvas needs to
        be redrawn.

        Args:
            azimuth (int): Azimuth angle in degrees.
        """
        fig = Figure(figsize=(3.5, 3.5), dpi=100)
        self.ax = fig.add_subplot(111, projection='3d')
        fig.patch.set_facecolor(sg.DEFAULT_BACKGROUND_COLOR)
        self.ax.set_position((0, 0, 1, 1))

        self.ax = ut.initialiseAxis(self.ax, azimuth)
        self.ax.disable_mouse_rotation()

        self.fig_agg = ut.drawFigure(fig, self.windowMain['-CANVAS-PLOT-'].TKCanvas)

        self.bg = self.fig_agg.copy_from_bbox(self.ax.bbox)

        self.pointData = self.ax.plot([], [], [], color="red", linestyle="none", marker="o", animated=True)[0]
        self.lineData = self.ax.plot([], [], [], color="red", animated=True)[0]

    def setAzimuth(self, azimuth):
        """
        Set the azimuth of the plot to the slider value. This allows for aligning the plot to the user's orientation
        since the IMU orientation is based on magnetic north. The axis needs to be cleared first, then reinitialised
        to ensure a clean plot is saved for blit purposes.

        Args:
            azimuth (int): Azimuth to set the displayed plot to.
        """
        # Clear axis.
        self.ax.cla()
        # Reinitialise axis.
        self.ax = ut.initialiseAxis(self.ax, azimuth)
        # Redraw new axis.
        self.fig_agg.draw()
        # Re-save background for blit.
        self.bg = self.fig_agg.copy_from_bbox(self.ax.bbox)

    def togglePlotting(self):
        """
        Toggle whether the plot should be updated or not. Disabling plotting can give a slight frame rate boost, but
        with blit the improvement tends to be marginal.
        """
        self.enablePlotting = not self.enablePlotting
        self.windowMain['-BUTTON-PLOT-TOGGLE-'].update(
            text='Disable Plotting' if self.enablePlotting else 'Enable Plotting',
            button_color=sg.DEFAULT_BUTTON_COLOR if not self.enablePlotting else st.BUTTON_ACTIVE)

    def changeSignalDimensions(self, dimensions):
        """
        Attempt to change the signal dimensions from the menu click. After attempting to change the dimensions update
        the GUI with the actual dimensions. If the selected dimensions cannot be used, some default value will be used.

        Args:
            dimensions: Selected from the menu.
        """
        self.frameGrabber.setGrabberProperties(width=int(dimensions[0]), height=int(dimensions[1]),
                                               fps=c.DEFAULT_FRAME_RATE)
        self.windowMain['-TEXT-SIGNAL-DIMENSIONS-'].update(
            f'Signal Dimensions: {(self.frameGrabber.width, self.frameGrabber.height)}.')

    def refreshComPorts(self):
        """
        Refresh the available COM ports displayed in windowImuConnect. The variable list of available COM ports is
        updated as well as the drop-down menu/list.
        """
        self.availableComPorts = IMU.availableComPorts()
        # Set elements
        self.windowImuConnect['-COMBO-COM-PORT-'].update(values=self.availableComPorts)

    def showImuConnectWindow(self):
        """
        Show a window for the user to connect to an IMU based on COM port and baud rate selection. The user
        can refresh available COM ports, select a COM port, and select a baud rate from this window. When the CONNECT
        button is clicked an attempt is made to open the requested COM port at the specified baud rate.

        When the COM port and baud rate are changed from the combo boxes, the self.imu variable has its properties
        modified immediately (self.imu.comPort, self.imu.baudrate). If CONNECT is clicked while the COM port box is
        empty (post refresh), the currently stored self.imu.comPort will be used.

        The window will close if there is a successful connection to the COM port. There is no test to see if the
        port belongs to an IMU or not, just if the connection is made. The user will need to see if acceleration values
        are being updated in the main GUI.
        """
        self.windowImuConnect = sg.Window('Connect to IMU',
                                          self.layout.getImuWindowLayout(self.availableComPorts, self.imu.comPort,
                                                                         self.imu.baudRate),
                                          element_justification='center', modal=True)

        while True:
            event, values = self.windowImuConnect.read()

            if event in [sg.WIN_CLOSED, 'None']:
                # On window close.
                break
            elif event == '-BUTTON-COM-REFRESH-':
                # On refresh available COM ports clicked.
                self.refreshComPorts()
            elif event == '-COMBO-COM-PORT-':
                # On COM port changed.
                self.imu.comPort = values['-COMBO-COM-PORT-']
            elif event == '-COMBO-BAUD-RATE-':
                # On baud rate changed.
                self.imu.baudRate = int(values['-COMBO-BAUD-RATE-'])
            elif event == '-BUTTON-IMU-CONNECT-':
                # On connect button clicked.
                self.imu.connect()
                if self.imu.isConnected:
                    self.threadExecutor.submit(self.plottingThread)
                    break

        self.updateMenus()
        self.windowImuConnect.close()

    def updateMenus(self):
        """
        Helper function that updates the main window's menu based on the current states of the self.frameGrabber and
        self.imu objects.
        """
        # Set elements.
        self.windowMain['-MENU-'].update(
            menu_definition=self.menu.getMenu(self.frameGrabber.isConnected, self.imu.isConnected, self.enableEditing))

    def close(self):
        """
        Delete references to IMU object for garbage collection. This ensures the resources are freed
        up for future use. Only called as the program is shutting down. The FrameGrabber object is disconnected, the
        release takes place in the FrameGrabber __del__ method.
        """
        if self.imu.isConnected:
            self.imu.disconnect()
            del self.imu

        if self.frameGrabber.isConnected:
            self.frameGrabber.disconnect()

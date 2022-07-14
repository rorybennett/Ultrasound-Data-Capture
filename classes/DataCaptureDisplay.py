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
from classes import Recording

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
        self.pointPlot = None
        self.linePlot = None
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
        self.recording = None
        # Do Graph clicks add data points?
        self.enableDataPoints = False
        # Should a Graph click change the offset?
        self.enableOffsetChangeTop = False
        self.enableOffsetChangeBottom = False
        self.enableOffsetChangeLeft = False
        self.enableOffsetChangeRight = False

        # IMU connect window
        self.windowImuConnect = None

        self.windowMain = sg.Window('Ultrasound Data Capture', self.layout.getInitialLayout(), finalize=True)

        # Create the initial plot.
        self.createPlot()

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
                self.windowMain['-TXT-ACCELERATION-X-'].update(f'{self.imu.acceleration[0]:.4f}')
                self.windowMain['-TXT-ACCELERATION-Y-'].update(f'{self.imu.acceleration[1]:.4f}')
                self.windowMain['-TXT-ACCELERATION-Z-'].update(f'{self.imu.acceleration[2]:.4f}')

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
                self.windowMain['-TXT-ANGLES-'].update(
                    f'Yaw: {self.recording.getFrameAngles()[0]}\tPitch: {self.recording.getFrameAngles()[1]} \tRoll:'
                    f' {self.recording.getFrameAngles()[2]}')
                self.windowMain['-GRAPH-FRAME-'].draw_image(data=values[event], location=(0, c.DISPLAY_DIMENSIONS[1]))

            # Menu events.
            if event.endswith('::-MENU-SIGNAL-CONNECT-'):
                self.setSignalSourceAndConnect(int(event.split('::')[0]))
            elif event.endswith('::-MENU-SIGNAL-DISCONNECT-'):
                self.frameGrabber.disconnect()
                self.updateMenus()
            elif event.endswith('::-MENU-SIGNAL-DIMENSIONS-'):
                self.changeSignalDimensions(event.split('::')[0].split('x'))
            elif event.endswith('::-MENU-IMU-CONNECT-'):
                self.showImuConnectWindow()
            elif event.endswith('::-MENU-IMU-DISCONNECT-'):
                self.imu.disconnect()
                self.updateMenus()
            elif event.endswith('::-MENU-IMU-RATE-'):
                self.imu.setReturnRate(float(event.split('Hz')[0]))
            elif event.endswith('::-MENU-IMU-CALIBRATE-'):
                self.imu.calibrateAcceleration()
            elif event.endswith('::-MENU-EDIT-TOGGLE-'):
                self.toggleEditing()

            # Signal Display Events.
            if event == '-BTN-DISPLAY-TOGGLE-':
                self.toggleDisplay()
            elif event == '-BTN-SNAPSHOT-':
                ut.saveSingleFrame(self.frameRaw, f'{self.singleFramesPath}\\{int(time.time() * 1000)}.png')
            elif event == '-BTN-RECORD-TOGGLE-':
                self.toggleRecording()

            # IMU Display Events.
            if event == '-SLIDER-AZIMUTH-':
                self.setAzimuth(int(values['-SLIDER-AZIMUTH-']))
            elif event == '-BTN-PLOT-TOGGLE-':
                self.togglePlotting()

            # Thread events.
            if event == '-THREAD-SIGNAL-RATE-':
                self.windowMain['-TXT-SIGNAL-RATE-'].update(f'{values[event]}')
            elif event == '-THREAD-RESIZE-RATE-':
                self.windowMain['-TXT-RESIZE-RATE-'].update(f'{values[event]}')
            elif event == '-THREAD-FRAMES-SAVED-':
                self.windowMain['-TXT-FRAMES-SAVED-'].update(f'{values[event]}')
            elif event == '-THREAD-PLOT-':
                self.fig_agg.blit(self.ax.bbox)
            self.fig_agg.flush_events()

            # Editing events.
            if event == '-COMBO-RECORDINGS-':
                self.selectRecordingForEdit(values[event])
            elif event == '-TXT-DETAILS-PATH-' and self.recording:
                ut.openWindowsExplorer(self.recording.path)
            elif event in Layout.NAV_KEYS:
                self.navigateFrames(event.split('-')[-2])
            elif event == '-INPUT-NAV-GOTO-' + '_Enter':
                self.navigateFrames(values['-INPUT-NAV-GOTO-'])
            elif event == '-BTN-OFFSET-TOP-':
                self.toggleChangingOffsetTop()
            elif event == '-BTN-OFFSET-BOTTOM-':
                self.toggleChangingOffsetBottom()
            elif event == '-BTN-OFFSET-LEFT-':
                self.toggleChangingOffsetLeft()
            elif event == '-BTN-OFFSET-RIGHT-':
                self.toggleChangingOffsetRight()
            elif event == '-INPUT-EDIT-DEPTH-' + '_Enter':
                self.recording.changeScanDepth(values['-INPUT-EDIT-DEPTH-'])
            elif event == '-INPUT-EDIT-DEPTHS-' + '_Enter':
                self.changeAllScanDepths(values['-INPUT-EDIT-DEPTHS-'])
            elif event == '-INPUT-IMU-OFFSET-' + '_Enter':
                self.changeImuOffset(values['-INPUT-IMU-OFFSET-'])
            elif event == '-BTN-POINTS-':
                self.toggleAddingDataPoints()
            elif event == '-BTN-CLEAR-FRAME-':
                self.clearFramePoints(Recording.CLEAR_FRAME)
            elif event == '-BTN-CLEAR-ALL-':
                self.clearFramePoints(Recording.CLEAR_ALL)
            elif event == '-GRAPH-FRAME-':
                self.onGraphFrameClicked(values[event])

            # GUI frame rate estimate.
            guiDt = time.time() - guiFps1
            guiFps = int(1 / guiDt) if guiDt > 0.00999 else '100+'

            self.windowMain['-TXT-GUI-RATE-'].update(f'{guiFps}' if not self.enableEditing else '0')

    def changeImuOffset(self, newImuOffset):
        """
        Change IMU offset value.
        """
        self.recording.changeImuOffset(newImuOffset)

        self.fig_agg.restore_region(self.bg)
        self.ax = self.recording.plotDataPointsOnAxis(self.ax, self.pointPlot)
        self.windowMain.write_event_value('-THREAD-PLOT-', None)

    def clearFramePoints(self, clearType):
        """
        Clear points from current frame or all frames.
        """
        if clearType == Recording.CLEAR_FRAME:
            self.recording.clearFramePoints()
        elif clearType == Recording.CLEAR_ALL:
            self.recording.clearAllPoints()

        self.windowMain.write_event_value('-UPDATE-GRAPH-FRAME-', self.recording.getCurrentFrameAsBytes())
        self.fig_agg.restore_region(self.bg)
        self.ax = self.recording.plotDataPointsOnAxis(self.ax, self.pointPlot)
        self.windowMain.write_event_value('-THREAD-PLOT-', None)
        self.windowMain['-TXT-TOTAL-POINTS-'].update(f'Total Points: {len(self.recording.pointData)}')

    def recreateEditingAxis(self):
        """
        Recreate the axis for editing purposes.
        """
        # Clear axis.
        self.ax.cla()
        # Reinitialise axis.
        self.ax = ut.initialiseEditingAxis(self.ax, c.AZIMUTH,
                                           self.recording.depths[self.recording.currentFrame])
        # Redraw new axis.
        self.fig_agg.draw()
        # Re-save background for blit.
        self.bg = self.fig_agg.copy_from_bbox(self.ax.bbox)
        if self.recording:
            self.ax = self.recording.plotDataPointsOnAxis(self.ax, self.pointPlot)
        self.windowMain.write_event_value('-THREAD-PLOT-', None)

    def changeAllScanDepths(self, newScanDepth: str):
        """
        Call the changeAllScanDepths of the RecordingDetails object.
        """
        self.recording.changeAllScanDepths(newScanDepth)

        self.recreateEditingAxis()

        # Set element states.
        self.windowMain['-INPUT-EDIT-DEPTH-'].update(
            f'{self.recording.depths[self.recording.currentFrame]}')
        self.windowMain['-INPUT-EDIT-DEPTHS-'].update()

    def onGraphFrameClicked(self, point):
        """
        Click handler function for when the Graph frame element is clicked. If:
            1. enableDataPoints         -   A new data point is added or removed (if within proximity of existing point)
                                            to the frame.
            2. enableOffsetChangeTop    -   The vertical portion of the point is used as the new top offset value.
            3. enableOffsetChangeBottom -   The vertical portion of the point is used as the new bottom offset value.
            4. enableOffsetChangeLeft   -   The horizontal portion of the point is used as the new left offset value.
            5. enableOffsetChangeRight  -   The horizontal portion of the point is used as the new right offset value.

        Args:
            point: Coordinates of where the Graph element was clicked.
        """

        if self.enableDataPoints:
            self.recording.addRemovePointData(point)
            self.windowMain.write_event_value('-UPDATE-GRAPH-FRAME-',
                                              self.recording.getCurrentFrameAsBytes())
            self.fig_agg.restore_region(self.bg)
            self.ax = self.recording.plotDataPointsOnAxis(self.ax, self.pointPlot)
            self.windowMain.write_event_value('-THREAD-PLOT-', None)
            self.windowMain['-TXT-TOTAL-POINTS-'].update(f'Total Points: {len(self.recording.pointData)}')
        elif self.enableOffsetChangeTop:
            self.recording.changeOffsetTop((c.DISPLAY_DIMENSIONS[1] - point[1]) / c.DISPLAY_DIMENSIONS[1])
            self.windowMain.write_event_value('-UPDATE-GRAPH-FRAME-',
                                              value=self.recording.getCurrentFrameAsBytes())
        elif self.enableOffsetChangeBottom:
            self.recording.changeOffsetBottom((c.DISPLAY_DIMENSIONS[1] - point[1]) / c.DISPLAY_DIMENSIONS[1])
            self.windowMain.write_event_value('-UPDATE-GRAPH-FRAME-',
                                              value=self.recording.getCurrentFrameAsBytes())
        elif self.enableOffsetChangeLeft:
            self.recording.changeOffsetLeft(point[0] / c.DISPLAY_DIMENSIONS[0])
            self.windowMain.write_event_value('-UPDATE-GRAPH-FRAME-',
                                              value=self.recording.getCurrentFrameAsBytes())
        elif self.enableOffsetChangeRight:
            self.recording.changeOffsetRight(point[0] / c.DISPLAY_DIMENSIONS[0])
            self.windowMain.write_event_value('-UPDATE-GRAPH-FRAME-',
                                              value=self.recording.getCurrentFrameAsBytes())

    def navigateFrames(self, navCommand):
        """
        Call the navigateFrames function of the RecordingDetails object.
        """
        self.recording.navigateFrames(navCommand)

        # Set element states.
        self.windowMain['-TXT-NAV-CURRENT-'].update(
            f'{self.recording.currentFrame}/{self.recording.frameCount}')
        self.windowMain['-INPUT-EDIT-DEPTH-'].update(
            f'{self.recording.depths[self.recording.currentFrame - 1]}')

        self.windowMain.write_event_value('-UPDATE-GRAPH-FRAME-', value=self.recording.getCurrentFrameAsBytes())

    def selectRecordingForEdit(self, videoDirectory: str):
        """
        Update main window to allow editing of the selected recording. This creates the recordingDetails object and
        sets the elements to the correct states. The first frame from the recording is shown in the display and
        the details of the recording are displayed.

        Args:
            videoDirectory (str): Directory name where the recording is stored.
        """
        print(f'Create editing data for: {videoDirectory}')
        self.recording = Recording.Recording(self.videosPath, videoDirectory)
        self.enableOffsetChangeTop, self.enableOffsetChangeBottom = False, False
        self.enableOffsetChangeLeft, self.enableOffsetChangeRight = False, False
        self.enableDataPoints = False

        self.recreateEditingAxis()

        # Set element states
        self.windowMain['-TXT-DETAILS-DATE-'].update(self.recording.date)
        self.windowMain['-TXT-DETAILS-PATH-'].update(self.recording.path)
        self.windowMain['-TXT-DETAILS-DURATION-'].update(
            time.strftime('%H:%M:%S', time.localtime(self.recording.duration / 1000)))
        self.windowMain['-TXT-DETAILS-FRAMES-'].update(self.recording.frameCount)
        self.windowMain['-TXT-DETAILS-POINTS-'].update(self.recording.imuCount)
        self.windowMain['-TXT-DETAILS-FPS-'].update(self.recording.fps)

        [self.windowMain[i].update(disabled=False) for i in Layout.NAV_KEYS]
        self.windowMain['-INPUT-NAV-GOTO-'].update(disabled=False)
        self.windowMain['-TXT-NAV-CURRENT-'].update(
            f'{self.recording.currentFrame}/{self.recording.frameCount}')

        self.windowMain['-BTN-OFFSET-TOP-'].update(disabled=False, button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BTN-OFFSET-BOTTOM-'].update(disabled=False, button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BTN-OFFSET-LEFT-'].update(disabled=False, button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BTN-OFFSET-RIGHT-'].update(disabled=False, button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-INPUT-EDIT-DEPTH-'].update(
            f'{self.recording.depths[self.recording.currentFrame - 1]}', disabled=False)
        self.windowMain['-INPUT-EDIT-DEPTHS-'].update('', disabled=False)
        self.windowMain['-INPUT-IMU-OFFSET-'].update(self.recording.imuOffset, disabled=False)

        self.windowMain['-BTN-POINTS-'].update(disabled=False, button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BTN-CLEAR-FRAME-'].update(disabled=False, button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BTN-CLEAR-ALL-'].update(disabled=False, button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-TXT-TOTAL-POINTS-'].update(f'Total Points: {len(self.recording.pointData)}')

        self.windowMain.write_event_value('-UPDATE-GRAPH-FRAME-', value=self.recording.getCurrentFrameAsBytes())

    def toggleAddingDataPoints(self):
        """
        Toggle the state of self.enableDataPoints to enable or disable adding data points to a frame.
        """
        self.enableDataPoints = not self.enableDataPoints
        self.enableOffsetChangeTop = False
        self.enableOffsetChangeBottom = False
        self.enableOffsetChangeLeft = False
        self.enableOffsetChangeRight = False
        # Set element states.
        self.windowMain['-BTN-POINTS-'].update(
            button_color=st.COLOUR_BTN_ACTIVE if self.enableDataPoints else sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BTN-OFFSET-TOP-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BTN-OFFSET-BOTTOM-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BTN-OFFSET-LEFT-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BTN-OFFSET-RIGHT-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)

    def toggleEditing(self):
        """
        Toggle the state of self.enableEditing. When in editing state (True), the Signal Source and IMU menu items
        are disabled. The FrameGrabber object and IMU are disconnected and the plot is cleared. Some buttons are
        disabled and some are reset to default values. The display and plot are enabled for consistency.
        """
        self.enableEditing = not self.enableEditing
        self.windowMain.close()
        self.windowMain = sg.Window('Ultrasound Data Capture',
                                    self.layout.getEditingLayout() if self.enableEditing else
                                    self.layout.getInitialLayout(),
                                    finalize=True)

        # Enable/Disable plotting for consistency, clear plot.
        self.enablePlotting = False if self.enableEditing else True
        self.createPlot(limits=(0, 150) if self.enableEditing else (-5, 5),
                        size=(6, 6) if self.enableEditing else (3.5, 3.5))

        # Enable the frame display for consistency.
        self.enableDisplay = True
        self.recording = None
        print(f'Entering editing mode: {self.enableEditing}')
        # Editing has been enabled.
        if self.enableEditing:
            if self.frameGrabber.isConnected:
                self.frameGrabber.disconnect()
            if self.imu.isConnected:
                self.imu.disconnect()

            self.windowMain['-COMBO-RECORDINGS-'].update(
                values=ut.getRecordingDirectories(self.videosPath))
            # Enter key bindings for input elements.
            self.windowMain['-INPUT-NAV-GOTO-'].bind('<Return>', '_Enter')
            self.windowMain['-INPUT-EDIT-DEPTH-'].bind('<Return>', '_Enter')
            self.windowMain['-INPUT-EDIT-DEPTHS-'].bind('<Return>', '_Enter')
            self.windowMain['-INPUT-IMU-OFFSET-'].bind('<Return>', '_Enter')
            time.sleep(0.5)

        # Set element states.
        self.updateMenus()

    def getFramesThread(self):
        """
        Thread for acquiring frames from FrameGrabber object. As soon as a frame is acquired from the FrameGrabber
        object the currently stored IMU values are copied to local variables. This may result in a slight time delay
        between the frame and its associated IMU values.

        if self.enableRecording is True, the current frame will be saved with the IMU data available.

        If self.enableDisplay is True, the new frame will be resized and displayed in the main GUI.
        """
        print('Thread starting up: getFramesThread.')
        while self.frameGrabber.isConnected:
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
        """
        print('Thread starting up: resizeFramesThread.')
        while self.frameGrabber.isConnected:
            if self.resizeFrame:
                self.resizeFrame = False
                resizeFps1 = time.time()
                resizedFrame = ut.resizeFrame(self.frameRaw, c.DISPLAY_DIMENSIONS, ut.INTERPOLATION_NEAREST)
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
        Thread for plotting the orientation of the IMU. This thread will be limited to a fairly low frame rate and
        will call an event in the main window when the plot is ready.

        NB: When the main menu is open the system freezes. This delays the video signal for some reason. If the
        menu is open for 5 seconds, then the video signal will be delayed for 5 seconds. Once a delay is introduced
        you need to disable plotting.
        """
        print('Thread starting up: plottingThread.\n')
        while self.imu.isConnected:
            # Only plot if plotting is enabled, the IMU is connected, and a quaternion value is available.
            if self.enablePlotting and self.imu.quaternion:
                self.fig_agg.restore_region(self.bg)
                self.ax = ut.plotOrientationOnAxis(self.ax, self.imu.quaternion, self.pointPlot, self.linePlot)
                self.windowMain.write_event_value('-THREAD-PLOT-', None)

            time.sleep(0.1)
        print('-------------------------------------------\nThread closing down: '
              'plottingThread.\n-------------------------------------------')

    def toggleChangingOffsetTop(self):
        """
        Toggle the state of self.enableOffsetChangeTop to enable or disable changing of the top frame offset value.
        """
        self.enableOffsetChangeTop = not self.enableOffsetChangeTop
        self.enableDataPoints, self.enableOffsetChangeBottom = False, False
        self.enableOffsetChangeLeft, self.enableOffsetChangeRight = False, False
        # Set element states.
        self.windowMain['-BTN-OFFSET-TOP-'].update(
            button_color=st.COLOUR_BTN_ACTIVE if self.enableOffsetChangeTop else sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BTN-OFFSET-BOTTOM-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BTN-OFFSET-LEFT-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BTN-OFFSET-RIGHT-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BTN-POINTS-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)

    def toggleChangingOffsetBottom(self):
        """
        Toggle the state of self.enableOffsetChangeBottom to enable or disable changing of the bottom frame offset value.
        """
        self.enableOffsetChangeBottom = not self.enableOffsetChangeBottom
        self.enableOffsetChangeTop, self.enableDataPoints = False, False
        self.enableOffsetChangeLeft, self.enableOffsetChangeRight = False, False
        # Set element states.
        self.windowMain['-BTN-OFFSET-BOTTOM-'].update(
            button_color=st.COLOUR_BTN_ACTIVE if self.enableOffsetChangeBottom else sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BTN-OFFSET-TOP-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BTN-OFFSET-LEFT-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BTN-OFFSET-RIGHT-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BTN-POINTS-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)

    def toggleChangingOffsetLeft(self):
        """
        Toggle the state of self.enableOffsetChangeLeft to enable or disable changing of the left frame offset value.
        """
        self.enableOffsetChangeLeft = not self.enableOffsetChangeLeft
        self.enableOffsetChangeTop, self.enableOffsetChangeBottom = False, False
        self.enableDataPoints, self.enableOffsetChangeRight = False, False
        # Set element states.
        self.windowMain['-BTN-OFFSET-LEFT-'].update(
            button_color=st.COLOUR_BTN_ACTIVE if self.enableOffsetChangeLeft else sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BTN-OFFSET-TOP-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BTN-OFFSET-BOTTOM-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BTN-OFFSET-RIGHT-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BTN-POINTS-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)

    def toggleChangingOffsetRight(self):
        """
        Toggle the state of self.enableOffsetChangeRight to enable or disable changing of the right frame offset value.
        """
        self.enableOffsetChangeRight = not self.enableOffsetChangeRight
        self.enableOffsetChangeTop, self.enableOffsetChangeBottom = False, False
        self.enableOffsetChangeLeft, self.enableDataPoints = False, False
        # Set element states.
        self.windowMain['-BTN-OFFSET-RIGHT-'].update(
            button_color=st.COLOUR_BTN_ACTIVE if self.enableOffsetChangeRight else sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BTN-OFFSET-TOP-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BTN-OFFSET-BOTTOM-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BTN-OFFSET-LEFT-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)
        self.windowMain['-BTN-POINTS-'].update(button_color=sg.DEFAULT_BUTTON_COLOR)

    def record(self, frameName, frame, acceleration, quaternion):
        """
        Save a frame as part of a series of frames to be stitched together at a later stage. The frame is saved as a
        .png in the currentRecordingPath and the currentDataFile is updated with the relevant IMU data. The dimensions
        come from the frameGrabber signal and the depth is 150 as default.

        Args:
            frameName (str): Name of the frame, without extension. Based on time.
            frame (Image): CV2 image.
            acceleration (list): Acceleration returned by the imu object.
            quaternion (list): Quaternion returned by the imu object.
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
        Toggle self.enableDisplay. Disabling the display can give a moderate frame rate boost, especially when
        recording frames.
        """
        self.enableDisplay = not self.enableDisplay
        self.windowMain['-BTN-DISPLAY-TOGGLE-'].update(
            text='Disable Display' if self.enableDisplay else 'Enable Display',
            button_color=sg.DEFAULT_BUTTON_COLOR if not self.enableDisplay else st.COLOUR_BTN_ACTIVE)

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
        self.windowMain['-BTN-SNAPSHOT-'].update(disabled=False if self.frameGrabber.isConnected else True)
        self.windowMain['-BTN-RECORD-TOGGLE-'].update(disabled=False if self.frameGrabber.isConnected else True)
        self.windowMain['-TXT-SIGNAL-DIMENSIONS-'].update(
            f'Signal Dimensions: {(self.frameGrabber.width, self.frameGrabber.height)}.')

    def updateTimes(self):
        """
        Update the displayed times related to a recording that is currently taking place.
        """
        endTime = time.time()
        elapsedTime = endTime - self.recordStartTime
        # Set element states.
        self.windowMain['-TXT-RECORD-END-'].update(time.strftime('%H:%M:%S', time.localtime(endTime)))
        self.windowMain['-TXT-RECORD-ELAPSED-'].update(time.strftime('%H:%M:%S', time.localtime(elapsedTime)))

    def toggleRecording(self):
        """
        Toggle self.enableRecording. When in the recording state various elements are disabled.
        """
        self.enableRecording = not self.enableRecording
        print(f'Enable Recording: {self.enableRecording}')

        # Create video directory for saving frames.
        if self.enableRecording:
            self.currentRecordingPath, self.currentDataFilePath = ut.createRecordingDirectory(self.videosPath)
            self.currentDataFile = open(self.currentDataFilePath, 'w')
            self.frameGrabCounter = 1
            self.recordStartTime = time.time()
            self.windowMain['-TXT-RECORD-START-'].update(time.strftime('%H:%M:%S'))
        else:
            print(f'Closing data file {self.currentDataFilePath}...')
            self.currentDataFile.close()

        # Set element states.
        self.windowMain['-BTN-RECORD-TOGGLE-'].update(
            button_color=st.COLOUR_BTN_ACTIVE if self.enableRecording else sg.DEFAULT_BUTTON_COLOR,
            text='Stop Recording' if self.enableRecording else 'Start Recording')
        self.windowMain['-BTN-SNAPSHOT-'].update(disabled=True if self.enableRecording else False)

    def createPlot(self, limits=(-5, 5), size=(3.5, 3.5)):
        """
        Instantiate the initial plotting variables: The Figure and the axis, and the 2 plot parameters that store the
        line and point data.

        Args:
            limits (tuple): Lower and upper limits applied to all axes.
            size (tuple): Width and height of figure.

        """
        fig = Figure(figsize=size, dpi=100)
        self.ax = fig.add_subplot(111, projection='3d')
        fig.patch.set_facecolor(sg.DEFAULT_BACKGROUND_COLOR)
        self.ax.set_position((0, 0, 1, 1))

        self.ax = ut.initialiseAxis(self.ax, c.AZIMUTH, limits)
        self.ax.disable_mouse_rotation()

        self.fig_agg = ut.drawFigure(fig, self.windowMain['-CANVAS-PLOT-'].TKCanvas)

        self.bg = self.fig_agg.copy_from_bbox(self.ax.bbox)

        self.pointPlot = self.ax.plot([], [], [], color="red", linestyle="none", marker="o", animated=True)[0]
        self.linePlot = self.ax.plot([], [], [], color="red", animated=True)[0]

    def setAzimuth(self, azimuth):
        """
        Set the azimuth of the plot to the slider value.

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
        Toggle self.enablePlotting. Disabling plotting can give a slight frame rate boost.
        """
        self.enablePlotting = not self.enablePlotting
        self.windowMain['-BTN-PLOT-TOGGLE-'].update(
            text='Disable Plotting' if self.enablePlotting else 'Enable Plotting',
            button_color=sg.DEFAULT_BUTTON_COLOR if not self.enablePlotting else st.COLOUR_BTN_ACTIVE)

    def changeSignalDimensions(self, dimensions):
        """
        Attempt to change the signal dimensions from the menu click. After attempting to change the dimensions update
        the GUI with the actual dimensions. If the selected dimensions cannot be used, some default value will be used.

        Args:
            dimensions: Selected from the menu.
        """
        self.frameGrabber.setGrabberProperties(width=int(dimensions[0]), height=int(dimensions[1]),
                                               fps=c.DEFAULT_FRAME_RATE)
        self.windowMain['-TXT-SIGNAL-DIMENSIONS-'].update(
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
            elif event == '-BTN-COM-REFRESH-':
                # On refresh available COM ports clicked.
                self.refreshComPorts()
            elif event == '-COMBO-COM-PORT-':
                # On COM port changed.
                self.imu.comPort = values['-COMBO-COM-PORT-']
            elif event == '-COMBO-BAUD-RATE-':
                # On baud rate changed.
                self.imu.baudRate = int(values['-COMBO-BAUD-RATE-'])
            elif event == '-BTN-IMU-CONNECT-':
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

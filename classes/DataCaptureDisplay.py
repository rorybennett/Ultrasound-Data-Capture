"""
Main class for capturing frames from the output of an ultrasound scanner and adding IMU orientation data to the frames.

"""
import styling as st
import utils as ut
from classes import IMU
from classes import FrameGrabber
import constants as c
from classes import Menu
from classes import Layout

import PySimpleGUI as sg
import time
from classes import PlottingProcess
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
        self.enablePlotting = False
        # FrameGrabber object instantiated with default values.
        self.frameGrabber = FrameGrabber.FrameGrabber()
        # Initial search for system COM ports.
        self.availableComPorts = IMU.availableComPorts()
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

        # IMU connect window
        self.windowImuConnect = None

        self.windowMain = sg.Window('Ultrasound Data Capture', self.layout.getInitialLayout(),
                                    return_keyboard_events=True, finalize=True, use_default_focus=False,
                                    location=(20, 50))

        # Plotting process
        self.plottingProcess = PlottingProcess.PlottingProcess(self.windowMain)

        self.run()

    def run(self):
        """
        Main loop/thread for displaying the GUI and reacting to events, in standard PySimpleGUI fashion.
        """
        while True:
            guiFps1 = time.time()
            # Update recording times.
            if self.enableRecording:
                self.updateDisplayedTimes()
            # Update IMU values if present.
            if self.imu.isConnected and self.imu.acceleration:
                self.updateAccelerations()
            # Send orientation to plotting process.
            if self.enablePlotting and self.imu.quaternion:
                self.plottingProcess.plotOrientation(self.imu.quaternion)

            event, values = self.windowMain.read(timeout=0)

            if event in [sg.WIN_CLOSED, 'None']:
                # On window close clicked.
                self.close()
                break

            # Event for updating Image frame (recording).
            if event == '-UPDT-IMAGE-FRAME-':
                self.windowMain['-IMAGE-FRAME-'].update(data=values[event])

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
            elif event.endswith('::-MENU-IMU-BANDWIDTH-'):
                self.imu.setBandwidth(int(event.split('Hz')[0]))
            elif event.endswith('::-MENU-IMU-ALGORITHM-'):
                self.imu.setAlgorithm(int(event.split('-')[0]))
            elif event.endswith('::-MENU-IMU-CALIBRATE-'):
                self.imu.calibrateAcceleration()

            # Signal Display Events.
            if event == '-BTN-DISPLAY-TOGGLE-':
                self.toggleDisplay()
            elif event == '-BTN-SNAPSHOT-':
                ut.saveSingleFrame(self.frameRaw, f'{self.singleFramesPath}\\{int(time.time() * 1000)}.png')
            elif event == '-BTN-RECORD-TOGGLE-':
                self.toggleRecording()
            elif (len(event) == 1 and ord(event) == 32) and self.frameGrabber.isConnected:
                self.toggleRecording()

            # IMU Display Events.
            if event == '-BTN-PLOT-TOGGLE-':
                self.togglePlotting()

            # Thread events.
            if event == '-THD-SIGNAL-RATE-':
                self.windowMain['-TXT-SIGNAL-RATE-'].update(f'{values[event]}')
            elif event == '-THD-RESIZE-RATE-':
                self.windowMain['-TXT-RESIZE-RATE-'].update(f'{values[event]}')
            elif event == '-THD-FRAMES-SAVED-':
                self.windowMain['-TXT-FRAMES-SAVED-'].update(f'{values[event]}')

            # GUI frame rate estimate.
            guiDt = time.time() - guiFps1
            guiFps = int(1 / guiDt) if guiDt > 0.00999 else '100+'

            self.windowMain['-TXT-GUI-RATE-'].update(f'{guiFps}')

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
                self.windowMain.write_event_value(key='-THD-SIGNAL-RATE-', value=signalFps)
                # Record frames?
                if self.enableRecording:
                    self.saveFrame = True

                # Display enabled?
                if self.enableDisplay:
                    self.resizeFrame = True

        print('-------------------------------------------\nThread closing down: '
              'getFramesThread.\n-------------------------------------------')
        self.windowMain.write_event_value(key='-THD-SIGNAL-RATE-', value=0)

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
                self.windowMain.write_event_value(key='-UPDT-IMAGE-FRAME-', value=frameBytes)
                # Resize frame rate estimate.
                resizeFpsDt = time.time() - resizeFps1
                resizeFps = int(1 / resizeFpsDt)
                self.windowMain.write_event_value(key='-THD-RESIZE-RATE-', value=resizeFps)
            else:
                self.windowMain.write_event_value(key='-THD-RESIZE-RATE-', value=0)

            # Sleep thread.
            time.sleep(0.03)

        print('-------------------------------------------\nThread closing down: '
              'resizeFramesThread.\n-------------------------------------------')
        self.windowMain.write_event_value(key='-THD-RESIZE-RATE-', value=0)

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
                self.recordFrame(frameName, self.frameRaw, self.acceleration, self.quaternion)
                self.frameGrabCounter += 1
                self.windowMain.write_event_value(key='-THD-FRAMES-SAVED-', value=self.frameGrabCounter)
            else:
                # When not recording the empty while loop causes issues for the controlling process.
                time.sleep(0.001)

        print('-------------------------------------------\nThread closing down: '
              'saveFramesThread.\n-------------------------------------------')

    def recordFrame(self, frameName, frame, acceleration, quaternion):
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
            button_color=sg.DEFAULT_BUTTON_COLOR if not self.enableDisplay else st.COL_BTN_ACTIVE)

    def setSignalSourceAndConnect(self, signalSource):
        """
        Set the source of the video signal then attempt to connect to the new source.
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

    def updateDisplayedTimes(self):
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
            print(f'Closing data file {self.currentDataFilePath}...\n')
            self.currentDataFile.close()

        # Set element states.
        self.windowMain['-BTN-RECORD-TOGGLE-'].update(
            button_color=st.COL_BTN_ACTIVE if self.enableRecording else sg.DEFAULT_BUTTON_COLOR,
            text='Stop Recording' if self.enableRecording else 'Start Recording')
        self.windowMain['-BTN-SNAPSHOT-'].update(disabled=True if self.enableRecording else False)

    def updateAccelerations(self):
        """
        update displayed acceleration values.
        """
        self.windowMain['-TXT-IMU-ACC-'].update(
            f'Ax: {self.imu.acceleration[0]:.2f}\t'
            f'Ay: {self.imu.acceleration[1]:.2f}\t'
            f'Az: {self.imu.acceleration[2]:.2f}')

    def togglePlotting(self):
        """
        Toggle self.enablePlotting.
        """
        self.enablePlotting = not self.enablePlotting

        if self.enablePlotting:
            self.plottingProcess.startPlotting()
        else:
            self.plottingProcess.endPlotting()

        self.windowMain['-BTN-PLOT-TOGGLE-'].update(
            text='Disable Plotting' if self.enablePlotting else 'Enable Plotting',
            button_color=st.COL_BTN_ACTIVE if self.enablePlotting else sg.DEFAULT_BUTTON_COLOR)

    def changeSignalDimensions(self, dimensions):
        """
        Attempt to change the signal dimensions from the menu click. After attempting to change the dimensions update
        the GUI with the actual dimensions. If the selected dimensions cannot be used, some default value will be used.
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
            menu_definition=self.menu.getMenu(self.frameGrabber.isConnected, self.imu.isConnected))

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

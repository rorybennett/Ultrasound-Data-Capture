import utils as ut
from classes import IMU
from classes import FrameGrabber
import styling as st
import constants as c

import PySimpleGUI as sg
from datetime import datetime as dt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, FigureCanvasAgg


class DataCaptureDisplay():
    def __init__(self):
        # Create initial directories for storing data.
        self.singleFramesPath, self.videosPath = ut.createInitialDirectories()
        # Record state of the program.
        self.enableRecording = False
        # Counter for labelling frame number in a recording.
        self.frameGrabCounter = 0
        # Time variables used to estimate frame rate of program.
        self.fpsCalc1 = dt.now().timestamp()
        self.fpsCalc2 = dt.now().timestamp()
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

        self.layout = self.createLayout()

        self.window = sg.Window('Ultrasound Data Capture', self.layout, finalize=True)

        self.createPlot()

        self.run()


    def createLayout(self):
        imuColumnLayout = [
            [sg.Text('IMU Orientation Plot', size=(40, 1), justification='center', font=st.HEADING_FONT)],
            [sg.Canvas(key='-CANVAS-PLOT-', size=(500, 500))],
            [sg.Text('Select Azimuth')],
            [sg.Slider(key='-SLIDER-AZIMUTH-', range=(0, 360), default_value=30, size=(40, 10), orientation='h',
                       enable_events=True)],
            [sg.Text('IMU Controls', size=(40, 1), justification='center', font=st.HEADING_FONT,
                     pad=((0, 0), (20, 5)))],
            [sg.Button(key='-BUTTON-COM-REFRESH-', button_text='', image_source='icons/refresh_icon.png',
                       image_subsample=4, border_width=3),
             sg.Combo(key='-COMBO-COM-PORT-', values=self.availableComPorts, size=7, font=st.COMBO_FONT,
                      enable_events=True, readonly=True),
             sg.Text('Baud Rate:', justification='right', font=st.DESC_FONT, pad=((20, 0), (0, 0))),
             sg.Combo(key='-COMBO-BAUD-RATE-', values=c.COMMON_BAUD_RATES, size=7, font=st.COMBO_FONT,
                      enable_events=True, readonly=True),
             sg.Button(key='-BUTTON-IMU-CONNECT-', button_text='Connect IMU', size=(15, 1), font=st.BUTTON_FONT,
                       border_width=3, pad=((40, 0), (0, 0)))],

        ]

        layout = [[sg.Column(imuColumnLayout, element_justification='center')]]

        return layout

    def run(self):
        """
        Main loop for displaying the GUI and reacting to events, in standard PySimpleGUI fashion.
        """
        while True:
            # Update the plot
            self.updatePlot()

            event, values = self.window.read(timeout=0)

            if event == sg.WIN_CLOSED:
                self.close()
                break

            if event == '-SLIDER-AZIMUTH-':
                self.setAzimuth(values['-SLIDER-AZIMUTH-'])

            if event == '-BUTTON-COM-REFRESH-':
                self.refreshComPorts()

            if event == '-COMBO-COM-PORT-':
                self.imu.comPort = values['-COMBO-COM-PORT-']

            if event == '-COMBO-BAUD-RATE-':
                self.imu.baudRate = int(values['-COMBO-BAUD-RATE-'])

            if event == '-BUTTON-IMU-CONNECT-':
                self.toggleImuConnect()

    def drawFigure(self, figure, canvas):
        figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
        figure_canvas_agg.draw()
        figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
        return figure_canvas_agg

    def createPlot(self):
        fig = Figure(figsize=(5, 5), dpi=100)
        self.ax = fig.add_subplot(111, projection='3d')
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        self.ax.set_xlim((-5, 5))
        self.ax.set_ylim((-5, 5))
        self.ax.set_zlim((-5, 5))

        self.pointData = self.ax.plot([], [], [], color="red", linestyle="none", marker="o", animated=True)[0]
        self.lineData = self.ax.plot([], [], [], color="red", animated=True)[0]

        self.fig_agg = self.drawFigure(fig, self.window['-CANVAS-PLOT-'].TKCanvas)

        self.bg = self.fig_agg.copy_from_bbox(self.ax.bbox)

    def updatePlot(self):
        # Only plot if plotting is enabled, the IMU is connected, and a quaternion value is available.
        if self.enablePlotting and self.imu.isConnected and self.imu.quaternion:
            self.fig_agg.restore_region(self.bg)
            rpp = ut.rotatePoints(c.PROBE_POINTS, self.imu.quaternion)
            # Draw points
            for point in rpp:
                self.pointData.set_data([point[0]], [point[1]])
                self.pointData.set_3d_properties([point[2]])
                self.ax.draw_artist(self.pointData)

            # Draw lines between points
            # for i, point in enumerate(rpp):
            #     if not i < len(rpp) - 1:
            #         next_point = rpp[0, :]
            #         self.lineData.set_data([next_point[0], point[0]],
            #                                [next_point[1], point[1]])
            #         self.lineData.set_3d_properties([next_point[2], point[2]])
            #     else:
            #         next_point = rpp[i + 1, :]
            #         self.lineData.set_data([next_point[0], point[0]],
            #                                [next_point[1], point[1]])
            #         self.lineData.set_3d_properties([next_point[2], point[2]])
            #     self.ax.draw_artist(self.lineData)

            self.fig_agg.blit(self.ax.bbox)
            self.fig_agg.flush_events()

    def setAzimuth(self, azimuth):
        """
        Set the azimuth of the plot to the slider value. This allows for aligning the plot to the user's orientation
        since the IMU orientation is based on magnetic north.

        Args:
            azimuth (int): Azimuth to set the displayed plot to.
        """
        print(f'The azimuth will be set to: {azimuth}')

    def refreshComPorts(self):
        """
        Refresh the available COM ports. The list of available COM ports is updated as well as the drop down menu/list.
        """
        self.availableComPorts = IMU.availableComPorts()
        self.window['-COMBO-COM-PORT-'].update(values=self.availableComPorts)

    def toggleImuConnect(self):
        """
        Toggles the connection state of the IMU object. If the IMU is connected, it will be disconnected, else it will
        be connected using the values set in the Combo boxes or using the default initialisation values.
        """

        # If imu is not connected it must be connected, else disconnected.
        if not self.imu.isConnected:
            self.imu.connect()
        else:
            self.imu.disconnect()
        # Set colors and button states
        self.window['-COMBO-COM-PORT-'].update(disabled=True if self.imu.isConnected else False)
        self.window['-COMBO-BAUD-RATE-'].update(disabled=True if self.imu.isConnected else False)
        self.window['-BUTTON-IMU-CONNECT-'].update(
            button_color='#ff2121' if self.imu.isConnected else sg.DEFAULT_BUTTON_COLOR,
            text='Disconnect IMU' if self.imu.isConnected else 'Connect IMU'
        )

    def close(self):
        """
        Delete references to IMU and FrameGrabber objects for garbage collection. This ensures the resources are freed
        up for future use. Only called as the program is shutting down.
        """
        if self.imu.isConnected:
            self.imu.disconnect()
            del self.imu

        if self.frameGrabber.isConnected:
            del self.frameGrabber

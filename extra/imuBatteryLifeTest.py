"""
A Python script for testing the battery life of an IMU by running a test and updating the GUI until the IMU dies, at
which point the GUI will stop updating. When the test is stopped the details of the test are stored in the
DrainTests.txt file.
"""
from datetime import datetime as dt
from pathlib import Path

import PySimpleGUI as Psg
import witmotion as wm
from matplotlib.figure import Figure

# Custom constants used in the program.
import constants as c
# Custom styling.
import styling as st
import utils as ut
# Used to get the available COM ports.
from classes import IMU

# Location of refresh icon, stored for main program.
refresh_icon = str(Path().absolute().parent) + '\\icons\\refresh_icon.png'


class ImuBatterLifeTest:
    def __init__(self):
        # COM ports available on the system.
        self.com_ports = IMU.available_com_ports()
        # Number of messages received from the IMU device during a test.
        self.imu_counter = 0
        # File for saving IMU data of recording.
        self.save_file = None
        # IMU object and associated variables.
        self.imu = None
        self.imu_com_port = 'COM3'
        self.imu_baud_rate = c.COMMON_BAUD_RATES[6]
        self.quaternion = None
        self.acceleration = None
        self.angle = None
        self.rotate_imu_xy = False
        # Connection state of the IMU.
        self.imu_connected = False
        # Plotting variables: axis, points, lines, fig_agg, and bg set to None until initialised.
        self.ax = None
        self.point_data = None
        self.line_data = None
        self.fig_agg = None
        self.bg = None
        # Is a test currently running.
        self.testing = False
        self.test_start = dt.now().timestamp()
        self.test_last = dt.now().timestamp()
        self.test_elapsed = self.test_last - self.test_start
        # Create BatteryTests directory.
        self.battery_tests_path = ut.create_battery_test_directory()

        # Layout creation.
        self.layout = self.create_layout()
        # Create main window for display.
        self.window = Psg.Window('IMU Battery Tester', self.layout, finalize=True)

        self.create_orientation_plot(c.AZIMUTH)

        # Display loop.
        while True:
            self.update_imu_values()
            self.update_orientation_plot()
            event, values = self.window.read(0)
            if event in [Psg.WIN_CLOSED, 'None']:  # On window close clicked.
                break
            # Refresh available COM ports.
            if event == '-B-COM-REFRESH-':
                self.refresh_com_ports()
            # Combo of available COM ports.
            if event == '-COMBO-COM-PORT-':
                self.imu_com_port = values['-COMBO-COM-PORT-']
            # Combo of available baud rates.
            if event == '-COMBO-BAUD-RATE-':
                self.imu_baud_rate = int(values['-COMBO-BAUD-RATE-'])
            # Toggle IMU connection.
            if event == '-B-IMU-CONNECT-':
                self.toggle_imu_connect()
            # Set azimuth.
            if event == '-SLD-AZIMUTH-':
                self.set_azimuth(int(values['-SLD-AZIMUTH-']))
            # Set the return rate of the IMU.
            if event == '-COMBO-RETURN-RATE-':
                self.imu.set_update_rate(float(values['-COMBO-RETURN-RATE-'][:-2]))
            # Calibrate IMU acceleration.
            if event == '-B-IMU-CALIBRATE-':
                self.imu.send_config_command(wm.protocol.ConfigCommand(register=wm.protocol.Register.calsw, data=0x01))
            # Start a timed test.
            if event == '-B-TEST-START-':
                self.toggle_test()
            # Stop a timed test.
            if event == '-B-TEST-STOP-':
                self.toggle_test()

        # Close IMU connections manually.
        print('Program closing down...')

        if self.imu_connected:
            self.imu.ser.close()
            self.imu.close()

    def create_layout(self):
        """
        Create the layout for the program.

        Returns:
            layout (list): 2D list used by PySimpleGUI as the layout format.
        """
        # IMU controls.
        imu_layout = [
            [Psg.T('IMU Controls', s=(40, 1), justification='c', font=st.FONT_HEADING, p=((0, 0), (0, 20)))],
            [Psg.B(k='-B-COM-REFRESH-', button_text='', image_source=refresh_icon, image_subsample=4, border_width=3),
             Psg.Combo(k='-COMBO-COM-PORT-', default_value=self.imu_com_port, values=self.com_ports, s=7,
                       font=st.FONT_COMBO, enable_events=True, readonly=True),
             Psg.T('Baud Rate:', justification='r', font=st.FONT_DESCR, p=((20, 0), (0, 0))),
             Psg.Combo(k='-COMBO-BAUD-RATE-', default_value=self.imu_baud_rate, values=c.COMMON_BAUD_RATES, s=7,
                       font=st.FONT_COMBO, enable_events=True, readonly=True)],
            [Psg.B(k='-B-IMU-CONNECT-', button_text='Connect IMU', s=(15, 1), font=st.FONT_BTN, border_width=3,
                   p=((0, 0), (20, 20)))],
            [Psg.T('Return Rate:', justification='r', font=st.FONT_DESCR, p=((20, 0), (0, 0))),
             Psg.Combo(k='-COMBO-RETURN-RATE-', values=c.IMU_RATE_OPTIONS, s=7, font=st.FONT_COMBO, enable_events=True,
                       readonly=True, disabled=True),
             Psg.B(k='-B-IMU-CALIBRATE-', button_text='Calibrate Acc', s=(15, 1), font=st.FONT_BTN, border_width=3,
                   p=((40, 0), (0, 0)), disabled=True)]
        ]
        # Orientation plot.
        imu_plot_layout = [
            [Psg.T('IMU Orientation Plot', s=(40, 1), justification='c', font=st.FONT_HEADING)],
            [Psg.Canvas(k='-CANVAS-PLOT-', s=(500, 500))],
            [Psg.T('Select Azimuth', font=st.FONT_DESCR, p=((0, 0), (5, 0)))],
            [Psg.Sl(k='-SLD-AZIMUTH-', range=(0, 360), default_value=c.AZIMUTH, s=(40, 10),
                    orientation='h', enable_events=True)]
        ]
        # IMU values from callback.
        imu_values_layout = [
            [Psg.T('IMU Values (Raw)', s=(40, 1), justification='c', font=st.FONT_HEADING)],
            [Psg.T('Acceleration (m/s^2): ', justification='l', font=st.FONT_DESCR, s=(20, 1)),
             Psg.T(k='-TEXT-ACCELERATION-', text='', justification='r', font=st.FONT_DESCR, s=(30, 1))],
            [Psg.T('Quaternion: ', justification='l', font=st.FONT_DESCR, s=(20, 1)),
             Psg.T(k='-TEXT-QUATERNION-', text='', justification='r', font=st.FONT_DESCR, s=(30, 1))],
            [Psg.T('Euler Angles (deg): ', justification='l', font=st.FONT_DESCR, s=(20, 1)),
             Psg.T(k='-TEXT-ANGLE-', text='', justification='r', font=st.FONT_DESCR, s=(30, 1))]
        ]

        # Test start column.
        test_start_layout = [
            [Psg.T(text='Start Time', font=st.FONT_DESCR + ' underline', s=(15, 1))],
            [Psg.T(k='-TEXT-TEST-START-', font=st.FONT_DESCR, s=(15, 1))]
        ]

        # Test last message received column.
        test_last_layout = [
            [Psg.T(text='Last Message\nReceived At', font=st.FONT_DESCR + ' underline', s=(15, 1))],
            [Psg.T(k='-TEXT-TEST-LAST-', font=st.FONT_DESCR, s=(15, 1))]
        ]
        # Test elapsed time column.
        test_elapsed_layout = [
            [Psg.T(text='Elapsed Time', font=st.FONT_DESCR + ' underline', s=(15, 1))],
            [Psg.T(k='-TEXT-TEST-ELAPSED-', font=st.FONT_DESCR, s=(15, 1))]
        ]
        # Test counter layout
        test_counter_layout = [
            [Psg.T(text='Total Messages', font=st.FONT_DESCR + ' underline', s=(15, 1))],
            [Psg.T(k='-TEXT-TEST-COUNTER-', font=st.FONT_DESCR, s=(15, 1))]
        ]
        # Test control layout.
        test_control_layout = [
            [Psg.B(k='-B-TEST-START-', button_text='Start', font=st.FONT_BTN, border_width=3,
                   p=((0, 10), (20, 20)), disabled=True, button_color='#33ff77'),
             Psg.Col(test_start_layout, element_justification='c', vertical_alignment='t'),
             Psg.Col(test_last_layout, element_justification='c', vertical_alignment='t'),
             Psg.Col(test_elapsed_layout, element_justification='c', vertical_alignment='t'),
             Psg.Col(test_counter_layout, element_justification='c', vertical_alignment='t'),
             Psg.B(k='-B-TEST-STOP-', button_text='Stop', font=st.FONT_BTN, border_width=3,
                   p=((0, 10), (20, 20)), disabled=True, button_color='#ff2121')],
            [Psg.T('Test Name', font=st.FONT_DESCR, justification='l'),
             Psg.I(k='-INP-TEST-NAME-', justification='l', default_text='Drain Test')]
        ]
        # Total layout.
        layout = [
            [Psg.Col(imu_layout, element_justification='c', vertical_alignment='t', justification='c')],
            [Psg.HSep(p=((0, 10), (10, 20)))],
            [Psg.Col(imu_plot_layout, element_justification='c', vertical_alignment='t'),
             Psg.Col(imu_values_layout, element_justification='c', vertical_alignment='t')],
            [Psg.HSep(p=((0, 10), (10, 20)))],
            [Psg.Col(test_control_layout, element_justification='c', vertical_alignment='t',
                     justification='c')]
        ]

        return layout

    def toggle_test(self):
        """
        Toggle the testing state of the program. If true, reset imuTestCounter and instantiate testStartTime, else save
        test data to file.
        """
        self.testing = not self.testing
        print(f'Start a test: {self.testing}')

        if self.testing:
            self.imu_counter = 0
            self.test_start = dt.now().timestamp()
        else:
            self.save_to_file()

        # Set element states.
        self.window['-B-TEST-START-'].update(disabled=True if self.testing else False)
        self.window['-B-TEST-STOP-'].update(disabled=True if not self.testing else False)
        self.window['-TEXT-TEST-START-'].update(
            f"{dt.fromtimestamp(self.test_start).strftime('%H:%M:%S.%f')[:-3]}s" if self.testing else "")
        self.window['-TEXT-TEST-LAST-'].update('' if self.testing else "No Test Running")
        self.window['-TEXT-TEST-ELAPSED-'].update('')
        self.window['-B-IMU-CONNECT-'].update(disabled=True if self.testing else False)

    def refresh_com_ports(self):
        """
        Refresh the available COM ports. The list of available COM ports is updated as well as the related Combo box.
        """
        self.com_ports = IMU.available_com_ports()
        self.window['-COMBO-COM-PORT-'].update(values=self.com_ports)

    def toggle_imu_connect(self):
        """
        Toggles the connection state of the IMU. If the IMU is connected, it will be disconnected, else it will
        be connected using the values set in the Combo boxes.
        """

        # If imu is not connected it must be connected, else disconnected.
        if not self.imu_connected:
            print(f'Attempting to connect to {self.imu_com_port} at {self.imu_baud_rate}...')
            try:
                self.imu = wm.IMU(self.imu_com_port, self.imu_baud_rate)
                self.imu.subscribe(self.imu_callback)
                self.imu_connected = True
            except Exception as e:
                print(f'Error connecting to IMU: {e}.')
                self.imu_connected = False
        else:
            print(f'Disconnecting from {self.imu_com_port} as {self.imu_baud_rate}...')
            self.imu.close()
            self.imu.ser.close()
            self.imu_connected = False
        # Set element states
        self.window['-COMBO-COM-PORT-'].update(disabled=True if self.imu_connected else False)
        self.window['-COMBO-BAUD-RATE-'].update(disabled=True if self.imu_connected else False)
        self.window['-B-IMU-CONNECT-'].update(
            button_color='#ff2121' if self.imu_connected else Psg.DEFAULT_BUTTON_COLOR,
            text='Disconnect IMU' if self.imu_connected else 'Connect IMU'
        )
        self.window['-COMBO-RETURN-RATE-'].update(disabled=True if not self.imu_connected else False)
        self.window['-B-IMU-CALIBRATE-'].update(disabled=True if not self.imu_connected else False)
        self.window['-B-TEST-START-'].update(disabled=True if not self.imu_connected else False)

    def create_orientation_plot(self, azimuth):
        """
        Instantiate the initial plotting variables: The Figure and the axis, and the 2 plot parameters that store the
        line and point data. This is also called when changing the azimuth of the plot as the entire canvas needs to
        be redrawn.

        Args:
            azimuth (int): Azimuth angle in degrees.
        """
        fig = Figure(figs=(4, 4), dpi=100)
        self.ax = fig.add_subplot(111, projection='3d')
        fig.patch.set_facecolor(Psg.DEFAULT_BACKGROUND_COLOR)
        self.ax.set_position((0, 0, 1, 1))

        self.ax = ut.initialise_axis(self.ax, azimuth)
        self.ax.disable_mouse_rotation()

        self.fig_agg = ut.draw_figure(fig, self.window['-CANVAS-PLOT-'].TKCanvas)

        self.bg = self.fig_agg.copy_from_bbox(self.ax.bbox)

        self.point_data = self.ax.plot([], [], [], color="red", linestyle="none", marker="o", animated=True)[0]
        self.line_data = self.ax.plot([], [], [], color="red", animated=True)[0]

    def update_orientation_plot(self):
        """
        Update the plot to show orientation of the IMU unit. Restores the axis region that does not need to be
        recreated (bg), then adds the points to the axis. Blit is used to increase plot speed substantially. This
        currently limits the plot to lines and points, surfaces are not used.
        """
        # Only plot if the IMU is connected, and a quaternion value is available.
        if self.imu_connected and self.quaternion:
            self.fig_agg.restore_region(self.bg)

            self.ax = ut.plot_orientation_on_axis(self.ax, self.quaternion, self.point_data, self.line_data)

            self.fig_agg.blit(self.ax.bbox)
            self.fig_agg.flush_events()

    def set_azimuth(self, azimuth):
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
        self.ax = ut.initialise_axis(self.ax, azimuth)
        # Redraw new axis.
        self.fig_agg.draw()
        # Re-save background for blit.
        self.bg = self.fig_agg.copy_from_bbox(self.ax.bbox)

    def imu_callback(self, msg):
        """
        Callback subscribed to the IMU object. Called whenever a new dataset is available. This callback is
        activated for every value sent by the IMU (Acceleration, Quaternion, Angle, ..etc) and not just for each
        serial packet. The counter only increments when a quaternion message is read.

        This callback is handled off the main thread, and as such no GUI updates should take place from functions
        originating here.

        Args:
            msg (String): The type of dataset that is newly available.
        """
        msg_type = type(msg)

        if msg_type is wm.protocol.AccelerationMessage:
            self.acceleration = self.imu.get_acceleration()
        elif msg_type is wm.protocol.AngleMessage:
            self.angle = self.imu.get_angle()
        elif msg_type is wm.protocol.QuaternionMessage:
            self.quaternion = self.imu.get_quaternion()
            self.test_last = dt.now().timestamp()
            self.imu_counter += 1

    def update_imu_values(self):
        """
        Update the shown IMU and test values if they are available.
        """
        if self.imu_connected:
            if self.acceleration:
                self.window['-TEXT-ACCELERATION-'].update(
                    f'[{self.acceleration[0]:.4f}, {self.acceleration[1]:.4f}, {self.acceleration[2]:.4f}]')
            if self.quaternion:
                self.window['-TEXT-QUATERNION-'].update(
                    f'[{self.quaternion[0]:.4f}, {self.quaternion[1]:.4f}, {self.quaternion[2]:.4f}, '
                    f'{self.quaternion[3]:.4f}]')
            if self.angle and self.angle[0]:
                self.window['-TEXT-ANGLE-'].update(f'[{self.angle[0]:.4f}, {self.angle[1]:.4f}, {self.angle[2]:.4f}]')

            if self.testing:
                self.window['-TEXT-TEST-LAST-'].update(
                    f"{dt.fromtimestamp(self.test_last).strftime('%H:%M:%S.%f')[:-3]}s")
                self.window['-TEXT-TEST-ELAPSED-'].update(
                    f"{dt.fromtimestamp(max(self.test_last - self.test_start, 0)).strftime('%H:%M:%S')}s")
                self.window['-TEXT-TEST-COUNTER-'].update(
                    f'{self.imu_counter}'
                )

    def save_to_file(self):
        """
        Save details of the test to the DrainTests.txt file.

        Future note: Calling save_to_file from the IMU callback was causing threading issues as updating GUI from
        a non-main thread is a problem.
        """

        self.save_file = open(
            Path(self.battery_tests_path, 'DrainTests.txt'), 'a')

        self.save_file.write(
            f"{self.window['-INP-TEST-NAME-'].get()} "
            f"Started: {dt.fromtimestamp(self.test_start).strftime('%d %m %Y - %H:%M:%S')}, "
            f"Test Completed: {dt.fromtimestamp(dt.now().timestamp()).strftime('%d %m %Y - %H:%M:%S')}, "
            f"Last Message: {dt.fromtimestamp(self.test_last).strftime('%d %m %Y - %H:%M:%S')}, "
            f"Run Time: {dt.fromtimestamp(self.test_last - self.test_start).strftime('%H:%M:%S')}, "
            f"Total Messages received: {self.imu_counter}\n")

        self.save_file.close()


ImuBatterLifeTest()

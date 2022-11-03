"""
Class for creating the menu bar based on the state of variables in DataCaptureDisplay class.
"""
import constants as c


class Menu:
    def __init__(self):
        # Set initial values
        self.frameGrabberConnected = False
        self.imuConnected = False
        self.signalMenu = None
        self.imuImenu = None
        # Initial creation of menus.
        self.__generate_menus()

    def get_menu(self, frame_grabber_connected=False, imu_connected=False):
        """
        Return the current menu bar based on the parameter values given. The local parameter values are updated based on
        the given parameters and the menus are generated. The generated menus are combined into a single menu bar layout
        and returned.

        Args:
            frame_grabber_connected (bool): True if FrameGrabber object is connected, else False.
            imu_connected (bool): True if IMU object is connected, else False.

        Returns:
            menu_final (list): Final menu layout.
        """
        # Local variable update.
        self.frameGrabberConnected = frame_grabber_connected
        self.imuConnected = imu_connected
        # Generate menus.
        self.__generate_menus()

        menu_final = [self.signalMenu, self.imuImenu]
        # Return menu bar layout.
        return menu_final

    def __generate_signal_menu(self):
        """
        Function for creating signal source menus based on the connection status of the FrameGrabber object. For
        selecting the video source and changing its properties. If self.frameGrabberConnected:

        False (initial state):      Menu to show when the signal source is not connected. Since there is no signal,
                                    the signal properties cannot be changed.
        True (post connection):     Menu to show when the signal source is connected. Now that the source is connected,
                                    the source signal can be changed, it can be disconnected, and properties can be
                                    changed.
        """
        if not self.frameGrabberConnected:
            self.signalMenu = ['Signal Source', ['Connect to Source',
                                                 [f'{i}::-M-SIGNAL-CONNECT-' for i in
                                                  range(0, c.SIGNAL_SOURCES + 1)],
                                                 '---',
                                                 '!Change Signal Dimensions',
                                                 ]
                               ]
        if self.frameGrabberConnected:
            self.signalMenu = ['Signal Source', ['Disconnect from Source::-M-SIGNAL-DISCONNECT-',
                                                 '---',
                                                 'Change Signal Dimensions',
                                                 [f'{i[0]}::-M-SIGNAL-DIMENSIONS-' for i in
                                                  c.COMMON_SIGNAL_DIMENSIONS]
                                                 ]
                               ]

    def __generate_imu_menu(self):
        """
        Function for creating imu menus based on the connection status of the IMU object. For controlling the
        connection to the IMU. if self.imuConnected:

        False (initial state):      Menu to show when the IMU is not connected. Since the IMU is not connected the
                                    return rate cannot be changed and the acceleration cannot be calibrated, so these
                                    options are disabled.
        True (post connection):     Menu to show when the IMU has been connected, enabling return rate and acceleration
                                    calibration.
        """
        if not self.imuConnected:
            self.imuImenu = ['IMU', ['Connect::-M-IMU-CONNECT-',
                                     '---',
                                     '!Set Return Rate',
                                     '!Set Bandwidth',
                                     '!Set Algorithm',
                                     '!Calibrate Acceleration::-M-IMU-CALIBRATE-']
                             ]
        if self.imuConnected:
            self.imuImenu = ['IMU', ['Disconnect::-M-IMU-DISCONNECT-',
                                     '---',
                                     'Set Return Rate', [f'{i}::-M-IMU-RATE-' for i in c.IMU_RATE_OPTIONS],
                                     'Set Bandwidth', [f'{i}::-M-IMU-BANDWIDTH-' for i in c.IMU_BANDWIDTH_OPTIONS],
                                     'Set Algorithm', [f'{i}::-M-IMU-ALGORITHM-' for i in c.IMU_ALGORITHM_OPTIONS],
                                     'Calibrate Acceleration::-M-IMU-CALIBRATE-']
                             ]

    def __generate_menus(self):
        """
        Function to call individual menu generating functions. More menus can be added, which now only require a single
        function to create the menu and a single call to this __generate_menus function.
        """
        # Signal Menu.
        self.__generate_signal_menu()
        # IMU Menu.
        self.__generate_imu_menu()

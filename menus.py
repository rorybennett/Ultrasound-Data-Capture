"""
Contains all menus and their derivatives used throughout the lifecycle of the program. It seems that to update a menu
in PySimpleGUI you have to recall/recreate the enu from scratch. Having the menus in a separate file cleans up the main
class.
"""
import constants as c

"""
Signal source menus. For selecting the video source and changing its properties.

menuSignalDisconnected:     Menu to show when the signal source is not connected. Since there is no signal, the signal
                            properties cannot be changed.
menuSignalConnected:        Menu to show when the signal source is connected. Now that the source is connected, the 
                            source signal can be changed, it can be disconnected, and properties can be changed.
"""
menuSignalDisconnected = ['Signal Source', ['Connect to Source::-MENU-SIGNAL-CONNECT-',
                                            '!Disconnect from Source::-MENU-SIGNAL-DISCONNECT-',
                                            '---',
                                            '!Change Signal Dimensions::-MENU-SIGNAL-DIMENSIONS',
                                            ]
                          ]

menuSignalConnected = ['Signal Source', ['Change Source::-MENU-SIGNAL-CHANGE-',
                                         'Disconnect from Source::-MENU-SIGNAL-DISCONNECT-',
                                         '---',
                                         'Change Signal Dimensions::-MENU-SIGNAL-DIMENSIONS',
                                         [f'{i}::-MENU-SIGNAL-DIMENSIONS-' for i in c.COMMON_SIGNAL_DIMENSIONS]
                                         ]
                       ]

"""
Imu menus. For controlling the connection to the IMU.

imuMenuDisconnected:    Menu to show when the IMU is not connected. Since the IMU is not connected the return rate 
                        cannot be changed and the acceleration cannot be calibrated, so these options are disabled.
imuMenuConnected:       Menu to show when the IMU has been connected, enabling return rate and acceleration calibration.
                        
"""
menuImuDisconnected = ['IMU', ['Connect::-MENU-IMU-CONNECT-',
                               '---',
                               '!Set Return Rate',
                               '!Calibrate Acceleration::-MENU-IMU-CALIBRATE-']
                       ]

menuImuConnected = ['IMU', ['Disconnect::-MENU-IMU-DISCONNECT-',
                            '---',
                            'Set Return Rate', [f'{i}::-MENU-IMU-RATE-' for i in c.IMU_RATE_OPTIONS],
                            'Calibrate Acceleration::-MENU-IMU-CALIBRATE-']
                    ]

"""
Contains all menus and their derivatives used throughout the lifecycle of the program. It seems that to update a menu
in PySimpleGUI you have to recall/recreate the enu from scratch. Having the menus in a separate file cleans up the main
class.
"""
import constants as c

"""
Video source menu. For selecting the video source and changing its properties.
"""
menuVideoSource = ['Video Source', ['1']]

"""
Imu menus. 

imuMenuDisconnected:    Menu to show when the IMU is not connected. Since the IMU is not connected the return rate 
                        cannot be changed and the acceleration cannot be calibrated, so these options are disabled.
imuMenuConnected:       Menu to show when the IMU has been connected, enabling return rate and acceleration calibration.
                        
"""
menuImuDisconnected = ['IMU', ['Connect::-MENU-IMU-CONNECT-',
                               '---',
                               '!Set Return Rate', [f'{i}::-MENU-IMU-RATE-' for i in c.IMU_RATE_OPTIONS],
                               '!Calibrate Acceleration::-MENU-IMU-CALIBRATE-']]

menuImuConnected = ['IMU', ['Disconnect::-MENU-IMU-DISCONNECT-',
                            '---',
                            'Set Return Rate', [f'{i}::-MENU-IMU-RATE-' for i in c.IMU_RATE_OPTIONS],
                            'Calibrate Acceleration::-MENU-IMU-CALIBRATE-']]

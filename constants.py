"""
This file contains constant values used by the program.
"""

# List of commonly used baud rates, add more if required.
COMMON_BAUD_RATES = [
    2400,
    4800,
    9600,
    19200,
    38400,
    57600,
    115200,
    230400,
    460800,
    576000
]

# Points used for visual representation of the ultrasound probe in a 3D space. Order matters.
PROBE_POINTS = [
    [0, 0, 0],
    [-1, -.3, 0],
    [-2, -.8, 0],
    [0, -6, 0],
    [2, -.8, 0],
    [1, -.3, 0]]

# Default azimuth value used for the 3D plot.
DEFAULT_AZIMUTH = 30

# Available return rates for the IMU. The Witmotion library limits the number of return rates that are available.
IMU_RATE_OPTIONS = [
    "0.2Hz",
    "0.5Hz",
    "1Hz",
    "2Hz",
    "5Hz",
    "10Hz",
    "20Hz",
    "50Hz",
    "100Hz"
]

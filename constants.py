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
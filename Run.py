"""
A Python script for running the DataCaptureDisplay program.
"""
from classes import DataCaptureDisplay


def main():
    DataCaptureDisplay.DataCaptureDisplay()


if __name__ == '__main__':
    main()


"""
TODO:
    -Clear plot when switching between editing and not editing. Just need an IMU to test if this is being implemented
     correctly.
    -Consider the top of the frame displayed is not part of the IMU. The output of the Us scanner has a lot of
     extra information surrounding the image. A square POI is required within the output signal.
    -Make mainWindow timeout a variable that is None when signal is disconnected, and 1 when it is connected.
"""

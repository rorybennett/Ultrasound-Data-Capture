"""
Class for details about a video. All the details will be stored in this class, including editing information.
"""
from pathlib import Path
import time
import csv
import utils as ut


class VideoDetails:
    def __init__(self, videosPath: Path, videoDirectory: str):
        """
        Initially created variables for the VideoDetails class:
            path (str)          -       Full path to the video directory.
            date (str)          -       Date and time recording was started (in a more easy to read format).
            duration (str)      -       How long the test was run for (in HH:MM:SS).

            Args:
                videosPath (Path): Path to the Generated/Videos directory (parent of the recording).
                videoDirectory (str): Local path to the selected video directory.
        """
        # Path to video recording.
        self.path = Path(videosPath, videoDirectory).as_posix()
        # Date of recording, with time.
        self.date = time.strftime('%H:%M:%S on %d %B %Y', time.strptime(videoDirectory, '%d %m %Y %H-%M-%S,%f'))
        # Number of IMU lines, should be the same as frameCount.
        self.imuCount = 0
        # Number of frames saved as .png images.
        self.frameCount = 0
        # Duration of recording
        self.duration = 0
        # Frame names as read from data.txt file.
        self.frameNames = []
        # Acceleration data.
        self.acceleration = []
        # Quaternion data.
        self.quaternion = []
        # Dimensions of signal, per frame basis.
        self.dimensions = []

        self.__getImuDataFromFile()

    def __getImuDataFromFile(self):
        """
        Helper function for acquiring information from the data.txt file. This includes:
            frameNames      -       Names of the stored frames (should match with actual stored frames).
            acceleration    -       All acceleration values stored during recording.
            quaternion      -       All quaternion values stored during recording.
            dimensions      -       Dimensions of all frames (should all be the same, but not necessary).
            imuCount        -       Total rows in the file.
            duration        -       Duration of recording based on first and last frame names.
        Tests are conducted to ensure that the imuCount (lines) matches the number of saved frames in the data.txt file.
        The number of saved frames comes from the frameGrabberCounter in the DataCaptureDisplay class.
        """
        # Information acquired from the IMU data.txt file.
        with open(self.path + '/data.txt', 'r') as dataFile:
            reader = csv.reader(dataFile)
            for row in reader:
                self.frameNames.append(row[0])
                self.acceleration.append(ut.getAccelerationFromRow(row))
                self.quaternion.append(ut.getQuaternionFromRow(row))
                self.dimensions.append(ut.getDimensionsFromRow(row))
            self.imuCount = len(self.frameNames)
            self.duration = ut.getTimeFromName(self.frameNames[0]) - ut.getTimeFromName(self.frameNames[-1])

            # Test to ensure frame number in data.txt file matches number of lines.
            lastFrameNumber = int(row[0].split('-')[0])
            if lastFrameNumber != self.imuCount:
                print(f'!!! There is an inconsistency in the data.txt file. The number of lines {self.imuCount} and '
                      f'the frame number {lastFrameNumber} do not match. !!!')




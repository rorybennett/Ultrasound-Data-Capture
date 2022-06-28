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
            details (dict)      -       Supplementary details about the recording:
                path (str)          -       Full path to the video directory.
                date (str)          -       Date and time recording was started (in a more easy to read format).
                imuCount (int)      -       Total lines in data.txt (number of imu values available).
                duration (str)      -       How long the test was run for (in HH:MM:SS).

            frameCount (int)    -       Number of frames stored as .png images in the directory.
            frameNames (list)   -       All frame names as stored in the data.txt file (should match frame names
                                        in directory).
            acceleration (list) -       Acceleration values stored in data.txt file.
            quaternion (list)   -       Quaternion values stored in data.txt file.
            dimensions (list)   -       Frame dimensions stored in data.txt file.


            Args:
                videosPath (Path): Path to the Generated/Videos directory (parent of the recording).
                videoDirectory (str): Local path to the selected video directory.
        """
        # Supplementary details about the recording, path and date.
        self.details = {'path': Path(videosPath, videoDirectory).as_posix(),
                        'date': time.strftime('%H:%M:%S on %d %B %Y',
                                              time.strptime(videoDirectory, '%d %m %Y %H-%M-%S,%f'))}

        # Number of frames saved as .png images.
        self.frameCount = ut.getFrameCountInDirectory(Path(self.details['path']))
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
        with open(self.details['path'] + '/data.txt', 'r') as dataFile:
            reader = csv.reader(dataFile)
            for row in reader:
                self.frameNames.append(row[0])
                self.acceleration.append(ut.getAccelerationFromRow(row))
                self.quaternion.append(ut.getQuaternionFromRow(row))
                self.dimensions.append(ut.getDimensionsFromRow(row))
            self.details['imuCount'] = len(self.frameNames)
            self.details['duration'] = ut.getTimeFromName(self.frameNames[0]) - ut.getTimeFromName(self.frameNames[-1])

            """
            Run some variable validation tests to ensure the numbers match. If they do not, display a warning.
            This wont stop the program running but it will indicate future problems that may occur.
            """
            # Check if the last frame number in the data.txt file matches the total number of rows.
            lastFrameNumber = int(row[0].split('-')[0])
            if lastFrameNumber != self.details['imuCount']:
                print(f"!!! There is an inconsistency in the data.txt file."
                      f" The number of lines {self.details['imuCount']} and the frame number {lastFrameNumber}"
                      f" do not match. !!!")
            # Check if the number of saved .png frames matches the number of rows.
            if self.frameCount != self.details['imuCount']:
                print(f"!!! There is an inconsistency between the data.txt file and the number of saved frames in the "
                      f"video directory. The number of saved frames {self.frameCount} and the number of lines"
                      f" {self.details['imuCount']} do not match. !!!")

"""
Class for details about a video. All the details will be stored in this class, including editing information.
"""
from pathlib import Path
import time
import csv


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
        # Number of IMU lines, should be the same as number of frames.
        self.imuCount = None
        # Duration of recording
        self.duration = None
        # Frame names as read from data.txt file.
        self.frameNames = []
        # Acceleration data.
        self.acceleration = []
        # Quaternion data.
        self.quaternion = []

        # Information acquired from the IMU data.txt file.
        with open(self.path + '/data.txt', 'r') as dataFile:
            reader = csv.reader(dataFile)
            for row in reader:
                self.frameNames.append(self.__getTimeFromRow(row))
                self.acceleration.append(self.__getAccelerationFromRow(row))
                self.quaternion.append(self.__getQuaternionFromRow(row))

    def __getTimeFromRow(self, row: list) -> str:
        """
        Extract the time from a row. This is the same as the frame name. The second element in the row after frame
        number (separated by '-').

        Args:
            row (str): Pulled from csv.reader.

        Returns:
            timeAsString (str): String representation of the frame name, same as the time.
        """
        timeAsString = row[0].split('-')[1]
        return timeAsString

    def __getAccelerationFromRow(self, row: list) -> list:
        """
        Extract the acceleration from a row. The third, fourth, and fifth elements in the row.

        Args:
            row (str): Pulled from csv.reader.

        Returns:
            acc (list): List of the three acceleration values in the x, y, and z directions.
        """
        acc = [float(row[2]), float(row[3]), float(row[4])]
        return acc

    def __getQuaternionFromRow(self, row: list) -> list:
        """
        Extract the quaternion from a row. The 7, 8, 9, and 10 elements in the row.

        Args:
            row (str): Pulled from csv.reader.

        Returns:
            qua (list): List of the 4 quaternion values.
        """
        qua = [float(row[6]), float(row[7]), float(row[8]), float(row[9])]
        return qua





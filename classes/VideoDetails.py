"""
Class for details about a video. All the details will be stored in this class, including editing information.
"""
from pathlib import Path
import time


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
        # Duration of recording
        self.duration = None
        #

        # Information acquired from the IMU data.txt file.
        with open(self.path + 'data.txt', 'r') as dataFile:




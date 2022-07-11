"""
Class for details about a recording. All the details will be stored in this class, including editing information.
"""
from pathlib import Path
import time
import csv
import cv2
import numpy as np

import utils as ut
import constants as c


class RecordingDetails:
    def __init__(self, videosPath: Path, recordingDirectory: str):
        """
        Initially created variables for the RecordingDetails class:
            path (str)                  -       Full path to the video directory.
            date (str)                  -       Date and time recording was started (in a more easy to read format).
            imuCount (int)              -       Total lines in data.txt (number of imu values available).
            duration (str)              -       How long the test was run for (in milliseconds).
            frameCount (int)            -       Number of frames stored as .png images in the directory.
            frameNames (list)           -       All frame names as stored in the data.txt file (should match frame names
                                                in directory).
            acceleration (list)         -       Acceleration values stored in data.txt file.
            quaternion (list)           -       Quaternion values stored in data.txt file.
            dimensions (list)           -       Frame dimensions stored in data.txt file.
            currentFramePosition (int)  -       Position of current frame of interest.
            editingPath (str)           -       Path to EditingData.txt file.
            scanDepth (int)             -       Depth of scan in millimetres.
            frameOffset (int)           -       Top offset between frame and ultrasound start.


            Args:
                videosPath (Path): Path to the Generated/Videos directory (parent of the recording).
                recordingDirectory (str): Local path to the selected video directory.
        """
        # Path to recording directory.
        self.path = Path(videosPath, recordingDirectory).as_posix()
        # Date recording took place.
        self.date = time.strftime('%d %b %Y\n%H:%M:%S', time.strptime(recordingDirectory, '%d %m %Y %H-%M-%S,%f'))
        # Duration of recording.
        self.duration = 0
        # Number of frames saved as .png images.
        self.frameCount = ut.getFrameCountInDirectory(Path(self.path))
        # Frame names as read from data.txt file.
        self.frameNames = []
        # Acceleration data.
        self.acceleration = []
        # Quaternion data.
        self.quaternion = []
        # Dimensions of signal, per frame basis.
        self.dimensions = []
        # Depth of the scan, per frame basis.
        self.depths = []
        # Tracks position of current frame being displayed, starts at 1.
        self.currentFramePosition = 1

        self.__getImuDataFromFile()

        # Estimated fps of recording.
        self.fps = int(1000 * self.frameCount / self.duration)

        # Path to EditingData.txt file.
        self.editingPath = ''
        # Offsets between top, bottom, left, and right of frame and scan in fractions of display dimensions.
        self.recordingOffsetTop = 0
        self.recordingOffsetBottom = 0.999
        self.recordingOffsetLeft = 0
        self.recordingOffsetRight = 0.999
        # Path to PointData.txt.
        self.pointPath = ''
        # Point data of the frames.
        self.pointData = []

        self.__getEditDetailsFromFile()
        self.__getPointDataFromFile()

    def plotDataPointsOnAxis(self, axis, pointPlot):
        """
        Plot all self.pointData on the given axis. Each point has a frame with an associated Quaternion, which is used
        to rotate the point before plotting it. There will be some scaling involved, but the final plot will show
        all the point data in 3D space.

        Args:
            axis (axis): Axis on to which the points are plot.
            pointPlot (axis.plot): Used by the artis to draw points.

        Returns:
            axis (axis): Axis containing newly plotted points.
        """
        pointPlot.set_markersize(2)
        for row in self.pointData:
            # Position of frame name belonging to point.
            position = self.frameNames.index(row[0])
            # Quaternion of frame in question.
            quaternion = self.quaternion[position]
            # Depth ratio used to go from pixel ratio to mm for height.
            depthRatio = self.depths[position] / (
                (self.recordingOffsetBottom - self.recordingOffsetTop))
            # Width ratio used to go from pixel ratio to mm for width.
            widthRatio = self.depths[position] / (
                (self.recordingOffsetRight - self.recordingOffsetLeft))
            # Extract point from line.
            point = [[(row[1] - self.recordingOffsetLeft) * widthRatio, (row[2] - self.recordingOffsetTop) * depthRatio, 0]]

            print(point)

            axis = ut.plotPointOnAxis(axis, quaternion, point, pointPlot)

        return axis

    def __saveDetailsToFile(self):
        """
        Save all in memory data to relevant .txt files. This should be called whenever a value is changed. All previous
        values are overwritten and the current values stored.
        """
        try:
            with open(self.editingPath, 'w') as editingFile:
                editingFile.write(f'recordingOffsetTop:{self.recordingOffsetTop}\n')
                editingFile.write(f'recordingOffsetBottom:{self.recordingOffsetBottom}\n')
                editingFile.write(f'recordingOffsetLeft:{self.recordingOffsetLeft}\n')
                editingFile.write(f'recordingOffsetRight:{self.recordingOffsetRight}\n')

            with open(self.pointPath, 'w') as pointFile:
                for point in self.pointData:
                    pointFile.write(f'{point[0]},{point[1]},{point[2]}\n')

            if self.imuCount == self.frameCount:
                with open(self.path + '/data.txt', 'w') as dataFile:
                    for i in range(self.imuCount):
                        dataFile.write(f'{self.frameNames[i]},:'
                                       f'acc[,{self.acceleration[i][0]},{self.acceleration[i][1]},{self.acceleration[i][2]},]'
                                       f'q[,{self.quaternion[i][0]},{self.quaternion[i][1]},{self.quaternion[i][2]},'
                                       f'{self.quaternion[i][3]},]'
                                       f'dimensions[,{self.dimensions[i][0]},{self.dimensions[i][1]},]'
                                       f'depth[,{self.depths[i]},]\n')
            else:
                print('Due to the inconsistencies between frame number and imu data count, data cannot be saved.')
        except Exception as e:
            print(f'Error saving details to file: {e}')

    def addRemovePointData(self, point: [float, float]):
        """
        Add or remove a point to/from self.pointData. Point data is saved as a fraction of the display dimensions. A
        point is removed if it is within a certain proximity to a previous point.
        Since the Graph element starts from the bottom left (Image from top left), some conversions need to take place.
        All work on frames/images/graphs will work under the assumption that (0, 0) is the top left of the element.

        Args:
            point [float, float]: x/width-, and y/height-coordinates returned by the Graph elements' event
        """
        widthRatio = point[0] / c.DEFAULT_DISPLAY_DIMENSIONS[0]
        heightRatio = (c.DEFAULT_DISPLAY_DIMENSIONS[1] - point[1]) / c.DEFAULT_DISPLAY_DIMENSIONS[1]

        newPoint = [widthRatio, heightRatio]

        # Check if within radius, if NOT, add point, else remove a point.
        if not self.__checkIfWithinRadiusOfOtherPoints(newPoint):
            self.pointData.append([self.frameNames[self.currentFramePosition - 1], newPoint[0], newPoint[1]])

        self.__saveDetailsToFile()

    def __checkIfWithinRadiusOfOtherPoints(self, point: [float, float]) -> bool:
        """
        Check if the given point is with the constant radius of any other points that are already present. If it is
        within an already saved points radius, remove the saved point and leave the function. This means only one point
        can be removed at a time and points will be removed until there are no already saved points within range of the
        point that is to be newly added.

        Args:
            point [float, float]: New point to be tested against already saved points.

        Returns:
            withinRadius (bool): True if any point was within the radius, else False.
        """
        withinRadius = False

        for centrePoint in self.pointData:
            if ut.pointWithinRadius([centrePoint[1], centrePoint[2]], point):
                self.pointData.remove(centrePoint)
                withinRadius = True
                break
        return withinRadius

    def changeScanDepth(self, newScanDepth: float):
        """
        Change the scan depth of the current frame that is being edited. The scan depth can be a float and is
        read from the screen of the ultrasound image. This is manual for now, but perhaps that can be automated
        at some point.

        Args:
            newScanDepth (float): Depth of the ultrasound scan as read from the signal display.
        """
        try:
            newScanDepth = float(newScanDepth)
            self.depths[self.currentFramePosition - 1] = newScanDepth
            self.__saveDetailsToFile()
        except Exception as e:
            print(f'Error updating scan depth, ensure a float was entered: {e}')

    def changeOffsetTop(self, newOffset: int):
        """
        Change the top frame offset of the recording. If it is found that the offset can change,
        this will have to be changed to per frame basis.

        Args:
            newOffset (int): Offset between the top of the frame and the start of the scan as a ratio.
        """
        try:
            newOffset = float(newOffset)
            self.recordingOffsetTop = newOffset
            self.__saveDetailsToFile()
        except Exception as e:
            print(f'Error updating top offset, ensure that an integer was entered: {e}')

    def changeOffsetBottom(self, newOffset: int):
        """
        Change the bottom frame offset of the recording. If it is found that the offset can change,
        this will have to be changed to per frame basis.

        Args:
            newOffset (int): Offset between the bottom of the frame and the end of the scan as a ratio.
        """
        try:
            newOffset = float(newOffset)
            self.recordingOffsetBottom = newOffset
            self.__saveDetailsToFile()
        except Exception as e:
            print(f'Error updating top offset, ensure that an integer was entered: {e}')

    def changeOffsetLeft(self, newOffset: int):
        """
        Change the left frame offset of the recording. If it is found that the offset can change,
        this will have to be changed to per frame basis.

        Args:
            newOffset (int): Offset between the left of the frame and the left of the scan as a ratio.
        """
        try:
            newOffset = float(newOffset)
            self.recordingOffsetLeft = newOffset
            self.__saveDetailsToFile()
        except Exception as e:
            print(f'Error updating top offset, ensure that an integer was entered: {e}')

    def changeOffsetRight(self, newOffset: int):
        """
        Not using for now.

        Change the right frame offset of the recording. If it is found that the offset can change,
        this will have to be changed to per frame basis.

        Args:
            newOffset (int): Offset between the right of the frame and the end of the scan as a ratio.
        """
        try:
            newOffset = float(newOffset)
            self.recordingOffsetRight = newOffset
            self.__saveDetailsToFile()
        except Exception as e:
            print(f'Error updating top offset, ensure that an integer was entered: {e}')

    def navigateFrames(self, navCommand):
        """
        Navigate through the frames according to the navCommand parameter. The navCommand is a string that can either be
        converted to an integer for a specific frame number or a navigation command:
            str -   String representation of frame number.
            PPP -   Move back 10 frames.
            PP  -   Move back 5 frames.
            P   -   Move back 1 frame.
            N   -   Move forward 1 frame.
            NN  -   Move forward 5 frames.
            NNN -   Move forward 10 frames.

        Args:
            navCommand (str): String representation of the navigation command.
        """
        try:
            goToFrame = int(navCommand)
            if self.frameCount >= goToFrame > 0:
                self.currentFramePosition = goToFrame
            elif goToFrame > self.frameCount:
                self.currentFramePosition = self.frameCount
            elif goToFrame < 1:
                self.currentFramePosition = 1
        except ValueError:
            if navCommand == 'PPP':
                self.currentFramePosition -= 10
            elif navCommand == 'PP':
                self.currentFramePosition -= 5
            elif navCommand == 'P':
                self.currentFramePosition -= 1
            elif navCommand == 'N':
                self.currentFramePosition += 1
            elif navCommand == 'NN':
                self.currentFramePosition += 5
            elif navCommand == 'NNN':
                self.currentFramePosition += 10

            # If the frame position goes beyond max or min, cycle around.
            if self.currentFramePosition <= 0:
                self.currentFramePosition = self.frameCount + self.currentFramePosition
            elif self.currentFramePosition > self.frameCount:
                self.currentFramePosition = self.currentFramePosition - self.frameCount

    def getCurrentFrameAsBytes(self):
        """
        Return the byte representation of the current frame, based of self.currentFramePosition.

        Returns:
            frameAsBytes (bytes): Bytes representation of frame for displaying.
        """
        # Acquire current frame from stored location.
        frame = cv2.imread(self.path + '/' + self.frameNames[self.currentFramePosition - 1] + '.png')
        # Resize the frame for the display element.
        resizeFrame = ut.resizeFrame(frame, c.DEFAULT_DISPLAY_DIMENSIONS, ut.INTERPOLATION_AREA)
        # Add top offset line.
        cv2.line(resizeFrame, (0, int(self.recordingOffsetTop * c.DEFAULT_DISPLAY_DIMENSIONS[1])),
                 (c.DEFAULT_DISPLAY_DIMENSIONS[0], int(self.recordingOffsetTop * c.DEFAULT_DISPLAY_DIMENSIONS[1])),
                 color=(0, 0, 255), thickness=1)
        # Add bottom offset line.
        cv2.line(resizeFrame, (0, int(self.recordingOffsetBottom * c.DEFAULT_DISPLAY_DIMENSIONS[1])),
                 (c.DEFAULT_DISPLAY_DIMENSIONS[0], int(self.recordingOffsetBottom * c.DEFAULT_DISPLAY_DIMENSIONS[1])),
                 color=(0, 0, 255), thickness=1)
        # Add left offset line.
        cv2.line(resizeFrame, (int(self.recordingOffsetLeft * c.DEFAULT_DISPLAY_DIMENSIONS[0]), 0),
                 (int(self.recordingOffsetLeft * c.DEFAULT_DISPLAY_DIMENSIONS[0]), c.DEFAULT_DISPLAY_DIMENSIONS[0]),
                 color=(0, 0, 255), thickness=1)
        # Add right offset line.
        cv2.line(resizeFrame, (int(self.recordingOffsetRight * c.DEFAULT_DISPLAY_DIMENSIONS[0]), 0),
                 (int(self.recordingOffsetRight * c.DEFAULT_DISPLAY_DIMENSIONS[0]), c.DEFAULT_DISPLAY_DIMENSIONS[0]),
                 color=(0, 0, 255), thickness=1)
        # Add point data.
        for point in self.pointData:
            if point[0] == self.frameNames[self.currentFramePosition - 1]:
                cv2.circle(resizeFrame,
                           (int(point[1] * c.DEFAULT_DISPLAY_DIMENSIONS[0]),
                            int(point[2] * c.DEFAULT_DISPLAY_DIMENSIONS[1])), 5, color=(0, 255, 0), thickness=-1)
        # Convert resized frame to bytes.
        frameAsBytes = ut.frameToBytes(resizeFrame)

        return frameAsBytes

    def __getPointDataFromFile(self):
        """
        Helper function to get point data that has already been saved. If there is no file it is created. The
        frame name and coordinates of a point are stored on each line. The coordinates are stored as x-, and y-values
        that represent the location of the point as a percentage of the width and height of the signal dimensions.
        This makes it easier if the display dimensions are ever changed, but requires some conversion to go from
        percent of signal to pixel in display dimensions.
        """
        self.pointPath = ut.checkPointDataFile(self.path)

        with open(self.pointPath, 'r') as pointFile:
            for line in pointFile.readlines():
                lineSplit = line.split(',')
                self.pointData.append([lineSplit[0], float(lineSplit[1]), float(lineSplit[2])])

    def __getEditDetailsFromFile(self):
        """
        Helper function to get any editing details that are already stored. If there is no file it is created. Values
        stored in the file:
            recordingOffsetTop      -       The offset between the top of the frame and the start of the ultrasound
                                            image.
            recordingOffsetBottom   -       The offset between the bottom of the frame and the start of the ultrasound
                                            image.
        """
        self.editingPath = ut.checkEditDataFile(self.path)

        with open(self.editingPath, 'r') as editingFile:
            for line in editingFile.readlines():
                lineSplit = line.split(':')
                parameter = lineSplit[0]
                value = lineSplit[1]

                if parameter == 'recordingOffsetTop':
                    self.recordingOffsetTop = float(value)
                elif parameter == 'recordingOffsetBottom':
                    self.recordingOffsetBottom = float(value)
                elif parameter == 'recordingOffsetLeft':
                    self.recordingOffsetLeft = float(value)
                elif parameter == 'recordingOffsetRight':
                    self.recordingOffsetRight = float(value)

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
                self.depths.append(ut.getDepthFromRow(row))
            self.imuCount = len(self.frameNames)
            self.duration = ut.getTimeFromName(self.frameNames[-1]) - ut.getTimeFromName(self.frameNames[1])

            """
            Run some variable validation tests to ensure the numbers match. If they do not, display a warning.
            This wont stop the program running but it will indicate future problems that may occur.
            """
            # Check if the last frame number in the data.txt file matches the total number of rows.
            lastFrameNumber = int(row[0].split('-')[0])
            if lastFrameNumber != self.imuCount:
                print(f"!!! There is an inconsistency in the data.txt file."
                      f" The number of lines {self.imuCount} and the frame number {lastFrameNumber}"
                      f" do not match. !!!")
            # Check if the number of saved .png frames matches the number of rows.
            if self.frameCount != self.imuCount:
                print(f"!!! There is an inconsistency between the data.txt file and the number of saved frames in the "
                      f"video directory. The number of saved frames {self.frameCount} and the number of lines"
                      f" {self.imuCount} do not match. !!!")

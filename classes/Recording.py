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

CLEAR_FRAME = '-CLEAR-FRAME-'
CLEAR_ALL = '-CLEAR-ALL-'


class Recording:
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
            depths (list)               -       Scan depth of each frame.
            imuOffset (float)           -       Offset between IMU and end of probe.
            currentFrame (int)          -       Position of current frame of interest.
            fps (int)                   -       Estimated frame rate of the recording.
            editingPath (str)           -       Path to EditingData.txt file.
            offsetTop (float)           -       Top offset as faction of display dimensions.
            offsetBottom (float)        -       Bottom offset as faction of display dimensions.
            offsetLeft (float)          -       Left offset as faction of display dimensions.
            offsetRight (float)         -       Right offset as faction of display dimensions.
            pointPath (str)             -       Path to point data file.
            pointData (list)            -       Point data for points on frames.


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
        # IMU offset during scan.
        self.imuOffset = 0
        # Tracks position of current frame being displayed, starts at 1.
        self.currentFrame = 1

        self.__getImuDataFromFile()

        # Estimated fps of recording.
        self.fps = int(1000 * self.frameCount / self.duration)

        # Path to EditingData.txt file.
        self.editingPath = ''
        # Offsets between top, bottom, left, and right of frame and scan in fractions of display dimensions.
        self.offsetTop = 0
        self.offsetBottom = 0.999
        self.offsetLeft = 0
        self.offsetRight = 0.999
        # Path to PointData.txt.
        self.pointPath = ''
        # Point data of the frames.
        self.pointData = []
        # Path to BulletData.txt.
        self.bulletPath = ''
        # Point data for the bullet equation (LWHC).
        self.bulletData = []

        self.__getEditDetailsFromFile()
        self.__getPointDataFromFile()
        self.__getBulletDataFromFile()

    def addBulletPoint(self, position, point):
        """
        Add bullet point at specified position. Position ranges from 0 to 5 (6 points are required for the bullet
        equation).
        """
        widthRatio = point[0] / c.DISPLAY_DIMENSIONS[0]
        heightRatio = (c.DISPLAY_DIMENSIONS[1] - point[1]) / c.DISPLAY_DIMENSIONS[1]

        newPoint = [widthRatio, heightRatio]

        if len(self.bulletData) <= position:
            self.bulletData.append([self.frameNames[self.currentFrame - 1], newPoint[0], newPoint[1]])
        else:
            self.bulletData[position] = [self.frameNames[self.currentFrame - 1], newPoint[0], newPoint[1]]

        self.__saveDetailsToFile()

    def getCurrentFrameAsBytes(self):
        """
        Return the byte representation of the current frame, based of self.currentFramePosition.

        Returns:
            frameAsBytes (bytes): Bytes representation of frame for displaying.
        """
        # Acquire current frame from stored location.
        frame = cv2.imread(self.path + '/' + self.frameNames[self.currentFrame - 1] + '.png')
        # Resize the frame for the display element.
        resizeFrame = ut.resizeFrame(frame, c.DISPLAY_DIMENSIONS, ut.INTERPOLATION_AREA)
        # Add offset lines
        cv2.line(resizeFrame, (0, int(self.offsetTop * c.DISPLAY_DIMENSIONS[1])),
                 (c.DISPLAY_DIMENSIONS[0], int(self.offsetTop * c.DISPLAY_DIMENSIONS[1])),
                 color=(0, 0, 255), thickness=1)
        cv2.line(resizeFrame, (0, int(self.offsetBottom * c.DISPLAY_DIMENSIONS[1])),
                 (c.DISPLAY_DIMENSIONS[0], int(self.offsetBottom * c.DISPLAY_DIMENSIONS[1])),
                 color=(0, 0, 255), thickness=1)
        cv2.line(resizeFrame, (int(self.offsetLeft * c.DISPLAY_DIMENSIONS[0]), 0),
                 (int(self.offsetLeft * c.DISPLAY_DIMENSIONS[0]), c.DISPLAY_DIMENSIONS[0]),
                 color=(0, 0, 255), thickness=1)
        cv2.line(resizeFrame, (int(self.offsetRight * c.DISPLAY_DIMENSIONS[0]), 0),
                 (int(self.offsetRight * c.DISPLAY_DIMENSIONS[0]), c.DISPLAY_DIMENSIONS[0]),
                 color=(0, 0, 255), thickness=1)
        # Add point data.
        for point in self.pointData:
            if point[0] == self.frameNames[self.currentFrame - 1]:
                cv2.circle(resizeFrame,
                           (int(point[1] * c.DISPLAY_DIMENSIONS[0]),
                            int(point[2] * c.DISPLAY_DIMENSIONS[1])), 5, color=(0, 255, 0), thickness=-1)
        # Add bullet data.
        for point in self.bulletData:
            if point[0] == self.frameNames[self.currentFrame - 1]:
                cv2.circle(resizeFrame,
                           (int(point[1] * c.DISPLAY_DIMENSIONS[0]),
                            int(point[2] * c.DISPLAY_DIMENSIONS[1])), 5, color=(255, 249, 125), thickness=-1)

        # Convert resized frame to bytes.
        frameAsBytes = ut.frameToBytes(resizeFrame)

        return frameAsBytes

    def getFrameAngles(self) -> list:
        """
        Return the Euler angles of the current frame.
        """
        euler = ut.quaternionToEuler(self.quaternion[self.currentFrame - 1])

        return euler

    def clearAllPoints(self):
        """
        Clear all points on all frames.
        """
        self.pointData = []

        self.__saveDetailsToFile()

    def clearFramePoints(self):
        """
        Clear points on the currently displayed frame.
        """
        self.pointData = [point for point in self.pointData if not point[0] == self.frameNames[self.currentFrame - 1]]

        self.__saveDetailsToFile()

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
                (self.offsetBottom - self.offsetTop))
            # Width ratio used to go from pixel ratio to mm for width.
            widthRatio = self.depths[position] / (
                (self.offsetRight - self.offsetLeft))
            # Extract point from line.
            point = [
                [(row[1] - self.offsetLeft) * widthRatio - self.depths[position] / 2,
                 (row[2] - self.offsetTop) * depthRatio + self.imuOffset, 0]]

            axis = ut.plotPointOnAxis(axis, quaternion, point, pointPlot)

        return axis

    def __saveDetailsToFile(self):
        """
        Save all in memory data to relevant .txt files. This should be called whenever a value is changed. All previous
        values are overwritten and the current values stored.
        """
        try:
            with open(self.editingPath, 'w') as editingFile:
                editingFile.write(f'recordingOffsetTop:{self.offsetTop}\n')
                editingFile.write(f'recordingOffsetBottom:{self.offsetBottom}\n')
                editingFile.write(f'recordingOffsetLeft:{self.offsetLeft}\n')
                editingFile.write(f'recordingOffsetRight:{self.offsetRight}\n')
                editingFile.write(f'imuOffset:{self.imuOffset}\n')

            with open(self.pointPath, 'w') as pointFile:
                for point in self.pointData:
                    pointFile.write(f'{point[0]},{point[1]},{point[2]}\n')

            with open(self.bulletPath, 'w') as bulletFile:
                for point in self.bulletData:
                    bulletFile.write(f'{point[0]},{point[1]},{point[2]}\n')
            # todo Should probably move this to its own function, this is quite a lot of writing
            if self.imuCount == self.frameCount:
                with open(self.path + '/data.txt', 'w') as dataFile:
                    for i in range(self.imuCount):
                        dataFile.write(f'{self.frameNames[i]},:'
                                       f'acc[,{self.acceleration[i][0]},{self.acceleration[i][1]},'
                                       f'{self.acceleration[i][2]},]'
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
        widthRatio = point[0] / c.DISPLAY_DIMENSIONS[0]
        heightRatio = (c.DISPLAY_DIMENSIONS[1] - point[1]) / c.DISPLAY_DIMENSIONS[1]

        newPoint = [widthRatio, heightRatio]

        # Check if within radius, if NOT, add point, else remove a point.
        if not self.__checkIfWithinRadiusOfOtherPoints(newPoint):
            self.pointData.append([self.frameNames[self.currentFrame - 1], newPoint[0], newPoint[1]])

        self.__saveDetailsToFile()

    def __checkIfWithinRadiusOfOtherPoints(self, point: [float, float]) -> bool:
        """
        Check if the given point is with the constant radius of any other points that are already present. This is
        done per frame basis, so the frame names must also be checked. If it is within an already saved points radius,
        remove the saved point and leave the function. This means only one point can be removed at a time and points
        will be removed until there are no already saved points within range of the point that is to be newly added.

        Args:
            point [float, float]: New point to be tested against already saved points.

        Returns:
            withinRadius (bool): True if any point was within the radius, else False.
        """
        withinRadius = False

        for centrePoint in self.pointData:
            if self.frameNames[self.currentFrame - 1] == centrePoint[0] and ut.pointWithinRadius(
                    [centrePoint[1], centrePoint[2]], point):
                self.pointData.remove(centrePoint)
                withinRadius = True
                break
        return withinRadius

    def changeScanDepth(self, newScanDepth: str):
        """
        Change the scan depth of the current frame that is being edited. The scan depth can be a float and is
        read from the screen of the ultrasound image. This is manual for now, but perhaps that can be automated
        at some point.

        Args:
            newScanDepth (str): Depth of the ultrasound scan as read from the signal display.
        """
        try:
            newScanDepth = float(newScanDepth)
            self.depths[self.currentFrame - 1] = newScanDepth
            self.__saveDetailsToFile()
        except Exception as e:
            print(f'Error updating scan depth, ensure a float was entered: {e}.')

    def changeAllScanDepths(self, newScanDepth: str):
        """
        Change the scan depth of all the frames in the recording, then save the details to file.

        Args:
            newScanDepth (str): Depth of the ultrasound scan as read from the signal display.
        """
        try:
            newScanDepth = float(newScanDepth)
            self.depths = [newScanDepth for _ in self.depths]
            self.__saveDetailsToFile()
        except Exception as e:
            print(f'Error updating all scan depths at once: {e}.')

    def changeImuOffset(self, newIMuOffset: str):
        """
        Change the offset of the imu from the end of the probe, then save the details to file. This value will have an
        effect on the volume calculations.
        Args:
            newIMuOffset (str): Offset between the IMU and the start of the scan.
        """
        try:
            newIMuOffset = float(newIMuOffset)
            self.imuOffset = newIMuOffset
            self.__saveDetailsToFile()
        except Exception as e:
            print(f'Error updating the imu offset: {e}.')

    def changeOffsetTop(self, newOffset: int):
        """
        Change the top frame offset of the recording. If it is found that the offset can change,
        this will have to be changed to per frame basis.

        Args:
            newOffset (int): Offset between the top of the frame and the start of the scan as a ratio.
        """
        try:
            newOffset = float(newOffset)
            self.offsetTop = newOffset
            self.__saveDetailsToFile()
        except Exception as e:
            print(f'Error updating top offset, ensure that an integer was entered: {e}.')

    def changeOffsetBottom(self, newOffset: int):
        """
        Change the bottom frame offset of the recording. If it is found that the offset can change,
        this will have to be changed to per frame basis.

        Args:
            newOffset (int): Offset between the bottom of the frame and the end of the scan as a ratio.
        """
        try:
            newOffset = float(newOffset)
            self.offsetBottom = newOffset
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
            self.offsetLeft = newOffset
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
            self.offsetRight = newOffset
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
                self.currentFrame = goToFrame
            elif goToFrame > self.frameCount:
                self.currentFrame = self.frameCount
            elif goToFrame < 1:
                self.currentFrame = 1

        except ValueError:
            if navCommand == 'PPP':
                self.currentFrame -= 10
            elif navCommand == 'PP':
                self.currentFrame -= 5
            elif navCommand == 'P':
                self.currentFrame -= 1
            elif navCommand == 'N':
                self.currentFrame += 1
            elif navCommand == 'NN':
                self.currentFrame += 5
            elif navCommand == 'NNN':
                self.currentFrame += 10

            # If the frame position goes beyond max or min, cycle around.
            if self.currentFrame <= 0:
                self.currentFrame = self.frameCount + self.currentFrame
            elif self.currentFrame > self.frameCount:
                self.currentFrame = self.currentFrame - self.frameCount

    def __getBulletDataFromFile(self):
        """
        Helper function to get bullet data that has already been saved. If there is no file it is created. The frame
        name and coordinates of 6 points are stored. The coordinates are stored as x-, and y-values that represent
        the location of the points as ratios pf the width and height of the display dimensions.
        """
        self.bulletPath = ut.checkBulletDataFile(self.path)

        with open(self.bulletPath, 'r') as bulletFile:
            for line in bulletFile.readlines():
                lineSplit = line.split(',')
                self.bulletData.append([lineSplit[0], float(lineSplit[1]), float(lineSplit[2])])

    def __getPointDataFromFile(self):
        """
        Helper function to get point data that has already been saved. If there is no file it is created. The
        frame name and coordinates of a point are stored on each line. The coordinates are stored as x-, and y-values
        that represent the location of the point as a ratio of the width and height of the display dimensions.
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
                    self.offsetTop = float(value)
                elif parameter == 'recordingOffsetBottom':
                    self.offsetBottom = float(value)
                elif parameter == 'recordingOffsetLeft':
                    self.offsetLeft = float(value)
                elif parameter == 'recordingOffsetRight':
                    self.offsetRight = float(value)
                elif parameter == 'imuOffset':
                    self.imuOffset = float(value)

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
            self.duration = ut.getTimeFromName(self.frameNames[-1]) - ut.getTimeFromName(self.frameNames[0])
            if self.duration == 0:
                self.duration = 1
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

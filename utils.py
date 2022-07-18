"""
Helper script containing functions used throughout ultrasound_data_capture module.
"""
from pathlib import Path

import cv2
import numpy as np
from datetime import datetime as dt
from cv2.gapi.wip.draw import Image
from pyquaternion import Quaternion
import constants as c
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import PySimpleGUI as sg
import subprocess

INTERPOLATION_NEAREST = cv2.INTER_NEAREST
INTERPOLATION_AREA = cv2.INTER_AREA


def createInitialDirectories() -> (Path, Path):
    """
    Create the initial directories needed for file storage, if they do not already exist. The two directories needed
    are the Generated/SingleFrames directory and the Generated/Videos directory, for storing snapshots and
    subdirectories containing video recordings, respectively. The Generated/Videos subdirectories are generated as
    they are needed.

    Returns:
        singleFramesPath (Path): Path of the SingleFrames directory.
        videosPath (Path): Path of the Videos directory.
    """
    currentWorkingDirectory = Path.cwd()

    singleFramesPath = Path(currentWorkingDirectory, 'Generated/SingleFrames')
    singleFramesPath.mkdir(parents=True, exist_ok=True)

    videosPath = Path(currentWorkingDirectory, 'Generated/Videos')
    videosPath.mkdir(parents=True, exist_ok=True)

    return singleFramesPath, videosPath


def getRecordingDirs(videosPath: Path) -> list:
    """
    Return a list of all the stored recording directories in the Generated/Videos directory. This list is used
    in a COMBO element when editing so the user can select which folder they want to edit/browse the frames of.

    Args:
        videosPath (Path): Path to directory containing all video directories.

    Returns:
        recordedVideos (list): List of recorded videos directories as strings.
    """
    videoDirectories = [vd.stem for vd in videosPath.iterdir() if vd.is_dir()]

    return videoDirectories


def checkBulletDataFile(recordingPath: str):
    """
    Check if the given directory contains a BulletData.txt file, if True return a Path object to it, else create
    the file and return a Path object to it.

    Args:
        recordingPath (Path): Path to a recording directory.

    Returns:
        editFileDir (Path): Path object to existing or newly created EditingData.txt file.
    """
    bulletFileDir = Path(recordingPath, 'BulletData.txt')
    if not bulletFileDir.is_file():
        with open(bulletFileDir, 'a'):
            pass

    return bulletFileDir


def checkEditDataFile(recordingPath: str) -> Path:
    """
    Check if the given directory contains an EditingData.txt file, if True return a Path object to it, else create
    the file and return a Path object to it. When creating the file add some default values to it. These default
    values align with the offsets of the Canon Aplio i700 with a scan depth of 150mm.

    Args:
        recordingPath (Path): Path to a recording directory.

    Returns:
        editFileDir (Path): Path object to existing or newly created EditingData.txt file.
    """
    editFileDir = Path(recordingPath, 'EditingData.txt')
    if not editFileDir.is_file():
        with open(editFileDir, 'a') as editingFile:
            editingFile.write('recordingOffsetTop:0.21180555555555555\n')
            editingFile.write(f'recordingOffsetBottom:0.8125\n')
            editingFile.write(f'recordingOffsetLeft:0.248046875\n')
            editingFile.write(f'recordingOffsetRight:0.6982421875\n')

    return editFileDir


def checkPointDataFile(recordingPath: str) -> Path:
    """
        Check if the given directory contains an PointData.txt file, if True return a Path object to it, else create
        the file and return a Path object to it.

        Args:
            recordingPath (Path): Path to a recording directory.

        Returns:
            pointFileDir (Path): Path object to existing or newly created PointData.txt file.
        """
    pointFileDir = Path(recordingPath, 'PointData.txt')
    if not pointFileDir.is_file():
        with open(pointFileDir, 'a'):
            pass

    return pointFileDir


def getFrameCountInDirectory(videoPath: Path) -> int:
    """
    Return the total number of saved frames in a directory. Frames are saved as .png images within a video directory.

    Args:
        videoPath (Path): Path to video directory where frames are stored.

    Returns:
        frameCount (int): Number of frames in directory.
    """
    frameCount = len([vd for vd in videoPath.glob('*.png')])

    return frameCount


def rotatePoints(points: list, quaternion: list) -> np.array:
    """
    Rotate the list of points [[x1, y1, z1], [x2, y2, z2], ...] using the given quaternion (given as 4D vector). First
    the given quaternion parameter is converted into a Quaternion object (from a 4D list). Then the points are rotated
    using the Quaternion.rotate() method of the Quaternion class. The result is returned as a numpy array.

    Args:
        points (list([x, y, z])): List of 3D vector points to be rotated.
        quaternion (list([q0, q1, q2, q3])): 4D vector representing a quaternion.

    Returns:
        rotatedPoints (np.array): A Numpy Array of rotated points
    """
    rotated_points = []
    myQuaternion = Quaternion(quaternion)
    for point in points:
        rotated_points.append(myQuaternion.rotate(point))

    return np.array(rotated_points)


def plotPointOnAxis(axis, quaternion, point, pointPlot):
    """
    Plot the given point on the given axis. The point is rotated according to its related quaternions.

    Args:
        axis (axis): Axis on to which the point must be plotted.
        quaternion (list): List of quaternion values.
        point (list):  List of point coordinates to be rotated then plot.
        pointPlot (axis.plot): Used by the artist to draw points.

    Returns:
        axis (axis): Axis containing newly plotted point.
    """
    rpp = rotatePoints(point, quaternion)[0]

    pointPlot.set_data([rpp[0]], [rpp[1]])
    pointPlot.set_3d_properties([rpp[2]])
    axis.draw_artist(pointPlot)

    return axis


def plotOrientationOnAxis(axis, quaternion, pointPlot, lineData):
    """
    Plot the orientation points on the given axis once they have been rotated by the given Quaternion. The returned
    axis is then blit on to the figure for increased plotting speed. The pointData and lineData parameters
    must be instantiated once in the parent class, otherwise a memory leak occurs.

    Args:
        axis (axis): Axis on to which the points and lines must be plotted.
        quaternion (list(q0, q1, q2, q3)): 4D vector representing a quaternion.
        lineData (axis.plot): Plot used for the lines.
        pointPlot (axis.plot): Plot used for the points.

    Returns:
        axis (axis): Axis containing newly plotted points and lines.
    """
    rpp = rotatePoints(c.PROBE_POINTS, quaternion)
    # Draw points
    for point in rpp:
        pointPlot.set_data([point[0]], [point[1]])
        pointPlot.set_3d_properties([point[2]])
        axis.draw_artist(pointPlot)

    # Draw lines between points
    for i, point in enumerate(rpp):
        if not i < len(rpp) - 1:
            next_point = rpp[0, :]
            lineData.set_data([next_point[0], point[0]],
                              [next_point[1], point[1]])
            lineData.set_3d_properties([next_point[2], point[2]])
        else:
            next_point = rpp[i + 1, :]
            lineData.set_data([next_point[0], point[0]],
                              [next_point[1], point[1]])
            lineData.set_3d_properties([next_point[2], point[2]])
        axis.draw_artist(lineData)

    return axis


def initialiseAxis(axis, azimuth, limits=(-5, 5)):
    """
    Set the initial labels, limits, and azimuth of the given axis.

    Args:
        limits:
        axis (axis): Axis that will have its labels, limits, and azimuth set.
        azimuth (int): Azimuth value applied to the axis.

    Returns:
        axis (axis): Axis containing newly plotted points and lines.
    """
    axis.set_xlim(limits)
    axis.set_ylim(limits)
    axis.set_zlim(limits)

    axis.set_xticklabels([])
    axis.set_yticklabels([])
    axis.set_zticklabels([])

    axis.set_facecolor(sg.DEFAULT_BACKGROUND_COLOR)

    axis.azim = azimuth

    return axis


def initialiseEditingAxis(axis, azimuth, scanDepth):
    """
    Set the initial labels, limits, and azimuth of the given axis.

    Args:
        axis (axis): Axis that will have its labels, limits, and azimuth set.
        azimuth (int): Azimuth value applied to the axis.
        scanDepth (float): Scan depth in mm.

    Returns:
        axis (axis): Axis containing newly plotted points and lines.
    """
    axis.set_xlim(-scanDepth, scanDepth)
    axis.set_ylim(-scanDepth, scanDepth)
    axis.set_zlim(-scanDepth, scanDepth)

    axis.set_xlabel('X')
    axis.set_ylabel('Y')
    axis.set_zlabel('Z')

    axis.set_facecolor(sg.DEFAULT_BACKGROUND_COLOR)

    axis.azim = azimuth

    return axis


def drawFigure(figure, canvas):
    """
    Helper function for integrating matplotlib plots with PySimpleGui. Used to draw the initial canvas.

    Args:
        figure (figure): Figure to be placed in a canvas.
        canvas (TKCanvas): Canvas that the figure is placed in.

    Returns:
        figure_canvas_agg (FigureCanvasTkAgg): A FigureCanvasTkAgg object.
    """

    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg


def quaternionToEuler(quaternion: list):
    """
    Convert the given quaternion to Euler angels (yaw, pitch, and roll).

    Args:
        quaternion (list): Quaternion values.

    Returns:
    `   euler (list): Euler angles of the given quaternion.
    """
    quat = Quaternion(quaternion)

    euler = np.array(quat.yaw_pitch_roll)

    euler = euler * 180 / np.pi

    return euler


def resizeFrame(frame, newDimensions, interpolation) -> Image:
    """
    Resize the given frame to the given dimensions. This is used to make the returned frame fit in the display box, and
    may result in some distortion if the video signal does not match the DEFAULT_DISPLAY_DIMENSIONS' aspect ratio.
    The interpolation method used is cv2.INTER_NEAREST, which preliminary tests show to be the fastest.

    Args:
        frame (Image): A CV2 image.
        newDimensions (int, int): A tuple representing the required width and height.
        interpolation (const): Type of interpolation to use.

    Returns:
        resizedFrame (Image): A resized CV2 image.

    """
    resizedFrame = cv2.resize(frame, newDimensions, interpolation=interpolation)
    return resizedFrame


def frameToBytes(frame) -> bytes:
    """
    Converts a frame (CV2 image) into a byte array for displaying in PySimpleGUI's Image element.

    Args:
        frame (Image): A CV2 image.

    Returns:
        byteFrame (bytes): frame converted into bytes.
    """
    byteFrame = cv2.imencode(".png", frame)[1].tobytes()
    return byteFrame


def pngAsBytes(pngPath: str) -> bytes:
    """
    Converts the .png file at the specified path to bytes, used to be displayed as a frame.

    Args:
        pngPath (str): Local path to .png file.

    Returns:
        pngBytes (bytes): .png file converted to bytes.
    """
    # Convert local path to full path.
    pngPath = Path(Path.cwd(), pngPath)
    # Read image using openCV
    img = cv2.imread(str(pngPath))
    # Convert image to bytes
    pngBytes = frameToBytes(img)

    return pngBytes


def saveSingleFrame(frame, framePath):
    """
    Save a single frame to the specified path. The path must include the intended name of the frame, not just the
    directory.

    Args:
        frame (Image): A CV2 image.
        framePath (str): Path to where the frame should be saved, including file name and extension.
    """
    try:
        cv2.imwrite(framePath, frame)
    except Exception as e:
        print(f'Error saving frame to {framePath}: {e}')


def createRecordingDirectory(videosPath) -> tuple[Path, str]:
    """
    Create a directory where a recording of frames will be saved. Based on the time the test/recording was started.

    Args:
        videosPath (str): Path to the parent Videos directory where all recordings are saved.

    Returns:
        tuple(Path, str): The Path to the current recording directory and its related data.txt file.

    """
    # Create the new recording directory.
    currentRecordingPath = Path(videosPath, dt.now().strftime("%d %m %Y %H-%M-%S,%f")[:-3])
    currentRecordingPath.mkdir(parents=True, exist_ok=True)
    # Return a path to the new directory's data.txt file for IMU data recording.
    dataFilePath = str(Path(currentRecordingPath, 'data.txt'))

    return currentRecordingPath, dataFilePath


def createBatteryTestDirectory() -> Path:
    """
    Create a directory for storing IMU data files created during battery tests. If the directory already exists, return
    a path to it.

    Returns:
        batteryTestPath (Path): Path object to the newly created directory.

    """
    # Create the directory for storing battery test IMU files.
    batteryTestPath = Path(Path.cwd(), 'BatteryTests')
    batteryTestPath.mkdir(parents=True, exist_ok=True)
    print(f'BatteryTests directory created: {batteryTestPath.absolute()}')
    # Return a path to the created directory.
    return batteryTestPath


def getTimeFromName(frameName: str) -> int:
    """
    Extract time from the frame name. The frame name is composed as such: (frame number)-(time).(png).

    Args:
        frameName (str): Name of the frame as a string.

    Returns:
        timeAsInt (int): Time as an integer.
    """
    timeAsInt = int(frameName.split('-')[1].split('.')[0])
    return timeAsInt


def getAccelerationFromRow(row: list) -> list:
    """
    Extract the acceleration from a row. The third, fourth, and fifth elements in the row.

    Args:
        row (str): Pulled from csv.reader.

    Returns:
        acceleration (list): List of the three acceleration values in the x, y, and z directions.
    """
    acceleration = [float(row[2]), float(row[3]), float(row[4])]
    return acceleration


def getQuaternionFromRow(row: list) -> list:
    """
    Extract the quaternion from a row. The 7, 8, 9, and 10 elements in the row.

    Args:
        row (str): Pulled from csv.reader.

    Returns:
        quaternion (list): List of the 4 quaternion values.
    """
    quaternion = [float(row[6]), float(row[7]), float(row[8]), float(row[9])]
    return quaternion


def getDimensionsFromRow(row: list) -> list:
    """
    Extract the dimensions from a row. The 12, and 13 elements in the row.

    Args:
        row (str): Pulled from csv.reader.

    Returns:
        dimensions (list): List of the width and height dimensions.
    """
    dimensions = [float(row[11]), float(row[12])]
    return dimensions


def getDepthFromRow(row: list) -> float:
    """
    Extract the recording/scan depth from a row. The 15 element in the row. The default value is 150 (mm), and if the
    value needs to be changed it can only be done on a per-frame basis for now.

    Args:
        row (str): Pulled from csv.reader.

    Returns:
        depth (float): Depth of the scan.
    """
    depth = float(row[14])
    return depth


def openWindowsExplorer(explorerPath: str):
    """
    Opens Windows explorer at the given string path. The path must be enclosed in double quotes to handle the whitespaces
    in the folder name.

    Args:
        explorerPath (str): String path to open.
    """
    path = explorerPath.replace('/', '\\')
    print(f'Attempting to open Windows explorer: {path}.')
    try:
        subprocess.Popen(f'explorer "{path}"')
    except Exception as e:
        print(f'Error opening Windows explorer: {e}')


def pointWithinRadius(centrePoint: (float, float), testPoint: (float, float)) -> bool:
    """
    Checks whether the testPoint is within the constant radius of the centrePoint, if it is return True, else False.

    Args:
        centrePoint (float, float): Location of centre point, as a percentage.
        testPoint (float, float): Location of test point, as a percentage.

    Returns:
        withinRadius (bool): True if within radius, else False.
    """
    withinRadius = False

    if (testPoint[0] - centrePoint[0]) ** 2 + (testPoint[1] - centrePoint[1]) ** 2 < c.DEFAULT_POINT_RADIUS ** 2:
        withinRadius = True

    return withinRadius

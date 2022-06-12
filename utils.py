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


def rotatePoints(points, quaternion):
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


def plotPointsOnAxis(axis, quaternion, pointData, lineData):
    """
    Plot the orientation points on the given axis once they have been rotated by the given Quaternion. The returned
    axis is then blit on to the figure for increased plotting speed. The pointData and lineData parameters
    must be instantiated once in the parent class, otherwise a memory leak occurs.

    Args:
        axis (axis): Axis on to which the points and lines must be plotted.
        quaternion (list(q0, q1, q2, q3)): 4D vector representing a quaternion.
        lineData (axis.plot): Plot used for the lines.
        pointData (axis.plot): Plot used for the points.

    Returns:
        axis (axis): Axis containing newly plotted points and lines.
    """
    rpp = rotatePoints(c.PROBE_POINTS, quaternion)
    # Draw points
    for point in rpp:
        pointData.set_data([point[0]], [point[1]])
        pointData.set_3d_properties([point[2]])
        axis.draw_artist(pointData)

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


def initialiseAxis(axis, azimuth):
    """
    Set the initial labels, limits, and azimuth of the given axis.

    Args:
        axis (axis): Axis that will have its labels, limits, and azimuth set.
        azimuth (int): Azimuth value applied to the axis.

    Returns:
        axis (axis): Axis containing newly plotted points and lines.
    """
    axis.set_xlabel('X')
    axis.set_ylabel('Y')
    axis.set_zlabel('Z')
    axis.set_xlim((-5, 5))
    axis.set_ylim((-5, 5))
    axis.set_zlim((-5, 5))

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


def resizeFrame(frame, newDimensions) -> Image:
    """
    Resize the given frame to the given dimensions. This is used to make the returned frame fit in the display box, and
    may result in some distortion if the video signal does not match the DEFAULT_DISPLAY_DIMENSIONS' aspect ratio.

    Args:
        frame (Image): A CV2 image.
        newDimensions (int, int): A tuple representing the required width and height.

    Returns:
        resizedFrame (Image): A resized CV2 image.

    """

    resizedFrame = cv2.resize(frame, newDimensions)
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
    currentRecordingPath = Path(videosPath, dt.now().strftime("%d-%m-%Y-%H-%M-%S.%f")[:-3])
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

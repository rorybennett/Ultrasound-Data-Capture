from pathlib import Path
import numpy as np
from pyquaternion import Quaternion
import constants as c


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
        quaternion (list(q0, q1, q2, q3)): 4D vector representing a quaternion.

    Returns:
        rotatedPoints (np.array): A Numpy Array of rotated points
    """
    rotated_points = []
    myQuaternion = Quaternion(quaternion)
    for point in points:
        rotated_points.append(myQuaternion.rotate(point))

    return np.array(rotated_points)


def plotPointsOnAxis(axis, quaternion):
    """
    Plot the orientation points on the given axis once they have been rotated by the given quaternion. The returned
    axis is then blitted on to the figure for increased plotting speed.

    Args:
        axis:
        quaternion:

    Returns:

    """
    rpp = rotatePoints(c.PROBE_POINTS, quaternion)
    pointData = axis.plot([], [], [], color="red", linestyle="none", marker="o", animated=True)[0]
    lineData = axis.plot([], [], [], color="red", animated=True)[0]
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
    axis.set_xlabel('X')
    axis.set_ylabel('Y')
    axis.set_zlabel('Z')
    axis.set_xlim((-5, 5))
    axis.set_ylim((-5, 5))
    axis.set_zlim((-5, 5))

    axis.azim = int(azimuth)

    return axis

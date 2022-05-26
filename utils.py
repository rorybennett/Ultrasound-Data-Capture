from pathlib import Path
import numpy as np
from pyquaternion import Quaternion


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

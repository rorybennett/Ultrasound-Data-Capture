"""
Helper script containing functions used throughout ultrasound_data_capture module.
"""
from datetime import datetime as dt
from pathlib import Path

import PySimpleGUI as Psg
import cv2
import numpy as np
from PIL.Image import Image
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pyquaternion import Quaternion

import constants as c

INTERPOLATION_NEAREST = cv2.INTER_NEAREST
INTERPOLATION_AREA = cv2.INTER_AREA


def create_initial_directories() -> (Path, Path):
    """
    Create the initial directories needed for file storage, if they do not already exist. The two directories needed
    are the Generated/SingleFrames directory and the Generated/Videos directory, for storing snapshots and
    subdirectories containing video recordings, respectively. The Generated/Videos subdirectories are generated as
    they are needed.

    Returns:
        single_frames_path (Path): Path of the SingleFrames directory.
        videos_path (Path): Path of the Videos directory.
    """
    current_working_directory = Path.cwd().parent

    single_frames_path = Path(current_working_directory, 'Generated/SingleFrames')
    single_frames_path.mkdir(parents=True, exist_ok=True)

    videos_path = Path(current_working_directory, 'Generated/Videos')
    videos_path.mkdir(parents=True, exist_ok=True)

    return single_frames_path, videos_path


def rotate_points(points: list, quaternion: list) -> np.array:
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
    my_quaternion = Quaternion(quaternion)
    for point in points:
        rotated_points.append(my_quaternion.rotate(point))

    return np.array(rotated_points)


def plot_orientation_on_axis(axis, quaternion, point_plot, line_data):
    """
    Plot the orientation points on the given axis once they have been rotated by the given Quaternion. The returned
    axis is then blit on to the figure for increased plotting speed. The pointData and lineData parameters
    must be instantiated once in the parent class, otherwise a memory leak occurs.

    Args:
        axis (axis): Axis on to which the points and lines must be plotted.
        quaternion (list(q0, q1, q2, q3)): 4D vector representing a quaternion.
        line_data (axis.plot): Plot used for the lines.
        point_plot (axis.plot): Plot used for the points.

    Returns:
        axis (axis): Axis containing newly plotted points and lines.
    """
    rpp = rotate_points(c.PROBE_POINTS, quaternion)
    # Draw points
    for point in rpp:
        point_plot.set_data([point[0]], [point[1]])
        point_plot.set_3d_properties([point[2]])
        axis.draw_artist(point_plot)

    # Draw lines between points
    for i, point in enumerate(rpp):
        if not i < len(rpp) - 1:
            next_point = rpp[0, :]
            line_data.set_data([next_point[0], point[0]],
                               [next_point[1], point[1]])
            line_data.set_3d_properties([next_point[2], point[2]])
        else:
            next_point = rpp[i + 1, :]
            line_data.set_data([next_point[0], point[0]],
                               [next_point[1], point[1]])
            line_data.set_3d_properties([next_point[2], point[2]])
        axis.draw_artist(line_data)

    return axis


def initialise_axis(axis, azimuth, limits=(-5, 5)):
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

    axis.set_facecolor(Psg.DEFAULT_BACKGROUND_COLOR)

    axis.azim = azimuth

    return axis


def draw_figure(figure, canvas):
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


def resize_frame(frame, new_dimensions, interpolation) -> Image:
    """
    Resize the given frame to the given dimensions. This is used to make the returned frame fit in the display box, and
    may result in some distortion if the video signal does not match the DEFAULT_DISPLAY_DIMENSIONS' aspect ratio.
    The interpolation method used is cv2.INTER_NEAREST, which preliminary tests show to be the fastest.

    Args:
        frame (Image): A CV2 image.
        new_dimensions (int, int): A tuple representing the required width and height.
        interpolation (const): Type of interpolation to use.

    Returns:
        resized_frame (Image): A resized CV2 image.

    """
    resized_frame = cv2.resize(frame, new_dimensions, interpolation=interpolation)
    return resized_frame


def frame_to_bytes(frame) -> bytes:
    """
    Converts a frame (CV2 image) into a byte array for displaying in PySimpleGUI's Image element.

    Args:
        frame (Image): A CV2 image.

    Returns:
        byte_frame (bytes): frame converted into bytes.
    """
    byte_frame = cv2.imencode(".png", frame)[1].tobytes()
    return byte_frame


def save_single_frame(frame, frame_path):
    """
    Save a single frame to the specified path. The path must include the intended name of the frame, not just the
    directory.

    Args:
        frame (Image): A CV2 image.
        frame_path (str): Path to where the frame should be saved, including file name and extension.
    """
    try:
        cv2.imwrite(frame_path, frame)
    except Exception as e:
        print(f'Error saving frame to {frame_path}: {e}')


def create_recording_directory(videos_path, patient_number, scan_plane) -> tuple[Path, str]:
    """
    Create a directory where a recording of frames will be saved. Based on the time the test/recording was started and
    extra parameters entered.

    Args:
        videos_path (str): Path to the parent Videos directory where all recordings are saved.
        patient_number (str): Patient scan identifier.
        scan_plane (str): Scan plane identifier, from radio buttons.

    Returns:
        tuple(Path, str): The Path to the current recording directory and its related data.txt file.

    """
    # Create the new recording directory.
    if not patient_number.strip():
        patient_number = dt.now().strftime("%d %m %Y %H-%M-%S,%f")[:-3]

    path = videos_path + '/' + patient_number + '/' + scan_plane
    current_recording_path = Path(path, dt.now().strftime("%d %m %Y %H-%M-%S,%f")[:-3])
    current_recording_path.mkdir(parents=True, exist_ok=True)
    # Return a path to the new directory's data.txt file for IMU data recording.
    data_file_path = str(Path(current_recording_path, 'data.txt'))

    return current_recording_path, data_file_path


def create_battery_test_directory() -> Path:
    """
    Create a directory for storing IMU data files created during battery tests. If the directory already exists, return
    a path to it.

    Returns:
        battery_test_path (Path): Path object to the newly created directory.

    """
    # Create the directory for storing battery test IMU files.
    battery_test_path = Path(Path.cwd(), 'BatteryTests')
    battery_test_path.mkdir(parents=True, exist_ok=True)
    print(f'BatteryTests directory created: {battery_test_path.absolute()}')
    # Return a path to the created directory.
    return battery_test_path

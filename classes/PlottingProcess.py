"""
Class for handling plotting the orientation of the probe.

Plotting is removed from the main process as it slows the main process down significantly.

A custom multiprocessing.manager class is created to enable a LIFO queue approach.
"""
import multiprocessing
import queue
from multiprocessing.managers import BaseManager
from queue import LifoQueue

import PySimpleGUI as Psg
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from pyquaternion import Quaternion

import constants as c
from classes import Layout


def rotate_points(points: list, quaternion: list) -> np.array:
    """
    Rotate the list of points by the given quaternion.

    Args:
        points (list): List of (x, y, z) coordinates to be rotated.
        quaternion (list): List of quaternion values.

    Returns:
        rotated_points (np.array): List of rotated points as a numpy array.
    """
    rotated_points = []
    my_quaternion = Quaternion(quaternion)
    for point in points:
        rotated_points.append(my_quaternion.rotate(point))

    rotated_points = np.array(rotated_points)

    return rotated_points


class MyManager(BaseManager):
    """
    Custom class used to register LifoQueue to the multiprocessing manager class.
    """
    pass


MyManager.register('LifoQueue', LifoQueue)


class PlottingProcess:
    def __init__(self, window):
        """
        Initialise a plotting_process object.

        Args:
            window (sg.Window): PySimpleGUI object that is needed to acquire screen dimensions.
        """
        self.screenDimensions = window.get_screen_dimensions()
        self.plottingAsyncProcess = None
        self.manager = MyManager()
        self.manager.start()
        self.plottingQueue = None
        self.pool = None

    def start_plotting(self):
        """
        Create the queue object, processing pool, and start the plotting_process running in the process pool.
        """
        self.plottingQueue = self.manager.LifoQueue()
        self.pool = multiprocessing.Pool(1)
        self.plottingAsyncProcess = self.pool.apply_async(plotting_process,
                                                          args=(self.plottingQueue, self.screenDimensions))

    def plot_orientation(self, quaternion):
        """
        Add a quaternion to the queue to be plotted when the plotting process is ready.

        Args:
            quaternion (list): Quaternion constants received from the IMU.
        """
        self.plottingQueue.put(quaternion)

    def end_plotting(self):
        """
        Close and join the plotting_process. First the while loop in the plotting_process method is broken, then the
        plottingQueue is deleted (helps with memory release), and the process pool is closed and joined.
        """
        self.plottingQueue.put('-END-PROCESS-')
        del self.plottingQueue
        self.pool.close()
        self.pool.join()


def plotting_process(lifo_queue, screen_dimensions):
    """
    Method to be run in an async_process pool for plotting orientation of a probe using a quaternion that is sent using
    the Last In First Out queue approach. The probe points in the constants file are rotated by the quaternion
    value and plot as red dots. A surface is fit to the dots using trisurf. The 'close' button of the window is
    disabled, so the window can only be closed by the main window button.

    Args:
        lifo_queue (LifoQueue): MyManager queue object operating with LIFO principle.
        screen_dimensions (list): Width and height of screen for placing plotting window.
    """
    print('Starting plotting process...')
    window = Psg.Window('Orientation Plot', Layout.plotting_layout(), element_justification='c',
                        finalize=True, location=(screen_dimensions[0] - 450, 50), disable_close=True)
    # Plot variables.
    fig = Figure(figsize=(3.5, 3.5), dpi=100)
    ax = fig.add_subplot(111, projection='3d')
    fig.patch.set_facecolor(Psg.DEFAULT_BACKGROUND_COLOR)

    ax.set_position((0, 0, 1, 1))
    ax.set_xlim([-5, 5])
    ax.set_ylim([-5, 5])
    ax.set_zlim([-5, 5])
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.set_zticklabels([])
    ax.set_facecolor(Psg.DEFAULT_BACKGROUND_COLOR)
    ax.azim = 40

    figure_canvas_agg = FigureCanvasTkAgg(fig, window['-CANVAS-PLOT-'].TKCanvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)

    while True:
        try:
            new_quaternion = lifo_queue.get(False)
            if new_quaternion == '-END-PROCESS-':
                break
            elif len(new_quaternion) == 4:
                # Empty the queue of older variables.
                while not lifo_queue.empty():
                    try:
                        lifo_queue.get(False)
                    except queue.Empty:
                        continue
                    lifo_queue.task_done()
                # Rotate the probe points using the given quaternion.
                rpp = rotate_points(c.PROBE_POINTS, new_quaternion)
                ax.cla()
                ax.set_xlim([-5, 5])
                ax.set_ylim([-5, 5])
                ax.set_zlim([-5, 5])
                ax.set_xticklabels([])
                ax.set_yticklabels([])
                ax.set_zticklabels([])
                ax.plot_trisurf(rpp[:, 0], rpp[:, 1], rpp[:, 2], color='blue')
                ax.scatter(rpp[:, 0], rpp[:, 1], rpp[:, 2], c='red')
                figure_canvas_agg.draw()
        except queue.Empty:
            pass
        # Enable read of window at 50fps.
        window.read(timeout=20)

    window.close()
    print('Ending plotting process...')

"""
Class for handling plotting the orientation of the probe.

Plotting is removed from the main process as it slows the main process down significantly.

A custom multiprocessing.manager class is created to enable a LIFO queue approach.
"""
import queue
import numpy as np
from pyquaternion import Quaternion
from classes import Layout
import PySimpleGUI as sg
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import multiprocessing
from queue import LifoQueue
from multiprocessing.managers import BaseManager
import constants as c


def rotatePoints(points: list, quaternion: list) -> np.array:
    """
    Rotate the list of points by the given quaternion.

    Args:
        points (list): List of (x, y, z) coordinates to be rotated.
        quaternion (list): List of quaternion values.

    Returns:
        rotatedPoints (np.array): List of rotated points as a numpy array.
    """
    rotatedPoints = []
    myQuaternion = Quaternion(quaternion)
    for point in points:
        rotatedPoints.append(myQuaternion.rotate(point))

    rotatedPoints = np.array(rotatedPoints)

    return rotatedPoints


class MyManager(BaseManager):
    """
    Custom class used to register LifoQueue to the multiprocessing manager class.
    """
    pass


MyManager.register('LifoQueue', LifoQueue)


class PlottingProcess:
    def __init__(self, window):
        """
        Initialise a plottingProcess object.

        Args:
            window (sg.Window): PySimpleGUI object that is needed to acquire screen dimensions.
        """
        self.screenDimensions = window.get_screen_dimensions()
        self.plottingAsyncProcess = None
        self.manager = MyManager()
        self.manager.start()
        self.plottingQueue = None
        self.pool = None

    def startPlotting(self):
        """
        Create the queue object, processing pool, and start the plottingProcess running in the process pool.
        """
        self.plottingQueue = self.manager.LifoQueue()
        self.pool = multiprocessing.Pool(1)
        self.plottingAsyncProcess = self.pool.apply_async(plottingProcess,
                                                          args=(self.plottingQueue, self.screenDimensions))

    def plotOrientation(self, quaternion):
        """
        Add a quaternion to the queue to be plotted when the plotting process is ready.

        Args:
            quaternion (list): Quaternion constants received from the IMU.
        """
        self.plottingQueue.put(quaternion)

    def endPlotting(self):
        """
        Close and join the plottingProcess. First the while loop in the plottingProcess method is broken, then the
        plottingQueue is deleted (helps with memory release), and the process pool is closed and joined.
        """
        self.plottingQueue.put('-END-PROCESS-')
        del self.plottingQueue
        self.pool.close()
        self.pool.join()


def plottingProcess(lifoQueue, screenDimensions):
    """
    Method to be run in an async_process pool for plotting orientation of a probe using a quaternion that is sent using
    the Last In First Out queue approach. The probe points in the constants file are rotated by the quaternion
    value and plot as red dots. A surface is fit to the dots using trisurf.

    Args:
        lifoQueue (LifoQueue): MyManager queue object operating with LIFO principle.
        screenDimensions (list): Width and height of screen for placing plotting window.
    """
    print('Starting plotting process...')
    plottingWindow = sg.Window('Orientation Plot', Layout.getPlottingWindowLayout(), element_justification='c',
                               finalize=True, location=(screenDimensions[0] - 600, 50), disable_close=True)

    fig = Figure(figsize=(5, 5), dpi=100)
    ax = fig.add_subplot(111, projection='3d')
    fig.patch.set_facecolor(sg.DEFAULT_BACKGROUND_COLOR)

    ax.set_position((0, 0, 1, 1))
    ax.set_xlim([-5, 5])
    ax.set_ylim([-5, 5])
    ax.set_zlim([-5, 5])
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.set_zticklabels([])
    ax.set_facecolor(sg.DEFAULT_BACKGROUND_COLOR)
    ax.azim = 40

    figure_canvas_agg = FigureCanvasTkAgg(fig, plottingWindow['-CANVAS-PLOT-'].TKCanvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)

    while True:
        try:
            newQuaternion = lifoQueue.get(False)
            if newQuaternion == '-END-PROCESS-':
                break
            elif len(newQuaternion) == 4:
                rpp = rotatePoints(c.PROBE_POINTS, newQuaternion)
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
        # Enable read of window at 10fps.
        plottingWindow.read(timeout=10)

    plottingWindow.close()
    print('Ending plotting process...')

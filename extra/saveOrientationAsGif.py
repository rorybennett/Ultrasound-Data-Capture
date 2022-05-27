"""A Python script for selecting a recorded data file and generating a gif of the orientation of the probe during
 recording of the data file. """
import csv
import os
from tkinter import filedialog
import matplotlib.pyplot as plt
import numpy as np
from pyquaternion import Quaternion
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import animation


def main():
    # IMU data collected from the data.txt file.
    imuData = []
    # Points representing the probe, used for orientation.
    probePoints = [
        [0, 0, 0],
        [-1, -.3, 0],
        [-2, -.8, 0],
        [0, -6, 0],
        [2, -.8, 0],
        [1, -.3, 0]]

    # Select video folder for orientation reconstruction.
    folderPath = filedialog.askdirectory(title="Select Video Folder",
                                         initialdir=os.path.split(os.getcwd())[0] + '\Generated\Videos')

    print(f"Orientation will be generated for: {folderPath.split('/')[-1]}")

    # Read quaternion data from data.txt file.
    with open(folderPath + '/data.txt', 'r') as fd:
        reader = csv.reader(fd)
        for row in reader:
            # Split row at white spaces
            quaternion = row[6:10]
            imuData.append(quaternion)

    # Convert to numpy array
    imuData = np.array(imuData)

    print(f'Total lines (frames): {len(imuData)}')

    # Plotting variables
    fig = plt.figure(figsize=(6, 6), dpi=100)
    ax = Axes3D(fig, auto_add_to_figure=False)
    fig.add_axes(ax)

    # Initialise the axis (also used to clear the axis).
    def init():
        ax.cla()
        ax.set_xlim(-5, 5)
        ax.set_ylim(-5, 5)
        ax.set_zlim(-5, 5)
        ax.view_init(elev=10, azim=30)
        return fig

    # Animation function where plotting and surface creation happen step-by-step through imuData.
    def animate(i):
        rpp = []
        myQuaternion = Quaternion(imuData[i])
        init()
        # Rotate probe points by given quaterion.
        for point in probePoints:
            rpp.append(myQuaternion.rotate(point))

        rpp = np.array(rpp)
        # Scatter main points.
        ax.scatter(rpp[:, 0], rpp[:, 1], rpp[:, 2], c='red')
        # Fit surface between points.
        ax.plot_trisurf(rpp[:, 0], rpp[:, 1], rpp[:, 2])
        return fig

    # Animation call.
    anim = animation.FuncAnimation(fig, animate, init_func=init, frames=len(imuData), interval=20, repeat=False)
    # Save animation as a .gif. Named after video folder name.
    name = folderPath.split('/')[-1] + '.gif'
    writerGif = animation.PillowWriter(fps=30)
    anim.save(name, writer=writerGif)
    print(f'GIF created: {name}.')


if __name__ == '__main__':
    main()

"""
A Python script for calculating and plotting the time differences between a set of recorded frames.

Used to test recording consistency.
"""

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

    # Select video folder for orientation reconstruction.
    folderPath = filedialog.askdirectory(title="Select Video Folder",
                                         initialdir=os.path.split(os.getcwd())[0] + '\\Generated\\Videos')

    print(f"Time differences will be plotted for: {folderPath.split('/')[-1]}")

    # Read file names from data.txt file, file names are time stamps in milliseconds.
    with open(folderPath + '/data.txt', 'r') as fd:
        reader = csv.reader(fd)
        for row in reader:
            # Split row at white spaces
            timestamp = row[0].split('-')[1]
            imuData.append(int(timestamp))

    # Convert to numpy array
    imuData = np.array(imuData)
    estimatedFps = int(len(imuData) / ((imuData[-1] - imuData[0]) / 1000))

    # Calculate differences
    timeDiff = []
    for i in range(len(imuData) - 1):
        timeDiff.append(imuData[i + 1] - imuData[i])

    # Display information
    print(f'Total lines (frames): {len(imuData)}')
    print(f"Are all frames in order: "
          f"{'Yes' if all(imuData[i] <= imuData[i + 1] for i in range(len(imuData) - 1)) else 'No'}")
    print(f'Estimated frame rate: {estimatedFps} fps')
    print(f'Theoretical time difference based on frame rate: {int(1000 / estimatedFps)} ms')
    print(f'Mean time difference based on frame names: {int(np.average(timeDiff))} ms')
    print(f'Minimum time difference: {int(np.amin(timeDiff))} ms')
    print(f'Maximum time difference: {int(np.amax(timeDiff))} ms')

    # Plotting variables
    fig = plt.figure(figsize=(10, 5), dpi=100)
    fig.suptitle('Time difference between successive frames')
    ax1 = fig.add_subplot(121)
    ax1.plot(timeDiff, linewidth=0.1)
    ax1.plot([0, len(timeDiff)], [int(np.average(timeDiff)), int(np.average(timeDiff))], linestyle='dashed',
             linewidth=0.2, c='red')
    ax1.set_xlabel('Frame number')
    ax1.set_ylabel('Time difference [milliseconds]')

    ax2 = fig.add_subplot(122)
    ax2.boxplot(timeDiff, labels=['Single Tests'])

    plt.show()


if __name__ == '__main__':
    main()

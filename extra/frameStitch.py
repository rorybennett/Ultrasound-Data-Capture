"""
A Python script for stitching a series of frames together to create a video.
"""
import cv2 as cv
import os
from tkinter import filedialog
import natsort


def main():
    # Get video directory
    folderPath = filedialog.askdirectory(title="Select Video Folder",
                                         initialdir=os.path.split(os.getcwd())[0] + '\\Generated\\Videos')
    folderName = folderPath.split("/")[-1]

    print("Creating video...")
    # Sort the files so the frames are in the correct order.
    sortedFile = natsort.natsorted(os.listdir(folderPath))
    # Add all frames to an array.
    imgArray = []
    for fileName in sortedFile:
        img = cv.imread(os.path.join(folderPath, fileName))
        imgArray.append(img)
    # Calculated total amount of frames
    totalFrames = len(imgArray) - 1
    # Estimate the recording's frame rate.
    fpsEstimate = totalFrames / ((int(sortedFile[-2].split("-")[-1].split(".")
                                      [0]) - int(sortedFile[0].split("-")[-1].split(".")[0])) / 1000)
    # Frame information
    height, width, layers = imgArray[0].shape
    frame_size = (width, height)
    # Use openCV's VideoWrite class for creating the video.
    fileName = os.path.split(os.getcwd())[0] + "\\extra\\" + folderName + ".avi"
    output = cv.VideoWriter(fileName, cv.VideoWriter_fourcc('M', 'J', 'P', 'G'), fpsEstimate, frame_size)
    # Display details of the video.
    print("====================================")
    print("Details")
    print("====================================")
    print(f"Total Frames: {totalFrames}")
    print(f"FPS estimate: {fpsEstimate:.0f}")
    print(f"Width: {width}")
    print(f"Height: {height}")
    print("====================================")
    # Write frames to file.
    for frame in imgArray:
        output.write(frame)

    output.release()


if __name__ == '__main__':
    main()

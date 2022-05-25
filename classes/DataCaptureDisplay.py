from pathlib import Path
import Utils

import PySimpleGUI as sg


class DataCaptureDisplay():
    def __init__(self):
        # Create initial directories for storing data.
        self.singleFramesPath, self.videosPath = Utils.createInitialDirectories()


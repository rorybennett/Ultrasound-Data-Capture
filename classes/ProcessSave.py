"""
Class for handling saving of frames after a recording has ended.
"""
import multiprocessing

import PySimpleGUI as Psg
import numpy as np

import constants as c
import utils as ut


class ProcessSave:
    def __init__(self):
        """
        Initialise a ProcessSave object.
        """
        self.async_process = None
        self.queue = None
        self.pool = None

    def start_process(self, frames, frame_timestamps, imu_acc, imu_q, data_file_path, recording_path):
        """
        Start the process that will save a recording.
        """
        self.pool = multiprocessing.Pool(1)
        self.async_process = self.pool.apply_async(process, args=(frames, frame_timestamps, imu_acc, imu_q,
                                                                  data_file_path, recording_path))


def process(frames, frame_timestamps, imu_acc, imu_q, data_file_path, recording_path):
    """
    Method to be run in an async_process pool for saving frame and IMU data.
    """
    try:
        print(f'Frames: {len(frames)}, Timestamps: {len(frame_timestamps)}, '
              f'Accelerations: {len(imu_acc)}, Quaternions: {len(imu_q)}.')
        current_data_file = open(data_file_path, 'w')

        accelerations = np.array(imu_acc)
        if accelerations.ndim == 2:
            accelerations[:, 0] = accelerations[:, 0] * 1000
        else:
            print('No accelerations given.')
            accelerations = np.zeros((1, 4))

        quaternions = np.array(imu_q)
        if quaternions.ndim == 2:
            quaternions[:, 0] = quaternions[:, 0] * 1000
        else:
            print('No quaternions given.')
            quaternions = np.zeros((1, 5))

        for index, frameData in enumerate(frames):
            Psg.PopupAnimated(image_source=Psg.DEFAULT_BASE64_LOADING_GIF, message='Saving to disk...',
                              keep_on_top=True, time_between_frames=50, text_color='black',
                              background_color=Psg.DEFAULT_BACKGROUND_COLOR)

            frame_time = frame_timestamps[index]

            acc_index = (np.abs(accelerations[:, 0] - frame_time)).argmin()
            acceleration = accelerations[acc_index, 1:]
            q_index = (np.abs(quaternions[:, 0] - frame_time)).argmin()
            quaternion = quaternions[q_index, 1:]

            frame_name = f'{index + 1}-{frame_timestamps[index]}'

            current_data_file.write(f'{frame_name},:'
                                    f'acc[,{acceleration[0]},{acceleration[1]},{acceleration[2]},]'
                                    f'q[,{quaternion[0]},{quaternion[1]},{quaternion[2]},{quaternion[3]},]'
                                    f'dimensions[,{frameData.shape[1]},{frameData.shape[0]},]'
                                    f'depth[,{c.DEFAULT_SCAN_DEPTH},]\n')
            ut.save_single_frame(frameData, f'{recording_path}\\{frame_name}.png')

        Psg.PopupAnimated(None)
        print('In memory frames have been recorded to disk.')
        current_data_file.close()
    except Exception as e:
        print(e)

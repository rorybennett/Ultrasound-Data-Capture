"""
Main class for capturing frames from the output of an ultrasound scanner and adding IMU orientation data to the frames.

"""
import time
from concurrent.futures import ThreadPoolExecutor

import PySimpleGUI as Psg

import constants as c
import styling as st
import utils as ut
from classes import FrameGrabber, ProcessSave
from classes import IMU
from classes import Layout
from classes import Menu
from classes import ProcessPlotting


class DataCaptureDisplay:
    def __init__(self):
        # Create initial directories for storing data.
        self.single_frames_path, self.video_path = ut.create_initial_directories()
        # Menu object.
        self.menu = Menu.Menu()
        # Layout object.
        self.layout = Layout.Layout(self.menu)
        # Record state of the program.
        self.enable_recording = False
        # Directory where recorded frames are stored.
        self.current_recording_path = None
        # Path to data.txt file where IMU data of recording is saved.
        self.current_data_file_path = None
        # File for saving IMU data of recording.
        self.current_data_file = None
        # Save a single frame.
        self.save_single_frame = False
        # Counter for labelling frame number in a recording.
        self.frame_grab_counter = 1
        # IMU object instantiated with default values.
        self.imu = IMU.IMU()
        # Display FrameGrabber results.
        self.enable_display = True
        # Enable plot updates
        self.enable_plotting = False
        # FrameGrabber object instantiated with default values.
        self.frame_grabber = FrameGrabber.FrameGrabber()
        # Initial search for system COM ports.
        self.com_ports = IMU.available_com_ports()
        # Threading executor.
        self.thread_executor = ThreadPoolExecutor()
        # Recording variables for storing (signal and IMU).
        self.frame_raw = None
        self.frames_to_record = []
        self.frame_record_times = []
        # Is frame available for resize?
        self.enable_frame_resize = False
        # Must the frame be saved?
        self.enable_frame_save = False
        # Time a recording was started.
        self.recording_start = None
        # Save data process.
        self.save_process = ProcessSave.ProcessSave()

        # IMU connect window
        self.window_imu = None

        self.window = Psg.Window('Ultrasound Data Capture', self.layout.get_initial_layout(),
                                 return_keyboard_events=True, finalize=True, use_default_focus=False,
                                 location=(20, 50))

        # Plotting process
        self.plotting_process = ProcessPlotting.ProcessPlotting(self.window)

        self.run()

    def run(self):
        """
        Main loop/thread for displaying the GUI and reacting to events, in standard PySimpleGUI fashion.
        """
        while True:
            gui_fps_1 = time.time()
            # Update recording times.
            if self.enable_recording:
                self.update_times()
            # Update IMU values if present.
            if self.imu.is_connected and self.imu.acceleration:
                self.update_accelerations()
            # Send orientation to plotting process.
            if self.enable_plotting and self.imu.quaternion:
                self.plotting_process.plot_orientation(self.imu.quaternion)

            event, values = self.window.read(timeout=10)

            if event in [Psg.WIN_CLOSED, 'None']:
                # On window close clicked.
                self.close()
                break

            # Event for updating Image frame (recording).
            if event == '-UPDT-IMAGE-FRAME-':
                self.window['-IMAGE-FRAME-'].update(data=values[event])

            # Menu events.
            if event.endswith('::-M-SIGNAL-CONNECT-'):
                self.set_signal_source_and_connect(int(event.split('::')[0]))
            elif event.endswith('::-M-SIGNAL-DISCONNECT-'):
                self.frame_grabber.disconnect()
                self.update_menus()
            elif event.endswith('::-M-SIGNAL-DIMENSIONS-'):
                self.change_signal_dimensions(event.split('::')[0].split('x'))
            elif event.endswith('::-M-IMU-CONNECT-'):
                self.show_imu_window()
            elif event.endswith('::-M-IMU-DISCONNECT-'):
                self.imu.disconnect()
                self.update_menus()
            elif event.endswith('::-M-IMU-RATE-'):
                self.imu.set_return_rate(float(event.split('Hz')[0]))
            elif event.endswith('::-M-IMU-BANDWIDTH-'):
                self.imu.set_bandwidth(int(event.split('Hz')[0]))
            elif event.endswith('::-M-IMU-ALGORITHM-'):
                self.imu.set_algorithm(int(event.split('-')[0]))
            elif event.endswith('::-M-IMU-CALIBRATE-'):
                self.imu.calibrate_acceleration()

            # Signal Display Events.
            if event == '-B-DISPLAY-TOGGLE-':
                self.toggle_display()
            elif event == '-B-RECORD-TOGGLE-':
                self.toggle_recording()
            elif (len(event) == 1 and ord(event) == 32) and self.frame_grabber.is_connected:
                self.toggle_recording()

            # IMU Display Events.
            if event == '-B-PLOT-TOGGLE-':
                self.toggle_plotting()

            # Thread events.
            if event == '-THD-SIGNAL-RATE-':
                self.window['-T-SIGNAL-RATE-'].update(f'{values[event]}')
            elif event == '-THD-RESIZE-RATE-':
                self.window['-T-RESIZE-RATE-'].update(f'{values[event]}')
            elif event == '-THD-FRAMES-SAVED-':
                self.window['-T-FRAMES-SAVED-'].update(f'{values[event]}')

            # GUI frame rate estimate.
            gui_dt = time.time() - gui_fps_1
            gui_fps = int(1 / gui_dt) if gui_dt > 0.00999 else '100+'

            self.window['-T-GUI-RATE-'].update(f'{gui_fps}')

    def toggle_recording(self):
        """
        Toggle self.enableRecording. If recording is disabled, the data stored in memory is saved to disk.
        """
        # Create video directory for saving frames.
        if not self.enable_recording:
            self.current_recording_path, self.current_data_file_path = ut.create_recording_directory(self.video_path)
            self.frames_to_record = []
            self.frame_record_times = []
            self.frame_grab_counter = 1
            self.recording_start = time.time()
            self.window['-T-RECORD-START-'].update(time.strftime('%H:%M:%S'))
            self.enable_recording = True
            if self.imu.is_connected:
                self.imu.start_recording()
        else:
            self.enable_recording = False
            self.imu.stop_recording()
            time.sleep(0.03)
            self.save_process.start_process(self.frames_to_record, self.frame_record_times, self.imu.accelerations,
                                            self.imu.quaternions, self.current_data_file_path,
                                            self.current_recording_path)
            time.sleep(0.03)
            self.frames_to_record = []
            self.imu.clear_data()

        # Set element states.
        self.window['-B-RECORD-TOGGLE-'].update(
            button_color=st.COL_BTN_ACTIVE if self.enable_recording else Psg.DEFAULT_BUTTON_COLOR,
            text='Stop Recording' if self.enable_recording else 'Start Recording')

    def thread_get_frames(self):
        """
        Thread for acquiring frames from FrameGrabber object.
        """
        print('Thread starting up: thread_get_frames.')
        while self.frame_grabber.is_connected:
            signal_fps_1 = time.time()
            # Grab frame.
            res, self.frame_raw = self.frame_grabber.get_frame()
            # Successful frame read?
            if res:
                # Is recording enabled?
                if self.enable_recording:
                    self.frames_to_record.append(self.frame_raw)
                    self.frame_record_times.append(int(time.time() * 1000))
                    self.frame_grab_counter += 1
                    self.window.write_event_value(key='-THD-FRAMES-SAVED-', value=self.frame_grab_counter)

                # Display enabled?
                if self.enable_display:
                    self.enable_frame_resize = True

                # Signal frame rate estimate.
                signal_dt = time.time() - signal_fps_1
                signal_fps = int(1 / signal_dt) if signal_dt != 0 else 100
                self.window.write_event_value(key='-THD-SIGNAL-RATE-', value=signal_fps)

        print('-------------------------------------------\nThread closing down: '
              'thread_get_frames.\n-------------------------------------------')
        self.window.write_event_value(key='-THD-SIGNAL-RATE-', value=0)

    def thread_resize_frames(self):
        """
        Thread for resizing a frame to be displayed in the GUI window.
        """
        print('Thread starting up: thread_resize_frames.')
        while self.frame_grabber.is_connected:
            if self.enable_frame_resize:
                self.enable_frame_resize = False
                resize_fps_1 = time.time()
                resized_frame = ut.resize_frame(self.frame_raw, c.DISPLAY_DIMENSIONS, ut.INTERPOLATION_NEAREST)
                frame_bytes = ut.frame_to_bytes(resized_frame)
                self.window.write_event_value(key='-UPDT-IMAGE-FRAME-', value=frame_bytes)
                # Resize frame rate estimate.
                resize_fps_dt = time.time() - resize_fps_1
                resize_fps = int(1 / resize_fps_dt)
                self.window.write_event_value(key='-THD-RESIZE-RATE-', value=resize_fps)
            else:
                self.window.write_event_value(key='-THD-RESIZE-RATE-', value=0)

            # Sleep thread.
            time.sleep(0.03)

        print('-------------------------------------------\nThread closing down: '
              'thread_resize_frames.\n-------------------------------------------')
        self.window.write_event_value(key='-THD-RESIZE-RATE-', value=0)

    def toggle_display(self):
        """
        Toggle self.enableDisplay. Disabling the display can give a moderate frame rate boost, especially when
        recording frames.
        """
        self.enable_display = not self.enable_display
        self.window['-B-DISPLAY-TOGGLE-'].update(
            text='Disable Display' if self.enable_display else 'Enable Display',
            button_color=Psg.DEFAULT_BUTTON_COLOR if not self.enable_display else st.COL_BTN_ACTIVE)

    def set_signal_source_and_connect(self, signal_source):
        """
        Set the source of the video signal then attempt to connect to the new source.
        """
        # Set source.
        self.frame_grabber.signalSource = signal_source
        # Attempt to connect to source (internally disconnect if currently connected).
        self.frame_grabber.connect()
        # Start frame threads.
        self.thread_executor.submit(self.thread_get_frames)
        time.sleep(0.01)
        self.thread_executor.submit(self.thread_resize_frames)
        # Update menus.
        self.update_menus()
        # Set element states.
        self.window['-B-RECORD-TOGGLE-'].update(disabled=False if self.frame_grabber.is_connected else True)
        self.window['-T-SIGNAL-DIMENSIONS-'].update(
            f'Signal Dimensions: {(self.frame_grabber.width, self.frame_grabber.height)}.')

    def update_times(self):
        """
        Update the displayed times related to a recording that is currently taking place.
        """
        end_time = time.time()
        elapsed_time = end_time - self.recording_start
        # Set element states.
        self.window['-T-RECORD-ELAPSED-'].update(time.strftime('%H:%M:%S', time.localtime(elapsed_time)))

    def update_accelerations(self):
        """
        update displayed acceleration values.
        """
        self.window['-T-IMU-ACC-'].update(f'Ax: {self.imu.acceleration[0]:.2f}\t'
                                          f'Ay: {self.imu.acceleration[1]:.2f}\t'
                                          f'Az: {self.imu.acceleration[2]:.2f}')

    def toggle_plotting(self):
        """
        Toggle self.enablePlotting.
        """
        self.enable_plotting = not self.enable_plotting

        if self.enable_plotting:
            self.plotting_process.start_plotting()
        else:
            self.plotting_process.end_plotting()

        self.window['-B-PLOT-TOGGLE-'].update(
            text='Hide Orientation' if self.enable_plotting else 'Show Orientation',
            button_color=st.COL_BTN_ACTIVE if self.enable_plotting else Psg.DEFAULT_BUTTON_COLOR)

    def change_signal_dimensions(self, dimensions):
        """
        Attempt to change the signal dimensions from the menu click.
        """
        self.frame_grabber.set_grabber_properties(width=int(dimensions[0]), height=int(dimensions[1]),
                                                  fps=c.DEFAULT_FRAME_RATE)
        self.window['-T-SIGNAL-DIMENSIONS-'].update(
            f'Signal Dimensions: {(self.frame_grabber.width, self.frame_grabber.height)}.')

    def show_imu_window(self):
        """
        Show a window for the user to connect to an IMU based on COM port and baud rate selection.
        """
        self.window_imu = Psg.Window('Connect to IMU', Layout.imu_layout(self.com_ports, self.imu.com_port,
                                                                         self.imu.baudRate),
                                     element_justification='center', modal=True)

        while True:
            event, values = self.window_imu.read()

            if event in [Psg.WIN_CLOSED, 'None']:
                # On window close.
                break
            elif event == '-B-COM-REFRESH-':
                # On refresh available COM ports clicked.
                self.com_ports = IMU.available_com_ports()
                # Set elements
                self.window_imu['-COMBO-COM-PORT-'].update(values=self.com_ports)
            elif event == '-B-IMU-CONNECT-':
                # On connect button clicked.
                self.imu.com_port = str(values['-COMBO-COM-PORT-']).split(' - ')[0]
                self.imu.baudRate = int(values['-COMBO-BAUD-RATE-'])
                self.imu.connect()
                if self.imu.is_connected:
                    break

        self.update_menus()
        self.window_imu.close()

    def update_menus(self):
        """
        Helper function that updates the main window's menu.
        """
        # Set elements.
        self.window['-M-'].update(
            menu_definition=self.menu.get_menu(self.frame_grabber.is_connected, self.imu.is_connected,
                                               self.imu.com_port))

    def close(self):
        """
        Delete references to IMU object for garbage collection.
        """
        self.plotting_process.end_plotting()

        if self.imu.is_connected:
            self.imu.disconnect()
            del self.imu

        if self.frame_grabber.is_connected:
            self.frame_grabber.disconnect()


if __name__ == '__main__':
    DataCaptureDisplay()

"""
IMU class for handling the IMU connection and messages. The Witmotion Python module is maintained by some rando and not
by the company. It is also not complete, as some quite basic functionality is missing. It does enough for now.

The extra classes at the bottom are used to expand on the Witmotion library capabilities.
"""
import time
from enum import Enum

import serial.tools.list_ports
import witmotion as wm


def available_com_ports():
    """
    Query all available COM ports. This will return sorted COM ports that are active/inactive AND ports that are not
    being used by a Witmotion IMU. If no data is returned from a connected COM port then it may not be the correct COM
    port. The COM ports can represent a USB or bluetooth connection.

    Returns:
        all_com_ports (list[str]): A list of available COM ports. Only the port number is returned, e.g. 'COM7'.
    """
    port_info = serial.tools.list_ports.comports()

    all_com_ports = []

    for i in sorted(port_info):
        all_com_ports.append(i)

    if not all_com_ports:
        all_com_ports = ['None']

    return all_com_ports


class IMU:
    """
    Class for handling a connection to a Witmotion IMU sensor. Tested with some of their Bluetooth range of sensors.
    During initialisation no connection is made, only variable instantiation. After a connection is made a callback is
    subscribed that lets the class know when new IMU data is available. This appears to be off the main thread, which
    can cause errors during closing of the main program, but it does not seem to be anything worth worrying about.

    The default values made available are acceleration, angle, and quaternion values, if other fields are
    required then the __imu_callback() method must be updated.
    """

    def __init__(self, com_port='COM3', baud_rate=115200):
        """
        Initialises an IMU object. No connection is made, only default variables
        are set.

        Args :
            com_port (String, optional): Comport the IMU is connected to. Defaults to 'COM3'.
            baud_rate (int, optional): Operational baud rate of the IMU. Defaults to 115200.
        """
        self.imu = None  # Witmotion IMU object
        self.is_connected = False  # Has an IMU object been successfully connected (does not account for callback).
        self.com_port = com_port  # IMU object's COM port
        self.baudRate = baud_rate  # IMU object's baudRate

        self.accelerations = []  # Acceleration returned by IMU
        self.angles = []  # Euler angles returned by IMU
        self.quaternions = []  # Quaternion returned by IMU

        self.acceleration = []  # Mostly used for updating the display.
        self.quaternion = []
        self.angle = []

        self.save_data = False  # Should data be appended for later storage.
        self.imu_start_time = 0  # IMU time at the start of data storage.
        self.system_start_time = 0  # System time at the start of data storage.

    def __imu_callback(self, msg):
        """
        Callback subscribed to the IMU object. Called whenever a new dataset is ready to be read. This callback is
        activated for every value sent by the IMU (Acceleration, Quaternion, Angle, ..etc) and not just for each serial
        packet.

        Args:
            msg (String): The type of dataset that is newly available.
        """
        msg_type = type(msg)

        imu_time = self.imu.get_timestamp()

        save_time = imu_time - self.imu_start_time + self.system_start_time if imu_time else 0

        if msg_type is wm.protocol.AccelerationMessage:
            ac = self.imu.get_acceleration()
            self.acceleration = ac
            if self.save_data:
                self.accelerations.append([save_time, ac[0], ac[1], ac[2]])
        elif msg_type is wm.protocol.QuaternionMessage:
            q = self.imu.get_quaternion()
            self.quaternion = q
            if self.save_data:
                self.quaternions.append([save_time, q[0], q[1], q[2], q[3]])
        elif msg_type is wm.protocol.AngleMessage:
            an = self.imu.get_angle()
            self.angle = an
            if self.save_data:
                self.angles.append([save_time, an[0], an[1], an[2]])

    def start_recording(self):
        """
        Set save_data to True so the data received from the IMU is saved into a variable. The locally stored data has
        an adjusted timestamp added to it:
                        current time on imu - start test time on imu + start test time on system.
        """
        self.save_data = True
        self.clear_data()

        self.imu_start_time = self.imu.get_timestamp()
        self.system_start_time = time.time()
        print('Starting IMU data save...')

    def stop_recording(self):
        """
        Set save_data to False to start saving data to a local variable.
        """
        self.save_data = False
        print('Ending IMU data save...')

    def clear_data(self):
        """
        Reset variables where IMU data is stored during a recording.
        """
        self.accelerations = []
        self.quaternions = []
        self.angles = []

    def connect(self) -> bool:
        """
        Attempt to connect to the IMU. If the COM port and baud rate were not explicitly set, the default values will
        be used. The callbackCounter and startTime are reset on a successful connection. self.isConnected is set to
        True if a successful IMU object is created, and does not account for the state of the callback subscription.
        If subscription fails the self.isConnected state can still be True but the success_flag will be False.

        Returns:
            success_flag (bool): True if the IMU connects, else False.
        """
        success_flag = False
        try:
            print(
                f'Attempting to connect to {self.com_port} at {self.baudRate}...', end=' ')
            self.imu = wm.IMU(path=self.com_port, baudrate=self.baudRate)
            self.is_connected = True

            print('IMU serial connection created. Subscribing callback...', end=' ')
            self.imu.subscribe(self.__imu_callback)

            print(f'Callback subscribed. IMU connected on {self.com_port}.')
            success_flag = True
        except Exception as e:
            print(f'Error initialising IMU class object: {e}')
            if self.is_connected:
                self.disconnect()
        return success_flag

    def disconnect(self):
        """
        Disconnect from IMU. This closes the IMU and the serial connection. For some reason closing the IMU does not
        close the serial connection, this is a problem with the Witmotion module.
        """
        try:
            if self.imu:
                print(f'Attempting to disconnect from IMU ({self.com_port})...', end=' ')
                self.imu.close()
                self.imu.ser.close()
                print('Disconnected from IMU!')
                self.is_connected = False
        except Exception as e:
            print(f'Error disconnecting from IMU: {e}')

    def set_return_rate(self, rate):
        """
        Set the return rate of the IMU in Hz. Not all IMUs have the same return rate capabilities and at the moment
        there is no way to test if the command was received correctly by the IMU. The return rate just needs to be
        monitored.

        Args:
            rate (float): Requested return rate. One of the values in the constants.py file.
        """
        print(f'Setting return rate of IMU: {rate}Hz')
        self.imu.set_update_rate(rate)

    def set_bandwidth(self, bandwidth):
        """
        Set the bandwidth of the IMU in Hz. If a high return rate of 200Hz is required, the bandwidth must be set
        to a higher rate (256Hz), if it is not increased the IMU will return repeat values.

        The Witmotion library does not have the capability to change the bandwidth, so it is mostly done here
        using lower level functions.

        Args:
            bandwidth (int): Requested bandwidth as int. One of the values in the constants.py file.
        """
        print(f'Setting bandwidth of IMU: {bandwidth}Hz')
        sel = {
            256: BandwidthSelect.bandwidth_256_Hz,
            184: BandwidthSelect.bandwidth_188_Hz,
            98: BandwidthSelect.bandwidth_98_Hz,
            42: BandwidthSelect.bandwidth_42_Hz,
            21: BandwidthSelect.bandwidth_20_Hz,
            10: BandwidthSelect.bandwidth_10_Hz,
            5: BandwidthSelect.bandwidth_5_Hz}[bandwidth]
        self.imu.send_config_command(wm.protocol.ConfigCommand(register=RegisterExtra.bandwidth, data=sel.value))

    def set_algorithm(self, algorithm_type):
        """
        Set the algorithm of the IMU. It can either be 6-axis (without the use of a magnetometer), or 9-axis (with a
        magnetometer). Using the 6-axis algorithm can reduce transient settling of the orientation angles. Using the
        9-axis algorithm uses north as the reference angle.

        Args:
            algorithm_type (int): Either 6 or 9.
        """
        print(f'Setting the algorithm of the IMU: {algorithm_type}-axis.')
        self.imu.set_algorithm_dof(algorithm_type)

    def calibrate_acceleration(self):
        """
        Tell the IMU to calibrate its accelerometer. The IMU should be placed flat on a horizontal service for 5 seconds
        while the calibration continues. Nothing is returned after the calibration, but you will see the acceleration
        values calibrate to (0, 0, 9.8) once the process is complete.

        Take note that the orientation of the IMU affects the calibration. If after calibration the IMU is rolled by
        180 degrees and the z-acceleration is not roughly -9.8m/s^2 it means the IMU was "upside-down" during
        calibration.
        """
        print('Calibrating accelerometer. Do not move the device for 5 seconds...')
        self.imu.send_config_command(wm.protocol.ConfigCommand(register=wm.protocol.Register.calsw, data=0x01))


class BandwidthSelect(Enum):
    """
    Supplementary class to set the bandwidth of the IMU.
    """
    bandwidth_256_Hz = 0x00
    bandwidth_188_Hz = 0x01
    bandwidth_98_Hz = 0x02
    bandwidth_42_Hz = 0x03
    bandwidth_20_Hz = 0x04
    bandwidth_10_Hz = 0x05
    bandwidth_5_Hz = 0x06


class RegisterExtra(Enum):
    """
    Supplementary class for registry editing.
    """
    bandwidth = 0x1f

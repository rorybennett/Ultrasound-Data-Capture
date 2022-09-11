"""
IMU class for handling the IMU connection and messages. The Witmotion Python module is maintained by some rando and not
by the company. It is also not complete, as some quite basic functionality is missing. It does enough for now.

The extra classes at the bottom are used to expand on the Witmotion library capabilities.
"""
from enum import Enum

import witmotion as wm
import time
import serial.tools.list_ports


def availableComPorts():
    """
    Query all available COM ports. This will return sorted COM ports that are active/inactive AND ports that are not
    being used by a Witmotion IMU. If no data is returned from a connected COM port then it may not be the correct COM
    port. The COM ports can represent a USB or bluetooth connection.

    Returns:
        allComPorts (list[str]): A list of available COM ports. Only the port number is returned, e.g. 'COM7'.
    """
    portInfo = serial.tools.list_ports.comports()

    allComPorts = []

    for port, description, hid in sorted(portInfo):
        allComPorts.append(port)

    if not allComPorts:
        allComPorts = ['None']

    return allComPorts


class IMU:
    """
    Class for handling a connection to a Witmotion IMU sensor. Tested with some of their Bluetooth range of sensors.
    During initialisation no connection is made, only variable instantiation. After a connection is made a callback is
    subscribed that lets the class know when new IMU data is available. This appears to be off the main thread, which
    can cause errors during closing of the main program, but it does not seem to be anything worth worrying about.

    The default values made available are acceleration, angle, and quaternion values, if other fields are
    required then the __imuCallback() method must be updated.
    """

    def __init__(self, comPort='COM3', baudRate=115200):
        """
        Initialises an IMU object. No connection is made, only default variables
        are set.

        Args :
            comPort (String, optional): Comport the IMU is connected to. Defaults to 'COM3'.
            baudRate (int, optional): Operational baud rate of the IMU. Defaults to 115200.
        """
        self.startTime = time.time()
        self.callbackCounter = None
        self.imu = None  # Witmotion IMU object
        self.isConnected = False  # Has an IMU object been successfully connected (does not account for callback).
        self.comPort = comPort  # IMU object's COM port
        self.baudRate = baudRate  # IMU object's baudRate
        self.acceleration = []  # Acceleration returned by IMU
        self.angle = []  # Euler angles returned by IMU
        self.quaternion = []  # Quaternion returned by IMU

    def __del__(self):
        """
        On class object delete the IMU object must be disconnected. This ensures that required connections are closed.
        """
        self.disconnect()
        self.imu = None

    def __imuCallback(self, msg):
        """
        Callback subscribed to the IMU object. Called whenever a new dataset is ready to be read. This callback is
        activated for every value sent by the IMU (Acceleration, Quaternion, Angle, ..etc) and not just for each serial
        packet.

        Args:
            msg (String): The type of dataset that is newly available.
        """
        msg_type = type(msg)

        if msg_type is wm.protocol.AccelerationMessage:
            self.acceleration = self.imu.get_acceleration()
        elif msg_type is wm.protocol.QuaternionMessage:
            self.quaternion = self.imu.get_quaternion()
            self.callbackCounter += 1
        elif msg_type is wm.protocol.AngleMessage:
            self.angle = self.imu.get_angle

    def connect(self) -> bool:
        """
        Attempt to connect to the IMU. If the COM port and baud rate were not explicitly set, the default values will
        be used. The callbackCounter and startTime are reset on a successful connection. self.isConnected is set to
        True if a successful IMU object is created, and does not account for the state of the callback subscription.
        If subscription fails the self.isConnected state can still be True but the successFlag will be False.

        Returns:
            successFlag (bool): True if the IMU connects, else False.
        """
        successFlag = False
        try:
            print(
                f'Attempting to connect to {self.comPort} at {self.baudRate}...')
            self.imu = wm.IMU(path=self.comPort, baudrate=self.baudRate)
            self.isConnected = True

            print('IMU serial connection created. Subscribing callback...')
            self.imu.subscribe(self.__imuCallback)

            print(f'Callback subscribed. IMU connected on {self.comPort}!')
            self.callbackCounter = 0
            self.startTime = time.time()
            successFlag = True
        except Exception as e:
            print(f'Error initialising IMU class object: {e}')
            if self.isConnected:
                self.disconnect()
        return successFlag

    def disconnect(self):
        """
        Disconnect from IMU. This closes the IMU and the serial connection. For some reason closing the IMU does not
        close the serial connection, this is a problem with the Witmotion module.
        """
        try:
            if self.imu:
                print(f'Attempting to disconnect from IMU ({self.comPort})...')
                self.imu.close()
                self.imu.ser.close()
                print('Disconnected from IMU!')
                self.isConnected = False
        except Exception as e:
            print(f'Error disconnecting from IMU: {e}')

    def setReturnRate(self, rate):
        """
        Set the return rate of the IMU in Hz. Not all IMUs have the same return rate capabilities and at the moment
        there is no way to test if the command was received correctly by the IMU. The return rate just needs to be
        monitored.

        Args:
            rate (float): Requested return rate. One of the values in the constants.py file.
        """
        print(f'Setting return rate of IMU: {rate}Hz')
        self.imu.set_update_rate(rate)

    def setBandwidth(self, bandwidth):
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
            94: BandwidthSelect.bandwidth_98_Hz,
            42: BandwidthSelect.bandwidth_42_Hz,
            21: BandwidthSelect.bandwidth_20_Hz,
            10: BandwidthSelect.bandwidth_10_Hz,
            5: BandwidthSelect.bandwidth_5_Hz}[bandwidth]
        self.imu.send_config_command(wm.protocol.ConfigCommand(register=RegisterExtra.bandwidth, data=sel.value))

    def setAlgorithm(self, algorithmType):
        """
        Set the algorithm of the IMU. It can either be 6-axis (without the use of a magnetometer), or 9-axis (with a
        magnetometer). Using the 6-axis algorithm can reduce transient settling of the orientation angles. Using the
        9-axis algorithm uses north as the reference angle.

        Args:
            algorithmType (int): Either 6 or 9.
        """
        print(f'Setting the algorithm of the IMU: {algorithmType}-axis.')
        self.imu.set_algorithm_dof(algorithmType)

    def calibrateAcceleration(self):
        """
        Tell the IMU to calibrate its accelerometer. The IMU should be placed flat on a horizontal service for 5 seconds
        while the calibration continues. Nothing is returned after the calibration, but you will see the acceleration
        values calibrate to (0, 0, 9.8) once the process is complete.

        Take note that the orientation of the IMU affects the calibration. If after calibration the IMU is rolled by
        180 degrees and the z-acceleration is not roughly -9.8m/s^2 it means the IMU was "upside-down" during
        calibration.
        todo Print message stating that IMU will be calibrated
        """
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

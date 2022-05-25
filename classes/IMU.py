import witmotion as wm
import time
import serial.tools.list_ports


def availableComPorts():
    """
    Query all available COM ports. This will return sorted COM ports that are active/inactive AND
    ports that are not being used by a Witmotion IMU. If no data is returned from a connected
    COM port then it may not be the correct COM port.

    Returns:
        portInfo (list[ListPortInfo]0: A list of available COM ports as [Port Number], [Description], [HardwareId].
    """
    portInfo = serial.tools.list_ports.comports()

    return sorted(portInfo)


class IMU:
    """
    Class for handling a connection to a Witmotion IMU sensor. Tested with some of their Bluetooth range
    of sensors. During initialisation the requested COM port is opened at the specified baudrate. Then
    a callback is subscribed that lets the class know when new IMU data is avaible.

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
        self.isConnected = False  # Has an IMU object been successfully created
        self.comPort = comPort  # IMU object's COM port
        self.baudRate = baudRate  # IMU object's baudRate
        self.acceleration = []  # Acceleration returned by IMU
        self.angle = []  # Euler angles returned by IMU
        self.quaternion = []  # Quaternion returned by IMU

    def __del__(self):
        """
        On class object delete the IMU object must be disconnected.
        """
        self.disconnect()
        self.imu = None

    def __imuCallback(self, msg):
        """
        Callback subscribed to the IMU object. Called whenever a new dataset
        is ready to be read. This callback is activated for every value sent
        by the IMU (Acceleration, Quaternion, Angle, ..etc) and not just for
        each serial packet.

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

    def connect(self):
        """
        Attempt to connect to the IMU. If the Com port and baudRate were not explicitly set, the default
        values will be used. The callbackCounter and startTime are reset on a successful connection.
        """
        try:
            print(
                f'Attempting to connect to {self.comPort} at {self.baudRate}...')
            self.imu = wm.IMU(path=self.comPort, baudrate=self.baudRate)

            print('IMU serial connection created. Subscribing callback...')
            self.imu.subscribe(self.__imuCallback)

            print(f'Callback subscribed. IMU connected on {self.comPort}!')
            self.isConnected = True
            self.callbackCounter = 0
            self.startTime = time.time()
        except Exception as e:
            print(f'Error initialising IMU class object: {e}')
            self.disconnect()
            raise

    def disconnect(self):
        """
        Disconnect from IMU. This closes the IMU and the serial connection. For some reason closing
        the IMU does not close the serial connection, this is a problem with the Witmotion
        module.
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

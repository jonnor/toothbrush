
# Copied from https://github.com/bikeNomad/micropython-xiao_ble_nrf52840_sense/blob/main/src/lib/lsm6ds.py
# Initially copied from pimoroni: https://github.com/pimoroni/lsm6ds3-micropython/blob/main/src/lsm6ds3.py
# Edited to use struct and provide status

import asyncio
from struct import pack, unpack
from micropython import const

# Registers
WHO_AM_I = const(0x0F)
CTRL1_XL = const(0x10) # accelerometer config
CTRL2_G = const(0x11) # gyro config
CTRL3_C = const(0x12)
CTRL8_XL = const(0x17)
CTRL10_C = const(0x19)
STATUS_REG = const(0x1E)

# FIFO registers
FIFO_CTRL5 = const(0x0A)
FIFO_STATUS1 = const(0x3A)
FIFO_DATA_OUT_L = const(0x3E)
FIFO_CTRL3 = const(0x08)

# This is the start of the data registers for the Gyro and Accelerometer
# There are 12 Bytes in total starting at 0x23 and ending at 0x2D
OUTX_L_G = const(0x22)
OUTX_L_XL = const(0x28)

STEP_COUNTER_L = const(0x4B)
STEP_COUNTER_H = const(0x4C)
TAP_SRC = const(0x1C)
TAP_CFG = const(0x58)
FUNC_SRC1 = const(0x53)
FUNC_SRC2 = const(0x54)
TAP_THS_6D = const(0x59)
FREE_FALL = const(0x5D)
WAKE_UP_THS = const(0x5B)
WAKE_UP_SRC = const(0x1B)
INT_DUR2 = const(0x5A)

# CONFIG DATA
NORMAL_MODE_104HZ = const(0x40)
NORMAL_MODE_208HZ = const(0x50)
PERFORMANCE_MODE_416HZ = const(0x60)
LOW_POWER_26HZ = const(0x02)
SET_FUNC_EN = const(0xBD)
RESET_STEPS = const(0x02)
TAP_EN_XYZ = const(0x8E)
TAP_THRESHOLD = const(0x02)
DOUBLE_TAP_EN = const(0x80)
DOUBLE_TAP_DUR = const(0x20)

ACCEL_FMT = "<hhh"
GYRO_FMT = "<hhh"
COMBO_FMT = "<hhhhhh"


class LSM6DS3:
    def __init__(self, i2c, address=0x6A, mode=NORMAL_MODE_104HZ):
        self.bus = i2c
        self.address = address
        self.mode = mode
        
        # preallocate a buffer for tag(1byte) + sample(6bytes)
        self.sample_buffer = bytearray(7)

        # Set gyro mode/enable
        self.bus.writeto_mem(self.address, CTRL2_G, bytearray([self.mode]))

        # Set accel mode/enable
        self.bus.writeto_mem(self.address, CTRL1_XL, bytearray([self.mode]))

        # Send the reset bit to clear the pedometer step count
        self.bus.writeto_mem(self.address, CTRL10_C, bytearray([RESET_STEPS]))

        # Enable sensor functions (Tap, Tilt, Significant Motion)
        self.bus.writeto_mem(self.address, CTRL10_C, bytearray([SET_FUNC_EN]))

        # Enable X Y Z Tap Detection
        self.bus.writeto_mem(self.address, TAP_CFG, bytearray([TAP_EN_XYZ]))

        # Enable Double tap
        self.bus.writeto_mem(self.address, WAKE_UP_THS, bytearray([DOUBLE_TAP_EN]))

        # Set tap threshold
        self.bus.writeto_mem(self.address, TAP_THS_6D, bytearray([TAP_THRESHOLD]))

        # Set double tap max time gap
        self.bus.writeto_mem(self.address, INT_DUR2, bytearray([DOUBLE_TAP_DUR]))

        # enable BDU and IF_INC
        self.bus.writeto_mem(self.address, CTRL3_C, bytearray([0b0100_0100]))

    def _read_reg(self, reg, size):
        return self.bus.readfrom_mem(self.address, reg, size)
    
    def set_hp_filter(self, mode):
        self.bus.writeto_mem(self.address, CTRL8_XL, bytearray([self.mode]))

    def get_readings(self) -> tuple[int, int, int, int, int, int]:
        # Read 12 bytes starting from 0x22. This covers the XYZ data for gyro and accel
        # return: (GX,GY,GZ,XLX,XLY,XLZ)
        data = self._read_reg(OUTX_L_G, 12)
        return unpack(COMBO_FMT, data)

    def get_accel_readings(self) -> tuple[int, int, int]:
        # Read 6 bytes starting at 0x28. This is the XYZ data for the accelerometer.
        data = self._read_reg(OUTX_L_XL, 6)
        return unpack(ACCEL_FMT, data)

    def get_gyro_readings(self) -> tuple[int, int, int]:
        # Read 6 bytes starting from 0x22. This covers the XYZ data for gyro
        data = self._read_reg(OUTX_L_G, 6)
        return unpack(GYRO_FMT, data)

    def get_step_count(self):
        data = self._read_reg(STEP_COUNTER_L, 2)
        steps = unpack("<h", data)[0]
        return steps

    def reset_step_count(self):
        # Send the reset bit
        self.bus.writeto_mem(self.address, CTRL10_C, bytearray([RESET_STEPS]))
        # Enable functions again
        self.bus.writeto_mem(self.address, CTRL10_C, bytearray([SET_FUNC_EN]))

    def tilt_detected(self):
        tilt = self._read_reg(FUNC_SRC1, 1)
        tilt = (tilt[0] >> 5) & 0b1
        return tilt

    def sig_motion_detected(self):
        sig = self._read_reg(FUNC_SRC1, 1)
        sig = (sig[0] >> 6) & 0b1
        return sig

    def single_tap_detected(self):
        s = self._read_reg(TAP_SRC, 1)
        s = (s[0] >> 5) & 0b1
        return s

    def double_tap_detected(self):
        d = self._read_reg(TAP_SRC, 1)
        d = (d[0] >> 4) & 0b1
        return d

    def freefall_detected(self):
        fall = self._read_reg(WAKE_UP_SRC, 1)
        fall = fall[0] >> 5
        return fall

    def accel_data_ready(self):
        status = self._read_reg(STATUS_REG, 1)
        return status[0] & 1

    def gyro_data_ready(self):
        status = self._read_reg(STATUS_REG, 1)
        return status[0] & 2

    def all_data_ready(self):
        status = self._read_reg(STATUS_REG, 1)
        return (status[0] & 3) == 3

    def fifo_enable(self, enable):        

        FIFO_MODE_CONTINIOUS = 0b110

        # Set FIFO mode
        val = FIFO_MODE_CONTINIOUS

        # Set ODR
        val += (0x40 >> 1)

        print('fifo-enable', hex(val))
        self.bus.writeto_mem(self.address, FIFO_CTRL5, bytearray([val]))

        # Enable gyro and accel without decimation
        val = 0b00001001
        self.bus.writeto_mem(self.address, FIFO_CTRL3, bytearray([val]))


    def get_fifo_count(self):
        """
        Return the number of samples ready in the FIFO
        """
        buf = bytearray(2)
        self.bus.readfrom_mem_into(self.address, FIFO_STATUS1, buf)
        
        # only 4 bit from FIFO_STATUS2 is part of the count
        fifo_words = ((buf[1] & 0b1111) << 8) + buf[0]
        fifo_count = fifo_words // 6 # 3 gyro plus 3 accel
        #print('fifo count', buf, fifo_words, fifo_count)
        return fifo_count

    def read_samples_into(self, buf):
        """
        Read accelerometer samples from the FIFO

        NOTE: caller is responsible for ensuring that enough samples are ready.
        Typically by calling get_fifo_count() first
        """
        n_bytes = len(buf)

        temp = bytearray(6)

        start_count = self.get_fifo_count()

        # gyro data is first
        # acceleration data follows
        #words = 3*8
        #for i in range(words):
        #    self.bus.readfrom_mem_into(self.address, FIFO_DATA_OUT_L, temp)


        self.bus.readfrom_mem_into(self.address, FIFO_DATA_OUT_L, buf)


        end_count = self.get_fifo_count()

        print('ss', n_bytes, n_bytes//12, start_count, end_count, start_count-end_count)

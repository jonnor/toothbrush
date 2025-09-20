

import machine
from machine import Pin, I2C


import gc
import time
import math
import struct
import array
import asyncio
import sys

sys.path.insert(0, 'lib/') # XXX: why not on path?

from core import StateMachine, OutputManager, DataProcessor, empty_array, clamp

import lsm6ds

HW_M5STICK_PLUS2 = 'm5stick-plus2'
HW_XIAO_BLE_SENSE = 'xiao-ble-sense'

hardware = HW_XIAO_BLE_SENSE # TODO: autodetect ?


# Free memory used by imports
gc.collect()


def _test_outputs_asyncio():

    #buzzer_pin = machine.Pin(2, machine.Pin.OUT)
    #led_pin = machine.Pin(19, machine.Pin.OUT)

    # On XIAO BLE, pin 6, 26, 30 has RGB LED
    #led_pin = ("gpio0", 26)
    led_pin = ("pwm0", 0)
    # PWM1 is mapped to GPIO pins using Zephyr .overlay
    buzzer_pin = ("pwm0", 1)

    sm = StateMachine()
    states = sm._state_functions.keys()
    out = OutputManager(buzzer_pin=buzzer_pin, led_pin=led_pin)

    for state in states:
        sub_states = [0]
        if state == 'brushing':
            sub_states = list(range(0, 4))
        for sub in sub_states:
            print('test-output-state', state)
            await out.run(state, sub)
            asyncio.sleep_ms(1000)

def test_outputs():
    asyncio.run(_test_outputs_asyncio()) 

def deinterleave_samples(buf : bytearray,
        xs, ys, zs, rowstride=6, offset=0, format='>hhh'):
    """
    Convert raw bytes into X,Y,Z int16 arrays
    """
    assert (len(buf) % rowstride) == 0
    samples = len(buf) // rowstride
    assert len(xs) == samples
    assert len(ys) == samples
    assert len(zs) == samples

    #view = memoryview(buf)
    for i in range(samples/2):
        idx = offset + (i*rowstride)
        x, y, z = struct.unpack_from(format, buf, idx)
        xs[i] = x
        ys[i] = y
        zs[i] = z

def main():

    print('init-start')

    # Settings
    hop_length = 50
    window_length = hop_length
    samplerate = 50
    bytes_per_sample = 12 # FIXME: make MPU also support gyro

    # working buffers
    x_values = empty_array('h', hop_length)
    y_values = empty_array('h', hop_length)
    z_values = empty_array('h', hop_length)
    chunk = bytearray(bytes_per_sample*hop_length)

    print('setup-hardware-start')

    time.sleep(1)

    # Setup hardware-specific things
    if hardware == HW_M5STICK_PLUS2:
        # pin19 is internal red LED on M5StickC PLUS2
        led_pin = machine.Pin(19, machine.Pin.OUT)
        # pin2 is internal buzzer on M5StickC PLUS2
        buzzer_pin = machine.Pin(2)

        # On M5StickC we need to set HOLD pin to stay alive when on battery
        hold_pin = machine.Pin(4, machine.Pin.OUT)
        hold_pin.value(1)

        from mpu6886 import MPU6886
        imu = MPU6886(I2C(0, sda=21, scl=22, freq=100000))
        # Enable FIFO at a fixed samplerate
        imu.fifo_enable(True)
        imu.set_odr(samplerate)

        assert imu.bytes_per_sample == bytes_per_sample

    elif hardware == HW_XIAO_BLE_SENSE:
        print('hardware-init-xiao-ble-sense')
        time.sleep(1)

        led_pin = ("pwm0", 0)
        # PWM1 is mapped to GPIO pins using Zephyr .overlay
        buzzer_pin = ("pwm0", 1)

        # FIXME: use 52 Hz, and FIFO
        i2c = I2C("i2c0")
        imu = lsm6ds.LSM6DS3(i2c, mode=lsm6ds.NORMAL_MODE_104HZ | 0b0000_1000) # 104Hz, FS=4g

        imu.fifo_enable(True)


    else:
        raise ValueError("Unknown hardware: " + hardware)

    print('setup-hardware-end')

    out = OutputManager(buzzer_pin=buzzer_pin, led_pin=led_pin)

    processor = DataProcessor()
    sm = StateMachine(time=time.time(), verbose=1, prediction_filter_length=3)

    # TEST config
    sm.brushing_target_time = 20.0
    sm.idle_time_max = 5.0
    sm.brushing_started_time = 2.0

    print('init-done')

    def main_task():
        print('main-start')

        count = 0

        while True:

            count = imu.get_fifo_count()
            #print('fifo check', count)
            if count >= hop_length:
                start = time.ticks_ms()

                # read data
                read_start = time.ticks_ms()

                imu.read_samples_into(chunk)
                deinterleave_samples(chunk, x_values, y_values, z_values, rowstride=12, offset=6, format='<hhh')

                read_duration = time.ticks_ms() - read_start

                process_start = time.ticks_ms()
                motion, brushing = processor.process(x_values, y_values, z_values)
                process_duration = time.ticks_ms() - process_start
        
                t = time.time()
                sm.next(t, motion, brushing)

                print('main-inputs', t, brushing, motion, sm.state)

                progress_state = sm.progress_state
                progress = int(100*(sm.brushing_time / sm.brushing_target_time))
                print('main-progress', sm.brushing_time, progress, f'{progress}%', progress_state)

                # Update outputs
                await out.run(sm.state, progress_state)

                d = time.ticks_diff(time.ticks_ms(), start)
                print('main-iter-times', d, read_duration, process_duration)

            await asyncio.sleep_ms(10)
            #machine.lightsleep(100)

    asyncio.run(main_task())

if __name__ == '__main__':

    #test_outputs()

    try:
        main()
    except KeyboardInterrupt:
        raise
    except Exception as e:
        print('unhandled-exception', e)
        time.sleep(1)
        raise e
        machine.reset()



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


def main():

    print('init-start')

    # Settings
    hop_length = 50
    window_length = hop_length
    samplerate = 50
    bytes_per_sample = 6

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
        mpu = MPU6886(I2C(0, sda=21, scl=22, freq=100000))
        # Enable FIFO at a fixed samplerate
        mpu.fifo_enable(True)
        mpu.set_odr(samplerate)

        assert mpu.bytes_per_sample == bytes_per_sample

    elif hardware == HW_XIAO_BLE_SENSE:
        print('hardware-init-xiao-ble-sense')
        time.sleep(1)

        led_pin = ("pwm0", 0)
        # PWM1 is mapped to GPIO pins using Zephyr .overlay
        buzzer_pin = ("pwm0", 1)

        # FIXME: use 52 Hz, and FIFO
        i2c = I2C("i2c0")
        lsm = lsm6ds.LSM6DS3(i2c, mode=lsm6ds.NORMAL_MODE_104HZ | 0b0000_1000) # 104Hz, FS=4g

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

            # FIXME: implement FIFO support, same/similar API as MPU6886
            ready = lsm.accel_data_ready()
            #print('acc ready', ready, count)
            if ready:
                xyz = lsm.get_accel_readings()
                x_values[count] = xyz[0]
                y_values[count] = xyz[1]
                z_values[count] = xyz[2]
                count += 1

            #count = mpu.get_fifo_count()
            if count >= hop_length:
                count = 0

                start = time.ticks_ms()

                # read data
                read_start = time.ticks_ms()

                #mpu.read_samples_into(chunk)
                #mpu.deinterleave_samples(chunk, x_values, y_values, z_values)

                read_duration = time.ticks_ms() - read_start

                process_start = time.ticks_ms()
                motion, brushing = processor.process(x_values, y_values, z_values)
                process_duration = time.ticks_ms() - process_start
        
                t = time.time()
                sm.next(t, motion, brushing)

                print('main-inputs', t, brushing, motion, sm.state)

                progress_state = sm.progress_state
                progress = int(100*(sm.brushing_time / sm.brushing_target_time))
                print('main-progress', sm.brushing_time, f'{progress}%', progress_state)

                # Update outputs
                await out.run(sm.state, progress_state)

                d = time.ticks_diff(time.ticks_ms(), start)
                print('main-iter-times', d, read_duration, process_duration)

            await asyncio.sleep_ms(1)
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

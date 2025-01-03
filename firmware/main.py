

import machine
from machine import Pin, I2C
from mpu6886 import MPU6886

import gc
import time
import math
import struct
import array
import asyncio

from core import StateMachine, OutputManager, DataProcessor, empty_array, clamp

# Free memory used by imports
gc.collect()


def _test_outputs_asyncio():

    buzzer_pin = machine.Pin(2, machine.Pin.OUT)
    led_pin = machine.Pin(19, machine.Pin.OUT)

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

    mpu = MPU6886(I2C(0, sda=21, scl=22, freq=100000))

    # Enable FIFO at a fixed samplerate
    mpu.fifo_enable(True)
    samplerate = 50
    mpu.set_odr(samplerate)

    hop_length = 50
    window_length = hop_length
    chunk = bytearray(mpu.bytes_per_sample*hop_length)

    x_values = empty_array('h', hop_length)
    y_values = empty_array('h', hop_length)
    z_values = empty_array('h', hop_length)

    # On M5StickC we need to set HOLD pin to stay alive when on battery
    hold_pin = machine.Pin(4, machine.Pin.OUT)
    hold_pin.value(1)

    # Internal LED on M5StickC PLUS2
    led_pin = machine.Pin(19, machine.Pin.OUT)

    # Buzzer
    buzzer_pin = machine.Pin(2)

    out = OutputManager(buzzer_pin=buzzer_pin, led_pin=led_pin)

    processor = DataProcessor()
    sm = StateMachine(time=time.time(), verbose=1)

    # TEST config
    sm.brushing_target_time = 60.0

    print('init-done')

    def main_task():
        print('main-start')

        while True:

            count = mpu.get_fifo_count()
            if count >= hop_length:
                start = time.ticks_ms()

                # read data
                read_start = time.ticks_ms()
                mpu.read_samples_into(chunk)
                mpu.deinterleave_samples(chunk, x_values, y_values, z_values)
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

            await asyncio.sleep_ms(100)
            #machine.lightsleep(100)

    asyncio.run(main_task())

if __name__ == '__main__':

    #test_outputs()

    main()

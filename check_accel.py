import sys
import time
sys.path.append("lib")


"""
Micropython module to monitor the acceleration value of the on-board LSM6DSTR3 accelerometer.
When the X acceleration value changes by more than THRESHOLD, flash both the on-board RGB LED
and an external LED triggered by the D0 pin going HIGH.
"""

from micropython import const
from time import ticks_us
from machine import I2C, Pin
import lsm6ds
from xiao_ble import BLUE_LED_PIN, RED_LED_PIN, GREEN_LED_PIN, D0_PIN

import asyncio
from asyncio import sleep_ms

blue_led = Pin(BLUE_LED_PIN, Pin.OUT, value=1)
green_led = Pin(GREEN_LED_PIN, Pin.OUT, value=1)
red_led = Pin(RED_LED_PIN, Pin.OUT, value=1)
external_white_led = Pin(D0_PIN, Pin.OUT, value=0)

DEFAULT_THRESHOLD = 10000
DEFAULT_DURATION = 100 # ms
NO_ARGS = const(())

def white_led_on():
    blue_led.value(0)
    green_led.value(0)
    red_led.value(0)
    external_white_led.value(1)

def white_led_off():
    blue_led.value(1)
    green_led.value(1)
    red_led.value(1)
    external_white_led.value(0)


async def accel_flasher(threshold=DEFAULT_THRESHOLD, duration=DEFAULT_DURATION):
    #flash_delay = Delay_ms(white_led_off, NO_ARGS, duration=duration)
    i2c = I2C("i2c0")
    lsm = lsm6ds.LSM6DS3(i2c, mode=lsm6ds.NORMAL_MODE_104HZ | 0b0000_1000) # 104Hz, FS=4g
    started = ticks_us()
    lastx = 0
    adr = lsm.accel_data_ready  # cache
    gar = lsm.get_accel_readings  # cache
    while True:
        while not adr():
            await sleep_ms(0)
        data = gar()
        now = ticks_us()
        dx = abs(data[0] - lastx)
        if dx > threshold:
            white_led_on()
            #flash_delay.trigger()
            print("*", end='')
        lastx = data[0]
        vals = [now-started, data[0], data[1], data[2], dx]
        print(','.join(map(str, vals)))
        await sleep_ms(1)

def set_global_exception():
    def handle_exception(loop, context):
        sys.print_exception(context["exception"])
        sys.exit()
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(handle_exception)

async def main():
    set_global_exception()

    await asyncio.gather(
        accel_flasher(threshold=10000, duration=50),
        #aiorepl.task()
    )

try:
    asyncio.run(main())
finally:
    try:
        time.sleep(3)
        asyncio.new_event_loop()
    except KeyboardInterrupt:
        raise

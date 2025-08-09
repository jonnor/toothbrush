
import time
from machine import PWM, Pin

# On XIAO BLE, pin 6, 26, 30 has RGB LED
led = Pin(("gpio0", 26), Pin.OUT)
led.value(1)

# PWM1 is mapped to GPIO pins using Zephyr .overlay
pwm = PWM(("pwm0", 1), freq=2000, duty_u16=0)

for x in range(0, 4):

    value = 0.5
    pwm.duty_u16(int(value*(2**16)))
    led.value(0)
    time.sleep(0.5)
    print(pwm)

    value = 0
    pwm.duty_u16(int(value*(2**16)))
    led.value(1)
    time.sleep(0.5)
    print(pwm)


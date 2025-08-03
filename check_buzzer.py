
import time
from machine import PWM, Pin

LEDS = [6, 26, 30]
for p in LEDS:
    led_pin = Pin(("gpio0", p), Pin.OUT)
    led_pin.value(0)

#buzzer_pin = Pin()
value = 1

for i in range(0, 30):

    pwm = PWM(("pwm0", i), freq=100, duty_u16=10000)
    print('t', pwm)

    for x in range(0, 4):

        value = 0
        pwm.duty_u16(int(value*(2**16)))
        time.sleep(0.5)

        value = 1
        pwm.duty_u16(int(value*(2**16)))
        time.sleep(0.5)


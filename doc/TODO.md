
# TODO

#### First PoC

- Clean up the ML pipeline for dataset prep
- Run unit-tests on device
- Implement tests for sad case
- Record more data. Get up to 8 or 10 sessions total.
- Setup quantitative evaluation of the time tracking.
Cut out random selections of time-sections.
Respect train/test folds

#### Zephyr version

Using XIAO BLE Sense NRF52840.
Initially with MicroPython, but with an aim to have pure C.

- Board. Assemble complete unit, dry mount in holder
- Holder. Make slightly smaller inner hole for toothbrush.
One type was a bit loose
- Holder. Let the "fingers" be two rows, on top of eachother while printing.
Make fingers a bit thinner. 1-2 mm
- Holder. A bit thicker on front / bigger component compartment.
Fillet the edges more.
- Holder. Add cutout bottom for USB-C magnet connector. 3-4 mm deep
- Holder. Try add in emlearn logo on bottom
- Holder. Try place components on a rigid carrier, so it can slide in, like a PCB
- XIAO. Include emlearn into the build as USER_C_MODULE
- XIAO. Implement FIFO support in LSM6 driver
- XIAO. Test entire toothbrush application


#### More features

Bluetooth connectivity

- Send prediction data over BLE. To phone
- Support sending sensor data over BLE.
For easier data collection.
- Make a small PoC application on phone that shows data

Power management

- Add battery voltage/power/percent tracking
- Enable sleeping, test battery life



# TODO

## Pipeline improvements

- Clean up the ML pipeline for dataset prep
- Implement tests for sad case
- Setup quantitative evaluation of the time tracking.
Note, some starts in the notebooks.
Cut out random selections of time-sections.
Respect train/test folds.

## Zephyr version

Using XIAO BLE Sense NRF52840.
Initially with MicroPython, but with an aim to have pure C.

#### Mini dataset v2

- Setup feature extraction.
Orientation after low-pass Elliptic. 2-5Hz bandpass energy. Total energy.
- Record at least 3 sessions
- Import data with features into Label Studio, do labeling
- Improve the notes in [data_collection.md](./data_collection.md)
- Record new demo video. Feature easy mounting onto toothbrush

#### Running in C

Related
https://github.com/jonnor/zephyr/blob/emlearn-sensor-readout/samples/modules/emlearn/sensor_reader/src/main.c

- Fixup the C feature extraction code.
- Support running C feature extraction in pipeline. CSV, gcc, and subprocess
- Setup/run evaluation pipeline on validation/testset on device. CSV
- Test live predictions on device

Later

- Port LSM6DS3 FIFO driver to C/Zephyr
- Use .npy instead of .csv
- Holder. Try add in emlearn logo on bottom

## Multi-participant dataset

Ref [data_collection.md](./data_collection.md)

- Get volunteers that are interested in participating
- Do a trial run at home
- Schedule a time to do the data recording


## More features

Bluetooth connectivity

- Send prediction data over BLE. To phone
- Support sending sensor data over BLE.
For easier data collection.
- Make a small PoC application on phone that shows data

Power management

- Add battery voltage/power/percent tracking
- Enable sleeping, test battery life


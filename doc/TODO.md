
# TODO

## Pipeline improvements

- Have steps for going from raw .npy data to trained model
Prepare the data for labeling with Label Studio. Output CSV. Copy example from har_trees
Merge in the labels. software.dataset.combine
Run har_train.py
- Add a Github Action which runs this
- Setup quantitative evaluation of the time tracking.
Note, some starts in the notebooks.
Cut out random selections of time-sections.
Respect train/test folds.
- Implement tests for state machine for sad case


## Zephyr version

Using XIAO BLE Sense NRF52840.
Initially with MicroPython, but with an aim to have pure C.

#### Mini dataset v2

- Get timeseries/video to work in LabelStudio
- Record at least 3 sessions
- Labeling all the sessions
- Test output with training pipeline
- Improve the notes in [data_collection.md](./data_collection.md)
- Record new demo video. Feature easy mounting onto toothbrush

#### Running in C

Related
https://github.com/jonnor/zephyr/blob/emlearn-sensor-readout/samples/modules/emlearn/sensor_reader/src/main.c

- Implement gravity separation using eml_iir
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


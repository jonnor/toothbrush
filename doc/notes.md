
# Sound design

https://onlinesequencer.net

Online Sequencer:923227:0 C5 1 43;2 D#5 1 43;1 D5 1 43;4 F5 1 43;5 F#5 1 43;6 G5 1 43;8 A5 1 43;9 B5 1 43;10 C6 1 43;12 D6 1 43;13 D#6 1 43;14 F6 1 43;17 C6 1 43;18 G5 1 43;19 E5 1 43;21 C5 4 43;:

# Hardware support

MicroPython on Zephyr for XIAO BLE Sense NRF52840

Need to have Zephyr 4.2 setup, and a virtualenv with `emlearn` installed.

In MicroPython repository

```
cd ports/zephyr/zephyrproject-4.2
source venv/bin/activate
west build --pristine -b xiao_ble/nrf52840/sense .. -- -DUSER_C_MODULES=/home/jon/projects/micropython/ports/zephyr/emlearn-micropython/src/micropython.cmake
```



With the `xiao-ble-sense-3` branch.
Includes MRs for

- https://github.com/micropython/micropython/pull/17679
- https://github.com/micropython/micropython/issues/17878

# Dataset

## sss

```
python -m software.dataset.combine \
    --data ./data/xiao-test-2/har_record \
    --samplerate 104 \
    --columns gyro_x,gyro_y,gyro_z,acc_x,acc_y,acc_z \
    --default-date 2024-09-20 \
    --out combined2.parquet
```

ss
```
python -m software.dataset.labeling_prepare --data data/xiao-test-2/har_record/ --out data/xiao-test-2/for_labeling --samplerate 104 --columns gyro_x,gyro_y,gyro_z,acc_x,acc_y,acc_z --default-date 2024-09-20
```

# Data


#### Dataset for toothbrushing activity using brush-attached and wearable sensors
https://www.sciencedirect.com/science/article/pii/S2352340921005321
https://data.mendeley.com/datasets/hx5kkkbr3j/1
https://prod-dcd-datasets-cache-zipfiles.s3.eu-west-1.amazonaws.com/hx5kkkbr3j-1.zip

Hussain et. al, 2021

Toothbrushing data for 120 sessions performed by 22 participants (11 males, 11 females).
The data was collected using two IMU devices from Mbientlab Inc.
One device was attached to the brush handle, while the other device was used as wearable (wristwatch on the brushing hand).
The participants brush their teeth for around two minutes in each session following a pre-given sequence.
16 sub-activities, corresponding to location being brushed, done in pre-defined order.

! no explicit labels.

235 MB total.

#### UMATBrush
https://www.sciencedirect.com/science/article/pii/S2352340925007048
https://figshare.com/articles/dataset/UMATBrush_Traces/28955756
October 2025.

F.J. González-Cañete, E. Casilari
Departamento de Tecnología Electrónica, Telecommunication Research Institute (TELMA), Universidad de Málaga

Dataset characteristics

- 4 experimental subjects during their normal life
- using 3 commercial smartwatches
- Over 5 hours of toothbrushing activity, and over 140 toothbrushing sessions
- long periods of monitoring of the subjects during their daily lives, over 200 hours in total
- binary labelled as either corresponding or not to a toothbrushing session
- Tri-axial accelerometer, no gyro
- Samplerate approximately 100 Hz

2.92 GB download.
Stored as .CSV files.

Table 1. Existing available datasets with sensor data collected with wrist-worn sensors during toothbrushing activities.
Lists 13 datasets, however vast majority are general Activities of Daily Living (ADL).

Reports toothbrushing power being typically around 4-5Hz.

Notes limited number of participants.
Expanding the participant pool to cover different age groups and dental conditions would help
improve the representativeness and applicability of the dataset.


## Hardware

- Needs accelerometer/IMU.
- And some way of notifying user. LED and/or buzzer.

For prototyping the M5StickC can be used.
A bit bulky, but workable.

Then the `dml20m` hardware would be used to actually demonstrate the 1 USD TinyML concept.

## References

#### Development and evaluation of the “Toothbrushing Timer with Information on Toothbrushes” application: A prospective cohort pilot study
https://pmc.ncbi.nlm.nih.gov/articles/PMC10728532/

A mobile phone app to help users ensure appropriate toothbrushing time and learn about the beneficial characteristics of toothbrushes

#### Separating Movement and Gravity Components in an Acceleration Signal and Implications for the Assessment of Human Daily Physical Activity

We aimed to evaluate five different methods (metrics) of processing
acceleration signals on their ability to remove the gravitational component of acceleration during standardised mechanical
movements and the implications for human daily physical activity assessment.

Euclidian norm minus one (ENMO),
Euclidian norm of the high-pass filtered signals (HFEN),
HFEN plus Euclidean norm of low-pass filtered signals minus 1 g (HFEN+)


#### Gravity subtraction

Should establish the initial gravity vector for calibration.
When standing in holder.

To leave out the gravity vector from the accelerometer value, you need to rotate the accelerometer vector to the earth frame using a rotation matrix or quaternion which can be calculated from accelerometer, gyroscope, and magnetometer.
After you rotate the vector to the earth frame you can subtract the (0, 0, g)^T vector to take out the gravity.
You can rotate the resulted vector to the body frame again by multiplying the inverse matrix of the rotation matrix that you have used before

https://math.stackexchange.com/a/1746199/1519080 
Python/numpy code

https://howtomechatronics.com/tutorials/arduino/how-to-track-orientation-with-arduino-and-adxl345-accelerometer/
https://www.allaboutcircuits.com/technical-articles/how-to-interpret-IMU-sensor-data-dead-reckoning-rotation-matrix-creation/

Freescale AN3461: Tilt Sensing Using a Three-Axis Accelerometer

https://josejuansanchez.org/android-sensors-overview/gravity_and_linear_acceleration/README.html
Simple java code using 

ahrs Python library has excellent explanations of the various methods.
Using different combinations of accel/gyro/magnetometer.
https://ahrs.readthedocs.io/en/latest/filters.html
https://ahrs.readthedocs.io/en/latest/filters/tilt.html
https://ahrs.readthedocs.io/en/latest/filters/complementary.html


#### Gravity estimation using lowpass

A Public Domain Dataset for Human Activity Recognition Using Smartphones. Anguita et al (2013)

> The gravitational force is assumed to have only low frequency components,
> therefore we found from the experiments that 0.3 Hz was an optimal corner frequency for a constant gravity signal.
! Order not specified. Their other filter was 3rd order.

In "A benchmark for domain adaptation and generalization in smartphone-based human activity recognition"
https://www.nature.com/articles/s41597-024-03951-4

> The Acc can only sense the total acceleration, so some procedures must be performed to separate the body and gravity acceleration.
> Several methods described in the literature are suitable for this task.
> However, the most common involves applying a high-pass Butterworth filter of low order (e.g., order 3) with a cutoff frequency below 1 Hz

In "Frequency Domain Approach for Activity Classification using Accelerometer"
Chung et al, 2028

> Elliptical IIR High Pass filter (HPF) of seventh order with 0.5 Hz cutoff frequency
was used to separate the bodily accelerations from the gravity accelerations.

## Existing products

There are timers.
Especially targetting kids.
Some are using an hourglass principle using colored oil.

Some are electronic using light to indicate done.

Braun has "Genius X" series.
https://www.oralb.co.uk/en-gb/product-collections/genius-x
An electric toothbrush with "Artificial Intelligence".
Tracks where you brush in your mouth.

## Ideas

How to get people to actually do their toothbrushing?
Touge in cheek approaches.

- Tooth-a-ma-gotchi. It will starve if you do not brush enough
- Shamification-gamification. If you do not brush enough, it will tell your mother/partner/dentist. Communicate via BLE to phone
- Strava for your teeth. Posts to social media bragging about the "course" that you completed

## Asides

#### Adverserial usage

If someone is trying to fool the device that they are actually brushing their teeth,
can we actually separate that from actual toothbrushing?
Like vigorous shaking. At approximately the right periodicity.
At approximately the right angle even?
Probably not...
But including some roughly similar data from other semi-energetic activities might be a good check for robustness.


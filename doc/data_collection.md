
# Data collection



## Overall design

Ideally one would want to have multiple persons perform the activities,
and test/train splits would be split on subject.
Number of subjects would preferably be 10+.

The next best thing is to have one person record separate sessions,
and test/train splits are done using the session.
Must have at least 4 sessions. Ideally would want 10+ sessions.

Each brushing session should be around 3 minutes long, with around 2 minutes of actively brushing teeth.
The rest of time is filled with "pauses" with activities which may plausibly appear
in and round the activity of brushing ones teeth.

### Protocol

Before session

- Setup device with har_record.py from har_trees emlearn-micropython example.
- Update the device RTC. `mpremote rtc --set`

For each session

- Start video recording on mobile phone
- Start data recording by holding the M5 button. Light should turn red
- Start with toothbrush standing stationary on surface/stand. 5 seconds
- Tap toothbrush 5 times onto flat service (timesync marker)
- Brush teeth like normally
- Take a number of pauses of 5-10 seconds duration. Do some pause activity (see below)
- After around 3 minutes, can stop
- Stop data recording
- Stop video recording

### Example of pause activities

- Swap toothbrush between hands.
- Hold toothbrush completely still in mouth
- Take toothbrush out of mouth to talk
- Put toothbrush down on surface, pick up again
- Swing arms down
- Walk around with toothbrush in hand
- Stretch with arms overhead
- Drop the toothbrush in the sink
- Rinse the toothbrush
- Put more toothpaste on toothbrush
- Other (subject decides)
- Check something on the face in the mirror
- Talk to someone
- Drink water from tap
- Turn tap off/on
- Inspect/poke at teeth


### Other activity data

NOTE: not used

### Example of other activities

- Walking around indoor, toothbrush in hand
- Walking in stairs, toothbrush in hand
- Playing swords with toothbrush
- Sitting down/up, toothbrush in hand
- Dropping toothbrush onto surface
- Throwing toothbrush onto surface
- Toothbrush lying on surface
- Throwing toothbrush into the air, flipping
- Tapping on toothbrush
- Inspecting toothbrush
- Walking with toothbrush in backpack
- Driving with X in backpack
- Biking with X in backpack

### Potential confusors

Things that have similar data characteristics.
Especially those that also can be expected to co-occur in ordinary real-world usage.

Periodic alternating motion with 2-5 Hz.
Fast walk / jogging / running?

## Video recording

Use "Open Camera" on Andoid phone.

Video settings
```
Resolution                  720p
Orientation.                Portrait
Framerate.                  30 fps
Format.                     MPEG4 H264
Bitrate.                    3 Mbps
```

Estimated 25 MB per 1 minute, 75 MB pre 3 minute session.
Still just a few GB for 20 sessions.

Going down to 1 Mbps gave noticably worse results.

! check that this open nicely in Label Studio.

## Dataset pipeline structure

```
Raw data:

    Session metadata            /sessions.csv
    Sensor data.                /har_record/$session/*.npy
    Video from phone.           /videos/$session/X.mkv

For labeling

    Video. One video (URL) per session
    Timeseries. One CSV per session
    Labeling list. CSV/JSON with one row per session, URLs to video and timeseries
    Annotation template

After labeling

    Labels from Label Studio.   /labels/project.csv

After combining

    Combined data               /combined.parquet
```

## Session metadata

```
participant
device
location
brush
```


## Video access

! videos need to be on a URL to be accessible.
Can be localhost if using Label Studio locally?

Not all participants may allow open access to the video.
Generally this should be something authenticated.
Might need to use pre-signed / anonymous URLs.

How to identify data in the Label Studio output?
Session identifiers should be in the video/timeseries URLs

# Aligning / time syncronization

Open video, find location of the first sync (in seconds)

??? Where does the time syncronization happen
Would want to do before


https://labelstud.io/templates/timeseries_audio_video
! Must set frameRate



# Labeling notes

Labeling precision target.
Better than 1 second.
Not needed as good as 100 ms.

# Video notes

Used this to get a more compressed video file.
15 MB per 3 minutes.

Recommendations by Label Studio
https://labelstud.io/tags/video#Video-format
! also specify -r 30 for constant-frame-rate

ffmpeg -i input.avi -c:a copy -vf "scale=-2:720" -c:v libx264 -pix_fmt yuv420p -crf 23 output.mkv

ffmpeg -ss 00:03:00 -i input.mkv -c copy output.mp4

Download links in Google Drive

https://drive.google.com/uc?export=download&id=FILEID

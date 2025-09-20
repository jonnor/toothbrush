
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


# Labeling notes

Labeling precision target.
Better than 1 second. Not needed as good as 100 ms.

ffmpeg -i input.avi -c:a copy -vf "scale=-2:720" -c:v libx264 -pix_fmt yuv420p -crf 23 output.mkv

ffmpeg -ss 00:03:00 -i input.mkv -c copy output.mp4

Download links in Google Drive

https://drive.google.com/uc?export=download&id=FILEID

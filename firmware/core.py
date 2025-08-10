
"""
Toothbrush timer using accelerometer and machine learning
"""

import math
import array
import gc
import time
import asyncio

import emlearn_trees
import timebased

def empty_array(typecode, length, value=0):
    return array.array(typecode, (value for _ in range(length)))

def median(values):
    L = len(values)
    if L == 0:
        raise ValueError('Input empty')
    if L == 1:
        return values[0]

    ordered = sorted(values)
    is_odd = (L % 2) == 1
    if is_odd:
        out = ordered[L//2]
    else:
        l = ordered[(L//2)-1]
        h = ordered[(L//2)-0]
        out = (l+h)/2

    #print('median', out, values)
    return out 

def buffer_push_end(values : list, new, length):
    assert len(values) <= length
    # NOTE: mutates values
    if len(values) == length:
        values = values[1:]
    values.append(new)
    assert len(values) <= length
    return values


class StateMachine:

    SLEEP = 'sleep'
    IDLE = 'idle'
    BRUSHING = 'brushing'
    DONE = 'done'
    FAILED = 'failed'

    def __init__(self,
            time=0.0,
            prediction_filter_length=5,
            idle_time_max=30.0,
            verbose=2,
        ):

        # config
        self.brushing_target_time = 120.0
        self.done_wait_time = 1.0
        self.fail_wait_time = 1.0
        self.idle_time_max = idle_time_max
        self.brushing_threshold = 0.6
        self.not_brushing_threshold = 0.4
        self.motion_threshold = 0.3
        self.brushing_started_time = 10.0
        self.prediction_filter_length = prediction_filter_length
        self.verbose = verbose

        # state
        self.state = self.SLEEP
        self.state_enter_time = time
        self.last_time = time
        self.motion_history = [0.0] * self.prediction_filter_length
        self.brushing_history = [0.0] * self.prediction_filter_length
        self.brushing_time = 0.0 # how long active

        self._state_functions = {
            self.SLEEP: self.sleep_next,
            self.IDLE: self.idle_next,
            self.BRUSHING: self.brushing_next,
            self.DONE: self.done_next,
            self.FAILED: self.failed_next,
        }

    def _get_predictions(self):
        # return filtered predictions
        m = median(self.motion_history)
        b = median(self.brushing_history)
        return m, b

    def _update_predictions(self, motion, brushing):
        # update filter states
        l = self.prediction_filter_length
        self.motion_history = buffer_push_end(self.motion_history, motion, l)
        self.brushing_history = buffer_push_end(self.brushing_history, brushing, l)
        # return filter outputs
        return self._get_predictions()

    @property
    def progress_state(self):
        # Discretized states for how much progress we have made
        n_states = 4
        progress = clamp(self.brushing_time / self.brushing_target_time, 0.0, 0.99)
        state = int(progress * n_states)
        return state

    def next(self, time, motion, brushing):
        # Handle logic common to all states,
        # and then delegate to current state
        motion, brushing = self._update_predictions(motion, brushing)
        kwargs = dict(time=time, motion=motion, brushing=brushing)
        func = self._state_functions[self.state]
        next_state = func(**kwargs)
        if not next_state is None:
            if self.verbose >= 1:
                print('sm-transition', self.state, next_state)
            self.state = next_state
            self.state_enter_time = time
        self.last_time = time

    # State functions
    def sleep_next(self, motion, **kwargs):
        # reset accumulated time
        self.brushing_time = 0.0

        if self.verbose >= 2:
            print('sm-sleep-next', motion)

        if motion > self.motion_threshold:
            return self.IDLE

    def idle_next(self, time, brushing, **kwargs):
        is_brushing = brushing > self.brushing_threshold
        since_enter = time - self.state_enter_time

        if self.verbose >= 2:
            print('sm-idle-next', is_brushing, since_enter)

        if is_brushing:
            return self.BRUSHING

        if since_enter > self.idle_time_max:
            if self.brushing_time > self.brushing_started_time:
                return self.FAILED
            else:
                # no-one actually started brushing
                return self.SLEEP

    def brushing_next(self, time, brushing, **kwargs):
        is_idle = brushing < self.not_brushing_threshold
        since_last = time - self.last_time

        if self.verbose >= 2:
            print('sm-brushing-next', brushing, is_idle, since_last)

        if is_idle:
            return self.IDLE
        else:
            # still brushing
            self.brushing_time += since_last
            if self.brushing_time > self.brushing_target_time:
                return self.DONE

    def done_next(self, time, **kwargs):
        since_enter = time - self.state_enter_time

        if self.verbose >= 2:
            print('sm-done-next', since_enter)

        if since_enter >= self.done_wait_time:
            self.brushing_history = [0.0] * self.prediction_filter_length
            return self.SLEEP

    def failed_next(self, time, **kwargs):
        since_enter = time - self.state_enter_time

        if self.verbose >= 2:
            print('sm-failed-next', since_enter)

        if since_enter >= self.fail_wait_time:
            self.brushing_history = [0.0] * self.prediction_filter_length
            return self.SLEEP



def mean(arr):
    m = sum(arr) / float(len(arr))
    return m

def magnitude_3d(x, y, z):
    r2 = x**2 + y**2 + z**2
    r = math.sqrt(r2)
    return r

def euclidean(a, b):
    s = 0.0
    assert len(a) == len(b)
    for av, bv in zip(a, b):
        s += (av-bv)**2

    return math.sqrt(s)

def clamp(value, lower, upper) -> float:
    v = value
    v = min(v, upper)
    v = max(v, lower)
    return v

def energy_xyz(xs, ys, zs, orientation):
    assert len(xs) == len(ys)
    assert len(ys) == len(zs)

    xo, yo, zo = orientation
    
    # compute RMS of magnitude, after having removed orientation
    s = 0.0
    for i in range(len(xs)):
        m = magnitude_3d(xs[i]-xo, ys[i]-yo, zs[i]-zo)
        s += m**2

    rms = math.sqrt(s)
    return rms

def dirname(path, sep='/'):
    parts = path.split(sep)
    dirname = sep.join(parts[:-1])
    return dirname


class DataProcessor():

    def __init__(self):

        # Config
        self.max_motion_energy = 3000

        # State
        here = dirname(__file__)
        if here == '':
            here = '.'
        model_path = here + '/brushing.trees.csv'
        self.brushing_model = self.load_model(model_path)

        features_typecode = timebased.DATA_TYPECODE
        n_features = timebased.N_FEATURES
        self.features = array.array(features_typecode, (0 for _ in range(n_features)))
    
        self.brushing_outputs = array.array('f', (0 for _ in range(2)))


    def load_model(self, model_path):

        # Load a CSV file with the model
        model = emlearn_trees.new(10, 1000, 10)
        with open(model_path, 'r') as f:
            emlearn_trees.load_model(model, f)

        return model

    def process(self, xs, ys, zs):
        """
        Analyze the accelerometers sensor data, to determine what is happening
        """

        # find orientation
        orientation_start = time.ticks_ms()
        orientation_xyz = mean(xs), mean(ys), mean(zs)
        mag = magnitude_3d(*orientation_xyz)
        norm_orientation = [ c/mag for c in orientation_xyz ]

        energy = energy_xyz(xs, ys, zs, orientation_xyz)    

        # dummy motion classifier, heuristics
        motion = clamp(energy / self.max_motion_energy, 0.0, 1.0)
   
        orientation_duration = time.ticks_ms() - orientation_start

        # brushing classifier
        # compute features
        features_start = time.ticks_ms()
        ff = timebased.calculate_features_xyz((xs, ys, zs))
        for i, f in enumerate(ff):
            self.features[i] = int(f)
        features_duration = time.ticks_ms() - features_start

        # run model
        predict_start = time.ticks_ms()
        self.brushing_model.predict(self.features, self.brushing_outputs)
        brushing = self.brushing_outputs[1]
        predict_duration = time.ticks_ms() - predict_start

        #print('comp', features_duration, predict_duration)
        # Only maintain a sane level of decimals for probabilities
        motion = round(motion, 2)
        brushing = round(brushing, 2)
        return motion, brushing



# Copy/paste from 
progress_1 = """0 C5 1 43;2 D#5 1 43;1 D5 1 43"""
progress_2 = """0 F5 1 43;1 F#5 1 43;2 G5 1 43"""
progress_3 = """0 A5 1 43;1 B5 1 43;2 C6 1 43"""
progress_4 = """0 D6 1 43;1 D#6 1 43;2 F6 1 43"""
success_song = """0 C6 1 43;1 G5 1 43;2 E5 1 43;4 C6 4 43"""
fail_song = """3 D4 4 43;0 C5 2 43"""

class OutputManager():

    def __init__(self, led_pin, buzzer_pin, note_step_ms=30):

        # dynamic import, since machine.PWM is not available on Unix
        from machine import PWM

        self.buzzer_pin = buzzer_pin
        self.led_pin = led_pin
        # XXX: on M5Stick PLUS2 using PWM in the audible range causes buzzer to sound =/
        self.led_pwm = PWM(self.led_pin, freq=100000, duty_u16=0)
        self.note_step_ms = note_step_ms

        self.last_state = None
        self.last_progress = None

    async def _play_song(self, notes):

        # NOTE: dynamic import of dependency
        # since it is not portable to Unix (machine.Pin not defined)
        from buzzer_music import music

        song = music(notes, pins=[self.buzzer_pin], looping=False)
        while True:
            running = song.tick()
            if not running:
                break
            await asyncio.sleep_ms(self.note_step_ms)    

    async def run(self, state : str, progress_state : int):

        if state == self.last_state and progress_state == self.last_progress:
            return

        led_value = 0.0
        if state == 'brushing':
            led_value = 0.5
        elif state == 'idle':
            led_value = 0.02
        else:
            pass
 
        led_duty = int(led_value*(2**16))
        self.led_pwm.duty_u16(led_duty)

        if state == 'sleep':
            pass
        elif state == 'idle':
            pass
        elif state == 'brushing':
            songs = [
                progress_1,
                progress_2,
                progress_3,
                progress_4,
            ]
            s = songs[progress_state]
            await self._play_song(s)

        elif state == 'done':
            await self._play_song(success_song)

        elif state == 'failed':
            await self._play_song(fail_song)

        else:
            raise ValueError(f"Unsupported state {state}")
    
        self.last_state = state
        self.last_progress = progress_state


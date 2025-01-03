
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
        ):

        # config
        self.brushing_target_time = 120.0
        self.done_wait_time = 1.0
        self.fail_wait_time = 1.0
        self.idle_time_max = idle_time_max
        self.brushing_threshold = 0.6
        self.not_brushing_threshold = 0.4
        self.motion_threshold = 0.3
        self.prediction_filter_length = prediction_filter_length

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

    def next(self, time, motion, brushing):
        # Handle logic common to all states,
        # and then delegate to current state
        motion, brushing = self._update_predictions(motion, brushing)
        kwargs = dict(time=time, motion=motion, brushing=brushing)
        func = self._state_functions[self.state]
        next_state = func(**kwargs)
        if not next_state is None:
            print('transition', self.state, next_state)
            self.state = next_state
            self.state_enter_time = time
        self.last_time = time

    # State functions
    def sleep_next(self, motion, **kwargs):
        # reset accumulated time
        self.brushing_time = 0.0

        print('sleep-next', motion)

        if motion > self.motion_threshold:
            return self.IDLE

    def idle_next(self, time, brushing, **kwargs):
        is_brushing = brushing > self.brushing_threshold
        since_enter = time - self.state_enter_time

        print('idle-next', is_brushing, since_enter)

        if is_brushing:
            return self.BRUSHING

        if since_enter > self.idle_time_max:
            if self.brushing_time > 10.0:
                return self.FAILED
            else:
                # no-one actually started brushing
                return self.SLEEP

    def brushing_next(self, time, brushing, **kwargs):
        is_idle = brushing < self.not_brushing_threshold

        if is_idle:
            return self.IDLE
        else:
            # still brushing
            since_last = time - self.last_time
            self.brushing_time += since_last
            if self.brushing_time > self.brushing_target_time:
                return self.DONE

    def done_next(self, time, **kwargs):
        since_enter = time - self.state_enter_time
        if since_enter >= self.done_wait_time:
            return self.SLEEP

    def failed_next(self, time, **kwargs):
        since_enter = time - self.state_enter_time
        if since_enter >= self.fail_wait_time:
            return self.SLEEP



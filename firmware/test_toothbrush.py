
from core import StateMachine

def run_scenario(sm, trace, default_dt = 0.1):

    capture_outputs = ['state', 'brushing_time']

    time = 0.0
    for row in trace:
        # inputs
        dt = row.get('dt', default_dt)
        time += dt
        mp = row['mp']
        if mp is None:
            mp = 0.5 # TODO: randomize

        # run
        inputs = dict(time=time, motion=mp, brushing=row['bp'])
        sm.next(**inputs)

        outputs = { o: getattr(sm, o) for o in capture_outputs }
        yield row, inputs, outputs

def check_expectations(row, outputs):

    # check expectations
    expect_state = row.pop('s')
    state = outputs['state']
    assert state == expect_state, (state, expect_state)

    expect_brushing_time = row.pop('bt', None)
    brushing_time = round(outputs['brushing_time'], 3)
    if expect_brushing_time is not None:
        e = round(expect_brushing_time, 3)
        assert brushing_time == e, (brushing_time, e)


def test_states_basic_happy():
    # check that we can reach the DONE/success state

    # make effect of median filter present but short
    sm = StateMachine(prediction_filter_length=3)
    sm.brushing_target_time = 2.0 # make it quick to hit target
    sm.done_wait_time = 1.0

    assert sm.state == sm.SLEEP

    LOW = 0.1
    HIGH = 0.8
    X = None # dont-care

    # expected outputs (s: sm.state), and inputs (everything else)
    trace = [
        dict(mp=LOW, bp=LOW, s=sm.SLEEP),
        dict(mp=LOW, bp=LOW, s=sm.SLEEP),
        # medial filter should reject short states
        dict(mp=HIGH, bp=LOW, s=sm.SLEEP),
        dict(mp=LOW, bp=LOW, s=sm.SLEEP),
        # longer case should transition
        #dict(mp=HIGH, bp=LOW, s=sm.SLEEP),
        dict(mp=HIGH, bp=LOW, s=sm.IDLE),
        # if not brushing, should stay idle
        dict(mp=X, bp=LOW, s=sm.IDLE),
        dict(mp=X, bp=LOW, s=sm.IDLE),
        dict(mp=X, bp=LOW, s=sm.IDLE),
        # if starting brushing, should count the time spent
        dict(mp=X, bp=HIGH, s=sm.IDLE),
        dict(mp=X, bp=HIGH, s=sm.BRUSHING, bt=0.0),
        dict(mp=X, bp=HIGH, s=sm.BRUSHING, bt=0.1),
        dict(mp=X, bp=HIGH, s=sm.BRUSHING, bt=0.2),
        # if not brushing, should go to idle
        dict(mp=X, bp=LOW, s=sm.BRUSHING, bt=0.3),
        dict(mp=X, bp=LOW, s=sm.IDLE, bt=0.3),
        dict(mp=X, bp=LOW, s=sm.IDLE, bt=0.3),
        # if starting brushing again, should continue counting
        dict(mp=X, bp=HIGH, s=sm.IDLE),
        dict(mp=X, bp=HIGH, s=sm.BRUSHING, bt=0.3),
        dict(mp=X, bp=HIGH, s=sm.BRUSHING, bt=0.4),
        # if brushing for long enough, will eventually get done
        dict(mp=X, bp=HIGH, s=sm.BRUSHING, dt=1.0, bt=1.4),
        dict(mp=X, bp=HIGH, s=sm.DONE, dt=1.0, bt=2.4),
        # done will automatically transition to sleep
        dict(mp=X, bp=HIGH, s=sm.DONE, dt=0.5),
        dict(mp=X, bp=HIGH, s=sm.SLEEP, dt=0.6),
    ]

    gen = run_scenario(sm, trace)
    for row, inputs, outputs in gen:
        print('next-ran', inputs, outputs, row)
        check_expectations(row, outputs)

def test_states_basic_sad():
    # check that we can reach FAIL state

    # make effect of median filter present but short
    sm = StateMachine(prediction_filter_length=3)
    sm.brushing_target_time = 2.0 # make it quick to hit target
    sm.done_wait_time = 1.0

    assert sm.state == sm.SLEEP

    LOW = 0.1
    HIGH = 0.8
    X = None # dont-care

    # expected outputs (s: sm.state), and inputs (everything else)
    trace = [
    ]

    gen = run_scenario(sm, trace)
    for row, inputs, outputs in gen:
        print('next-ran', inputs, outputs)
        check_expectations(row, outputs)


def main():
    test_states_basic_happy()
    #test_states_basic_sad()

if __name__ == '__main__':
    main()


import math
import array
import gc
import time

import npyfile

from core import StateMachine, DataProcessor, empty_array

class GravitySplitter():

    def __init__(self, samplerate, lowpass_cutoff=0.5):

        rc = 1.0/(2*3.14*lowpass_cutoff)
        dt = 1.0/samplerate
        self.lowpass_alpha = rc / (rc + dt)

        self.gravity = None
        self.motion = array.array('f', [0, 0, 0])

    def process(self, xyz):
        assert len(xyz) == 3, xyz

        if self.gravity is None:
            # jump straigth to it, to avoid slow ramp-in
            self.gravity = array.array('f', xyz)
        
        a = self.lowpass_alpha
        for i in range(len(xyz)):
            self.gravity[i] = (a * self.gravity[i]) + ((1.0 - a) * xyz[i])
            self.motion[i] = xyz[i] - self.gravity[i]



def read_data_file(path,
        chunk_length,
        n_features=3,
        skip_samples=0,
        limit_samples=None):

    with npyfile.Reader(path) as data:

        # Check that data is expected format: files x timesteps x features, int16
        shape = data.shape
        assert len(shape) == 2, shape
        assert shape[1] == n_features, shape
        assert data.itemsize == 2, data.itemsize
        assert data.typecode == 'h', data.typecode

        # Read one chunk at a time
        sample_count = 0

        chunk_size = n_features*chunk_length
        data_chunks = data.read_data_chunks(chunk_size, offset=n_features*skip_samples)

        for arr in data_chunks:
            yield arr

            sample_count += 1
            if limit_samples is not None and sample_count > limit_samples:
                break


def process_file(path):

    samplerate = 50
    hop_length = 50
    window_length = hop_length

    x_values = empty_array('h', hop_length)
    y_values = empty_array('h', hop_length)
    z_values = empty_array('h', hop_length)

    p = DataProcessor()
    sm = StateMachine(time=0.0)

    n_axes = 3
    sample_no = 0
    for xyz in read_data_file(path, chunk_length=hop_length):
        t = (1.0/samplerate) * sample_no
        n_samples = len(xyz) // n_axes
        for i in range(n_samples):
            x_values[i] = xyz[(i*3)+0]
            y_values[i] = xyz[(i*3)+1]
            z_values[i] = xyz[(i*3)+2]

        motion, brushing = p.process(x_values, y_values, z_values)
        sm.next(t, motion, brushing)
        sample_no += n_samples

        yield t, motion, brushing, sm.state, sm.brushing_time


def test_process_happy():

    # FIXME: select a file with test data for success scenario
    data_path = ''
    for out in process_file(data_path):
        t = out[1]
        state = out[4]
        if state == 'done':
            done_time = t
            break

    expect_done = 300
    assert done_time >= expect_done - 10
    assert done_time <= expect_done + 10

def main():

    import sys

    total_brushing_time = 0.0

    data_path = sys.argv[1]
    out_path = sys.argv[2]
    out_columns = ['time', 'motion', 'brushing', 'state', 'brushing_time']
    endline = '\n'
    delim = ','

    with open(out_path, 'w') as out:

        # Write header
        for i, c in enumerate(out_columns):
            out.write(c)
            if i != len(out_columns)-1:
                out.write(delim)
        out.write(endline)

        for res in process_file(data_path):
            t, motion, brushing, state, brushing_time = res
            print('toothbrush-state-out', res)

            assert len(res) == len(out_columns)
            for i, v in enumerate(res):
                out.write(str(v))
                if i != len(res)-1:
                    out.write(delim)
            out.write(endline)

            total_brushing_time = max(brushing_time, total_brushing_time)

        print('toothbrush-done', total_brushing_time)

if __name__ == '__main__':
    main()

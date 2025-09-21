
import pandas
import numpy

from scipy.signal import iirfilter, sosfiltfilt

def create_lowpass(samplerate, cutoff=0.5, order=4):
    nyquist = samplerate / 2
    normalized_cutoff = cutoff / nyquist
    
    # NOTE: in theory an Elliptic filter would allow sharper transition
    sos = iirfilter(order, normalized_cutoff, 
                   btype='lowpass', ftype='butter', output='sos')

    return sos
    

def compute_tilt(gravity_normalized):
    np = numpy

    gx = gravity_normalized[:, 0]
    gy = gravity_normalized[:, 1]
    gz = gravity_normalized[:, 2]
    
    pitch = np.degrees(np.arctan2(gx, np.sqrt(gy**2 + gz**2)))
    roll = np.degrees(np.arctan2(gy, gz))
    
    return pitch, roll

def apply_lowpass(df : pandas.DataFrame, lowpass,
           metric='acc', axes=['x', 'y', 'z'],
           orientation_prefix='orientation_',
           gravity_prefix='gravity_',
           motion_prefix='linear_acc_',
        ):

    out = df.copy()
    for axis in axes:
        in_column = f'{metric}_{axis}'
        signal = df[in_column]

        # XXX: this assumes regularly spaced time-series
        gravity = sosfiltfilt(lowpass, signal)
        linear = signal - gravity
        out[gravity_prefix+axis] = gravity
        out[motion_prefix+axis] = linear


    # Add normalized orientation vector
    gravity_columns = [ gravity_prefix+a for a in axes ]
    gravity_vector = out[gravity_columns]

    orientation_columns = [ orientation_prefix+a for a in axes ]
    orientation = gravity_vector / numpy.linalg.norm(gravity_vector, axis=0)
    print(orientation)
    for c, g in zip(orientation_columns, gravity_columns):    
        out[c] = orientation[g]

    # Add tilt/roll
    # NOTE: yaw cannot be estimated from accelerometer alone
    pitch, roll = compute_tilt(orientation.values)
    out['pitch'] = pitch
    out['roll'] = roll

    return out


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
    
class GravityEstimatorComplimentary:
    """Estimate gravity vector from IMU data using complementary filter"""
    
    def __init__(self, alpha=0.98, sr=100):
        """
        alpha: complementary filter weight (0.95-0.99 typical)
        sr: Hz
        """
        self.alpha = alpha
        self.dt = 1.0 / sr
        self.gravity = numpy.array([0, 0, 1.0])  # Initial gravity (normalized)
        
    def update(self, accel, gyro):
        """
        accel: [ax, ay, az] in m/s^2 or g's
        gyro: [gx, gy, gz] in rad/s
        Returns: gravity vector (normalized)
        """
        # Normalize accelerometer
        accel_norm = accel / numpy.linalg.norm(accel)
        
        # Integrate gyro to predict gravity rotation
        # Use NEGATIVE gyro (body rotates one way, gravity vector rotates opposite)
        angle = numpy.linalg.norm(gyro) * self.dt
        if angle > 1e-6:  # avoid division by zero
            axis = -gyro / numpy.linalg.norm(gyro)  # NEGATIVE here
            # Rodrigues' rotation formula
            K = numpy.array([[0, -axis[2], axis[1]],
                         [axis[2], 0, -axis[0]],
                         [-axis[1], axis[0], 0]])
            R = numpy.eye(3) + numpy.sin(angle) * K + (1 - numpy.cos(angle)) * K @ K
            gravity_pred = R @ self.gravity
        else:
            gravity_pred = self.gravity
            
        # Complementary filter: fuse prediction with measurement
        self.gravity = self.alpha * gravity_pred + (1 - self.alpha) * accel_norm
        self.gravity = self.gravity / numpy.linalg.norm(self.gravity)
        
        return self.gravity.copy()

def apply_complimentary(df : pandas.DataFrame, filter,
           gyro_columns=['gyro_x', 'gyro_y', 'gyro_z'],
           accelerometer_columns=['acc_x', 'acc_y', 'acc_z'],
           orientation_prefix='orientation_',
            axes=['x', 'y', 'z'],
           gravity_prefix='gravity_',
           motion_prefix='linear_acc_',
        ):

    orientation_columns = [ orientation_prefix+a for a in axes ]
    
    out = df.copy()
    # NOTE: assumes sorted by time, regularly spaced time-series
    for idx, row in df.iterrows(): 
        acc_values = row[accelerometer_columns].values
        gyro_values = row[gyro_columns].values
        #print(gyro_values)
        gyro_rad = gyro_values * (numpy.pi / 180.0) # to radians
        filter.update(acc_values, gyro_rad)
        out.loc[idx, orientation_columns] = filter.gravity # Is already normalized

    # Add linear acceleration
    motion_columns = [ motion_prefix+a for a in axes ]
    for acc, orient, motion in zip(accelerometer_columns, orientation_columns, motion_columns):
        out[motion] = out[acc] - out[orient]

    # Add tilt/roll
    # NOTE: yaw cannot be estimated from accelerometer alone
    orientation = out[orientation_columns]
    pitch, roll = compute_tilt(orientation.values)
    out['pitch'] = pitch
    out['roll'] = roll

    return out


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
    orientation = gravity_vector / numpy.linalg.norm(gravity_vector, axis=1, keepdims=True)
    print(orientation)
    for c, g in zip(orientation_columns, gravity_columns):    
        out[c] = orientation[g]

    # Add tilt/roll
    # NOTE: yaw cannot be estimated from accelerometer alone
    pitch, roll = compute_tilt(orientation.values)
    out['pitch'] = pitch
    out['roll'] = roll

    return out

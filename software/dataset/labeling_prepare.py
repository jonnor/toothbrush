
import os.path
import pandas

from .combine import load_sensor_data, comma_separated_strings, date_type
from ..features.orientation import create_lowpass, apply_lowpass

def parse():
    import argparse

    parser = argparse.ArgumentParser(description='Read sensor data and combine with labels (if available)')
    
    parser.add_argument('--samplerate', type=int, default=50,
                        help='Samplerate')
    parser.add_argument('--sensitivity', type=float, default=2.0,
                        help='Sensitivity for accelerometer (g/FS)')

    parser.add_argument('--data', type=str, 
                        default=None,
                        help='Path to sensor data directory')

    parser.add_argument('--out', type=str,
                        default='',
                        help='Output path for combined data (Parquet)')

    parser.add_argument('--columns', type=comma_separated_strings, default=None,
                        help='Comma-separated column names to process')

    parser.add_argument('--default-date', type=date_type, default=None,
                        help='Date to set if data has 0000-00-00')

    
    return parser.parse_args()


def main():

    args = parse()

    out_dir = args.out
    if not out_dir:
        raise ValueError("--out not specified")

    # Load sensor data
    data = load_sensor_data(args.data,
        columns=args.columns,
        sensitivity=args.sensitivity,
        samplerate=args.samplerate,
        default_date=args.default_date,
    )
    print(data.head())


    # FIXME: should group by a "session" of sort
    # each individual .npy file is just one of many
    # might also want to have some metadata on this
    #files = data.groupby('filename')
    session = 'test1'

    gravity_filter = create_lowpass(args.samplerate)
    df = apply_lowpass(data, gravity_filter)

    # TODO: convert to relative times?

    # XXX: resample to a multiple of the video framerate - as recommended by Label Studio?

    os.makedirs(out_dir, exist_ok=True)

    # Write .CSV files, suitable for importing in Label Studio
    out_path = os.path.join(out_dir, session+'.csv')
    df.to_csv(out_path)
    print('Wrote', out_path)
    print(df.columns)

if __name__ == '__main__':
    main()

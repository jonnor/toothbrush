
"""
Combine sensor data and labels into a dataset
"""

import os
import json
from datetime import datetime, date 

import plotly.express
import pandas
import numpy

from software.utils.labelstudio import read_timeseries_labels


def parse_har_record_filename(f, default_date=None):

    if default_date is not None:
        f = f.replace('0000-00-00', default_date.strftime('%Y-%m-%d'))

    tok = f.replace('.npy', '').split('_')
    datestr, label = tok

    s = pandas.Series({
        'time': pandas.Timestamp(datestr),
        'label': label,
    })
    return s

def load_har_record(path,
        samplerate,
        sensitivity,
        maxvalue=32767,
        suffix = '.npy',
        columns=None,
        ):
    """Load dataset from har_record.py, from emlearn-micropython har_trees example"""

    files = []

    if columns is None:
        columns = ['x', 'y', 'z']

    for f in os.listdir(path):
        if f.endswith(suffix):
            p = os.path.join(path, f)
            try:
                data = numpy.load(p, allow_pickle=True)
            except Exception as e:
                print(e)
                continue

            df = pandas.DataFrame(data, columns=columns)

            # Scale values into physical units (g)
            df = df.astype(float) / maxvalue * sensitivity

            # Add a time column, use as index
            t = numpy.arange(0, len(df)) * (1.0/samplerate)
            df['time'] = t
            df = df.set_index('time')

            classname = f.split('_')[1].rstrip(suffix)
            
            # Remove :, special character on Windows
            filename = f.replace(':', '')

            files.append(dict(data=df, filename=filename, classname=classname))

            #print(f, data.shape)

    out = pandas.DataFrame.from_records(files)
    out = out.set_index('filename')
    return out


def parse_video_filename(path):
    # Expects filename on form VID_20241231_155240
    basename = os.path.basename(path)
    filename, ext = os.path.splitext(basename)

    tok = filename.split('_')
    vid, date, time = tok

    dt = pandas.to_datetime(filename, format='VID_%Y%m%d_%H%M%S')
    #dt = pandas.to_datetime(date, format='%Y%m%d')
    #print(filename)
    return dt

def find_label_gaps(df):
    df = df.sort_values('start')
    gaps = df.shift(-1)['start'] - df['end']
    return gaps

def read_labels(path):

    labels = read_timeseries_labels(path, label_column='activity', label_key='labels')
    # XXX: this is toothbrushing specific
    labels['filename'] = labels['file'].str.replace('label_', '')

    # Enrich
    labels['duration'] = labels['end'] - labels['start']
    gg = labels.groupby('filename', as_index=False).apply(find_label_gaps, include_groups=False).droplevel(0)
    labels['gap'] = gg

    return labels


def apply_labels(data, labels,
                 label_column='class',
                 time='time',
                 start='start',
                 end='end',
                 groupby='filename'):

    labels = labels.reset_index().set_index(groupby)

    def apply_labels_one(df):
        group = df.name
        df = df.set_index(time).sort_index()
        
        # Find relevant labels
        try:
            ll = labels.loc[group]
        except KeyError as e:
            print('No labels found for', group, df.index.max())

            df = df[df.index == 'SHOULD BE FALSE']
            assert len(df) == 0
            return df

        # Apply the labels
        dup = df[df.index.duplicated()]
        assert len(dup) == 0, dup

        df[label_column] = None
        for idx, l in ll.iterrows():
            s = l[start]
            e = l[end]
            try:
                df.loc[s:e, label_column] = l[label_column]
            except KeyError as err:
                print(f'No matches for {s}:{e}')

        #print(ll)
        #df = df.reset_index()

        return df
    
    out = data.groupby(groupby, as_index=False).apply(apply_labels_one)
    return out


def load_sensor_data(path, samplerate=50, sensitivity=2.0, columns=None, default_date=None):

    files = load_har_record(path, samplerate=samplerate, sensitivity=sensitivity, columns=columns)
    files = files.reset_index()
    stats = files.filename.apply(parse_har_record_filename, default_date=default_date).add_prefix('file_')
    files = pandas.merge(files, stats, right_index=True, left_index=True)

    dfs = []
    for idx, f in files.iterrows():
        df = f.data.reset_index()
        df['filename'] = f.filename
        df['time'] = f.file_time + pandas.to_timedelta(df['time'], unit='s')
        dfs.append(df)

    data = pandas.concat(dfs)

    return data

def comma_separated_strings(value):
    return [item.strip() for item in value.split(',')]

def date_type(date_string):
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: '{date_string}'. Use YYYY-MM-DD")

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
    parser.add_argument('--labels', type=str,
                        default=None,
                        help='Path to labels CSV file')
    parser.add_argument('--out', type=str,
                        default='combined.parquet',
                        help='Output path for combined data (Parquet)')
    parser.add_argument('--columns', type=comma_separated_strings, default=None,
                        help='Comma-separated column names to process')

    parser.add_argument('--default-date', type=date_type, default=None,
                        help='Date to set if data has 0000-00-00')

    
    return parser.parse_args()

def main():
    args = parse()

    out_path = args.out

    # Load sensor data
    data = load_sensor_data(args.data,
        columns=args.columns,
        sensitivity=args.sensitivity,
        samplerate=args.samplerate,
        default_date=args.default_date,
    )
    print(data.head())
    
    # Load labels
    labels_path = args.labels
    if labels_path is not None:
        labels = read_labels(args.labels)

        print(labels)

        # Combine labels and data
        merged = apply_labels(data, labels)
        #merged['is_motion'] = ~lb['class'].isin(['docked'])
        merged['is_brushing'] = lb['class'].isin(['brushing'])
        merged

        print(merged.is_brushing.value_counts())

    else:
        print('No labels specified')
        merged = data.copy()

    merged.to_parquet(out_path)
    print('Wrote data to', out_path)

if __name__ == '__main__':
    main()



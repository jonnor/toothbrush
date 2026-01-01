
# FIXME: switch do the data in https://zenodo.org/records/4118900 - has labels
"""
Utilities for working with toothbrush IMU dataset by Hussain et. al (2021)
"Dataset for toothbrushing activity using brush-attached and wearable sensors"
https://www.sciencedirect.com/science/article/pii/S2352340921005321
https://data.mendeley.com/datasets/hx5kkkbr3j/1
"""

import os
import zipfile
import json

import pandas
import numpy

from ..utils.downloadutils import download_file, checksum_file
from software.features.featureutils import resample


dataset_url = 'https://zenodo.org/records/4118900/files/Zawar_Hussain-Toothbrushing_Data_and_Analysis_of_its_Potential_Use_in_Human_Activity_Recognition_Applications.zip?download=1'
dataset_sha1 = '56c20104e2a566f8e54f1656defd6ff15e924454'
dataset_filename = 'Toothbrushing_Data.zip'
dataset_top_dir = 'data'


def load_data_generator(dataset_path, sensors=['W', 'A']):

    """
    Expects dataset to have layout of the following form:
    
    ROOT
    ├── DESCRIPTION.md
    ....
    ├── S1-S10-S1-M-R-AW-30-E-3-AG
    │   ├── S1-S10-S1-M-R-A-30-E-3-A.csv
    ....
    """

    out_columns = {
        'epoc (ms)': 'time',
        #'elapsed (s)': 'elapsed',
        'x-axis (g)': 'acc_x',
        'y-axis (g)': 'acc_y',
        'z-axis (g)': 'acc_z',
        'x-axis (deg/s)': 'gyro_x',
        'y-axis (deg/s)': 'gyro_y',
        'z-axis (deg/s)': 'gyro_z',
    }

    missing_labels = []

    for d in os.listdir(dataset_path):
        # Ignore non-session files/directories
        if d in ('DESCRIPTION.md', 'sample', 'metadata.json'):
            continue

        # Labels are per session / dirname
        labels_path = os.path.join(dataset_path, d, 'labels.json')
        if not os.path.exists(labels_path):
            missing_labels.append(filename)
            continue

        # Not all sessions are labeled
        labels = None
        if os.path.exists(labels_path):
            labels = load_label_file(labels_path)
        else:
            missing_labels.append(filename)


        #print('d', d, None if labels is None else len(labels))

        # There are files for accelerometer+gyro, for brush-attached and a wrist-attached sensor

        for sensor in sensors:

            # collect the accel+gyro before merging
            sensor_data = {}
            all_files = []
            for filename in os.listdir(os.path.join(dataset_path, d)):
                all_files.append(filename)
                if filename == 'labels.json':
                    continue

                meta = parse_filename(filename)
                #print(meta.items)
    
                if meta.sensor_location != sensor:
                    continue

                #print('ff', sensor, filename)
                #continue

                p = os.path.join(dataset_path, d, filename)

                df = pandas.read_csv(p)

                other_columns = set(df.columns) - set(out_columns.keys())
                df = df.drop(columns=other_columns)
                df = df.rename(columns=out_columns)
                df['time'] = pandas.to_datetime(df['time'], unit='ms', utc=True)
                df['filename'] = filename
                #df['session'] = d
                for key, value in meta.items():
                    df[key] = value

                sensor_data[meta.sensor] = df

            # Merge the data for one sensor
            #print('s', sensor_data.keys(), all_files)
            acc = sensor_data['A']
            gyro = sensor_data['G'][['time', 'gyro_x', 'gyro_y', 'gyro_z']]
            data = pandas.merge(acc, gyro, right_on='time', left_on='time')
            yield data


def load_data(dataset_path, **kwargs):

    generator = load_data_generator(dataset_path, **kwargs)
    dfs = []
    rows = 0
    for df in generator:
        dfs.append(df)
        rows += len(df)

    print('files', len(dfs), rows)
    out = pandas.concat(dfs, axis=0, ignore_index=True)
    print('concat', out.shape, out.columns)
  
    return out


def load_label_file(labels_path):

    # Load and normalize label info
    labels = json.loads(open(labels_path).read())
    label_events = []
    for classname, (start, end) in labels.items():
        event = {
            'label': classname,
            'start': pandas.Timestamp(start),
            'end': pandas.Timestamp(end),
        }
        label_events.append(event)
    labels_df = pandas.DataFrame.from_records(label_events)

    return labels_df

def load_labels(dataset_path):

    dfs = []
    missing_labels = []
    for d in os.listdir(dataset_path):
        if d in ('DESCRIPTION.md', 'sample', 'metadata.json'):
            continue

        # Labels are per session / dirname
        labels_path = os.path.join(dataset_path, d, 'labels.json')
        if not os.path.exists(labels_path):
            missing_labels.append(filename)
            continue
    
        labels_df = load_label_file(labels_path)

        # We want to associate labels with data filename
        for filename in os.listdir(os.path.join(dataset_path, d)):
            if filename in ('labels.json', ):
                continue
            sub = labels_df.copy()
            sub['filename'] = filename
            dfs.append(sub)

    df = pandas.concat(dfs, axis=0, ignore_index=False)

    return df

def parse_filename(filename):
    """
    Parse the structured metadata provided in filenames
    Described in "Read me.txt"

    S{setting}-S{subject}-S{session}-{gender}-{hand}-{sensor-location}-{age}-{brush type}-{location}-{sensor}
    """

    setting = None
    tok = filename.split('-')

    #print(filename, len(tok))

    if len(tok) == 10:
        setting, subject, session, gender, hand, sensor_loc, age, brush, location, sensor = tok
    elif len(tok) == 9:
        # NOTE: there are 4 instances where the filenames are missing one of the first Sx values
        # but it is not documented which
        # However, the directory names does not seem to have this problem
        # XXX: which one is missing??
        subject, session, gender, hand, sensor_loc, age, brush, location, sensor = tok
        #raise ValueError(f"Missing value in filename: {filename}")
    else:
        raise ValueError(f'Unexpected filename format: {filename}')
    m = pandas.Series(dict(
        setting=setting,
        subject=subject, #.replace('S', 'P'),
        session=int(session.replace('S', '')),
        gender=gender,
        hand=hand,
        sensor_location=sensor_loc,
        brush=brush,
        location=location,
        sensor=sensor.replace('.csv' , ''),
        filename=filename,
    ))
    return m


def load_meta(data):
    data = data.reset_index()
    meta = pandas.Series(data.filename.unique()).apply(parse_filename).set_index('filename')
    
    categoricals = set(meta.columns) - set(['session'])
    for c in categoricals:
        meta[c] = meta[c].astype('category')

    return meta

def extract_relevant(data, brush='M', location='A'):

    # Filter the data
    select = data.copy()
    if brush is not None:
        select = select[select.brush == brush]
    if location is not None:
        select = select[select.sensor_location == location]

    return select

def apply_labels(data, labels):

    data = data.reset_index()
    data = data.set_index('filename')

    data_filenames = numpy.unique(data.index)
    label_filenames = numpy.unique(labels.index)
    unknown_labels = set(label_filenames) - set(data_filenames)
    unlabeled = set(data_filenames) - set(label_filenames)

    # XXX: data might be filtered, so cannot enforce these
    # assert unknown_labels == set(), unknown_labels
    # some in data do not have any labels
    # assert len(unlabeled) < 3, len(unlabeled)

    data_labels = labels[labels.index.isin(data_filenames)]
    assert len(data_labels) > 1, data_labels.shape

    dfs = []
    unknown_files = []

    for filename, sub in data.groupby('filename'):
        #sub['filename'] = filename

        sub['label'] = None # default to unknown
        sub = sub.reset_index().set_index('time').sort_index()

        filename_labels = data_labels.loc[filename]
        for _, row in filename_labels.iterrows():
            #if not isinstance(sub, pandas.DataFrame):
            #    print('Warn: Got Series instead of DataFrame', filename)
            #    continue
    
            # apply the label
            s = row['start']
            e = row['end']
            sub.loc[s:e, 'label'] = row.label
            sub['label'] = sub['label']

        sub = sub.reset_index()
        dfs.append(sub)

    assert len(unknown_files) == 0, unknown_files
    out = pandas.concat(dfs, ignore_index=True)
    out['label'] = out['label'].astype('category')
    assert len(out) == len(data)
    return out

def download(out_dir):

    # Download
    archive_path = os.path.join(out_dir, dataset_filename)
    if os.path.exists(archive_path):
        print('Archive file exists, skipping download', archive_path)
    else:
        download_file(dataset_url, archive_path)

    # Verify download
    checksum = checksum_file(archive_path)
    assert checksum == dataset_sha1, (checksum, dataset_sha1)

    # Unpack
    top_path = os.path.join(out_dir, dataset_top_dir)
    if os.path.exists(top_path):
        print('Dataset directory already exists, skipping unpacking', top_path)
    else:
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(out_dir)

        assert os.path.exists(top_path), top_path

    # Sanity check
    readme_path = os.path.join(top_path, 'DESCRIPTION.md')
    assert os.path.exists(readme_path), readme_path

    return top_path

def main():

    samplerate = 50
    out_dir = './data3/hussain2020'
    os.makedirs(out_dir, exist_ok=True)

    dataset_path = download(out_dir)


    labels = load_labels(dataset_path).set_index('filename')

    print(labels.head())    
    filenames = set(labels.index)
    #print(filenames)


    data = load_data(dataset_path)
    print('Data')
    print(data.head())
    assert len(data) > 0, data.shape

    # Preprocess
    acc = extract_relevant(data)
    assert len(acc) > 0, acc.shape
    print(acc.columns)
    print(acc.head())

    meta = load_meta(data)
    print(meta)

    # Resample to our samplerate
    freq = pandas.Timedelta(1/samplerate, unit='s')
    resampled = resample(acc, freq=freq).reset_index().drop(columns=['session'])

    print('\n\nresample', acc.shape, resampled.shape)

    resampled = pandas.merge(resampled, meta, left_on='filename', right_index=True).drop(columns=['index']).set_index(['filename', 'time']).sort_index()
    assert len(resampled) <= len(acc)

    #print(acc_re.head())
    labeled = apply_labels(resampled, labels)
    assert len(labeled) == len(resampled), (len(labeled), len(resampled))
    assert len(labeled) >= 188820, len(labeled)

    n_unlabeled = numpy.count_nonzero(labeled.label.isna())
    unlabeled_ratio = n_unlabeled / len(labeled)
    assert unlabeled_ratio <= 0.20, unlabeled_ratio

    print(labeled.label.value_counts(dropna=False))

    duplicates = labeled[labeled.index.duplicated()]
    assert duplicates.empty

    out_path = './data/hussain2021_brush_manual_s1.parquet'
    labeled.to_parquet(out_path)
    print('Wrote', out_path, labeled.shape)

if __name__ == '__main__':
    main()


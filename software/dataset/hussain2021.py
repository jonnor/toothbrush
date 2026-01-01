
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


def load_data(dataset_path):

    """
    Expects dataset to have layout of the following form:
    
    ROOT
    ├── DESCRIPTION.md
    ....
    ├── S1-S10-S1-M-R-AW-30-E-3-AG
    │   ├── S1-S10-S1-M-R-A-30-E-3-A.csv
    ....
    """

    dfs = []
    session_no = 0
    rows = 0

    out_columns = {
        'epoc (ms)': 'time',
        'elapsed (s)': 'elapsed',
        'x-axis (g)': 'acc_x',
        'y-axis (g)': 'acc_y',
        'z-axis (g)': 'acc_z',
        'x-axis (deg/s)': 'gyro_x',
        'y-axis (deg/s)': 'gyro_y',
        'z-axis (deg/s)': 'gyro_z',
    }

    for d in os.listdir(dataset_path):
        if d in ('DESCRIPTION.md', 'sample', 'metadata.json'):
            continue
        for f in os.listdir(os.path.join(dataset_path, d)):
            p = os.path.join(dataset_path, d, f)
            df = pandas.read_csv(p)
            other_columns = set(df.columns) - set(out_columns.keys())
            #print(df.head(10))
            df = df.drop(columns=other_columns)
            df['filename'] = f
            #df['dirname'] = d
                
            dfs.append(df)
            session_no += 1
            rows += len(df)
            #break

    print('files', len(dfs), rows)
    out = pandas.concat(dfs, axis=0, ignore_index=True)
    print('concat', out.shape, out.columns)
    
    # Get out time information
    out['time'] = pandas.to_datetime(out['epoc (ms)'], unit='ms', utc=True)
    out = out.drop(columns=['epoc (ms)'])

    # Drop units from colum names
    out = out.rename(columns=out_columns)
    return out

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

def extract_relevant(data, meta, only_acc=True, brush='M', location='A'):
    gyro_columns = ['gyro_x', 'gyro_y', 'gyro_z']
    acc_columns = ['acc_x', 'acc_y', 'acc_z']

    # FIXME: merge/align gyro data with accelerometer
    # only accelerometer data
    if only_acc:
        acc = data.dropna(subset=acc_columns).drop(columns=gyro_columns)
    else:
        acc = data


    acc = acc.reset_index()
    meta = meta.reset_index()
    common = set(acc['filename']).intersection(meta['filename'])
    assert common != set()

    acc = pandas.merge(acc, meta,
        left_on='filename',
        right_on='filename',
    )
    #assert len(acc) == len(data)

    if brush is not None:
        acc = acc[acc.brush == brush]
    if location is not None:
        acc = acc[acc.sensor_location == location]

    acc = acc.drop(columns=['index'])
    return acc

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
    for filename, row in data_labels.iterrows():
        #print('f', filename)
        s = row['start']
        e = row['end']
        try:
            sub = data.loc[[filename]]
        except KeyError as e:
            unknown_files.append(filename)
            continue

        #print(sub.head())

        if not isinstance(sub, pandas.DataFrame):
            print('Warn: Got Series instead of DataFrame', filename)
            continue

        sub = sub.set_index('time')
        sub['filename'] = filename
        sub['label'] = None # default to unknown
        sub.loc[s:e, 'label'] = row.label
        sub = sub.reset_index()
        sub['label'] = sub['label'].astype('category')
        #print('aa', len(sub))
        dfs.append(sub)

    assert len(unknown_files) == 0, unknown_files
    out = pandas.concat(dfs, ignore_index=True)
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

    meta = load_meta(data)
    print('Metadata')
    print(meta.head())
    assert len(meta) > 1, meta.shape

    print("Setting")
    print(meta.setting.value_counts(dropna=False))

    # Preprocess
    acc = extract_relevant(data, meta, only_acc=True)
    assert len(acc) > 0, acc.shape
    print(acc.columns)
    print(acc.head())


    # Resample to our samplerate
    freq = pandas.Timedelta(1/samplerate, unit='s')
    acc_re = resample(acc, freq=freq).reset_index().drop(columns=['session'])
    acc_re = pandas.merge(acc_re, meta, left_on='filename', right_index=True).drop(columns=['index']) # .set_index(['filename', 'time'])

    #print(acc_re.head())
    acc_re = apply_labels(acc_re, labels)

    print(acc_re.label.value_counts(dropna=True))

    print(acc_re.head())


    acc_re = acc_re.reset_index().set_index(['filename', 'time'])
    #print(acc_re.head())


    out_path = './data/hussain2021_brush_manual_s1.parquet'
    acc_re.to_parquet(out_path)
    print('Wrote', out_path)

if __name__ == '__main__':
    main()


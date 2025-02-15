

"""
Utilities for working with toothbrush IMU dataset by Hussain et. al (2021)
"Dataset for toothbrushing activity using brush-attached and wearable sensors"
https://www.sciencedirect.com/science/article/pii/S2352340921005321
https://data.mendeley.com/datasets/hx5kkkbr3j/1
"""

import os
import zipfile

import pandas
from ..utils.downloadutils import download_file, checksum_file
from software.features.featureutils import resample


dataset_url = 'https://prod-dcd-datasets-cache-zipfiles.s3.eu-west-1.amazonaws.com/hx5kkkbr3j-1.zip'
dataset_sha1 = '96d0de3756c566627be816fca96ca4dc8c5dcf6c'
dataset_filename = 'hx5kkkbr3j-1.zip'
dataset_top_dir = 'hussain2021'


def load_data(dataset_path):

    """
    Expects dataset to have layout of the following form:
    
    ROOT
    ├── Read Me.txt
    ├── S1-S10-S1-M-R-AW-30-E-3-AG
    │   ├── S1-S10-S1-M-R-A-30-E-3-A.csv
    ....
    """

    dfs = []
    session_no = 0
    for d in os.listdir(dataset_path):
        if d in ('Read Me.txt', ):
            continue
        for f in os.listdir(os.path.join(dataset_path, d)):
            p = os.path.join(dataset_path, d, f)
            df = pandas.read_csv(p)
            df['filename'] = f
            #df['dirname'] = d
                
            dfs.append(df)
            session_no += 1
            

    out = pandas.concat(dfs)

    # Get out time information
    out['time'] = pandas.to_datetime(out['epoc (ms)'], unit='ms')
    out = out.drop(columns=['timestamp (+1100)', 'timestamp (+1000)', 'epoc (ms)']) # redundant wrt 'time'

    # Drop units from colum names
    out = out.rename(columns={
        'elapsed (s)': 'elapsed',
        'x-axis (g)': 'acc_x',
        'y-axis (g)': 'acc_y',
        'z-axis (g)': 'acc_z',
        'x-axis (T)': 'mag_x',
        'y-axis (T)': 'mag_y',
        'z-axis (T)': 'mag_z',
        'x-axis (deg/s)': 'gyro_x',
        'y-axis (deg/s)': 'gyro_y',
        'z-axis (deg/s)': 'gyro_z',
    })
    return out


def parse_filename(filename):
    """
    Parse the structured metadata provided in filenames
    Described in "Read me.txt"

    S{setting}-S{subject}-S{session}-{gender}-{hand}-{sensor-location}-{age}-{brush type}-{location}-{sensor}
    """

    setting = None
    tok = filename.split('-')
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
    meta = pandas.Series(data.filename.unique()).apply(parse_filename).set_index('filename')

    # XXX: drop data with irregular formatting of metadata (filename has 9 components not 10)
    meta = meta[~meta.setting.isna()]
    
    categoricals = set(meta.columns) - set(['session'])
    for c in categoricals:
        meta[c] = meta[c].astype('category')
    
    return meta

def extract_relevant(data, meta):
    # only accelerometer data
    acc = data.dropna(subset=['acc_x', 'acc_y', 'acc_z']).drop(columns=['mag_x', 'mag_y', 'mag_z', 'gyro_x', 'gyro_y', 'gyro_z'])
    acc = acc.reset_index()
    acc = pandas.merge(acc, meta, left_on='filename', right_on='filename')
    # Setting 2 has more specific protocol
    # Pause for a few seconds in between different regions and bring the brush to a reference point
    acc = acc[acc.setting == 'S2'] 
    # Choose location mounted on brush
    acc = acc[acc.sensor_location == 'A']
    # Choose only manual brushing, not electric
    acc = acc[acc.brush == 'M']
    acc = acc.drop(columns=['index'])
    return acc


def download(out_dir):

    # Download
    archive_path = os.path.join(out_dir, dataset_filename)
    if os.path.exists(archive_path):
        print('Archive file exists, skipping download', archive_path)
    else:
        download_file(dataset_url, archive_path)

    # Verify download
    checksum = checksum_file(archive_path)
    assert checksum == dataset_sha1, (checksum, dataset_checksum)

    # Unpack
    top_path = os.path.join(out_dir, dataset_top_dir)
    if os.path.exists(top_path):
        print('Dataset directory already exists, skipping unpacking', top_path)
    else:
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(top_path)

        assert os.path.exists(top_path), top_path

    # Sanity check
    readme_path = os.path.join(top_path, 'Read Me.txt')
    assert os.path.exists(readme_path), readme_path

    return top_path

def main():

    samplerate = 50
    out_dir = './data2'
    dataset_path = download(out_dir)

    data = load_data(dataset_path)
    print(data.head())

    meta = load_meta(data)
    print(meta.head())

    # Preprocess
    acc = extract_relevant(data, meta)

    # Resample to our samplerate
    freq = pandas.Timedelta(1/samplerate, unit='s')
    acc_re = resample(acc, freq=freq).reset_index().drop(columns=['session'])
    acc_re = pandas.merge(acc_re, meta, left_on='filename', right_index=True).drop(columns=['index']).set_index(['filename', 'time'])

    acc_re.to_parquet('./data2/hussain2021_accelerometer_brush_manual.parquet')

if __name__ == '__main__':
    main()


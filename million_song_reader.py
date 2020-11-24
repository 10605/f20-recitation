import h5py
import os
import boto3 
import tempfile
import pandas as pd


# If you have the data already in s3, this function lists all the files in s3 that start with the given prefix
def get_prefixes(bucket='roborace-imaronna', prefix='million-song/data/'):
    # In order to run with multiple threads/machines at a time, the prefix could be set to different things,
    # to make sure there is no overlap. For example, 'million-song/data/A', 'million-song/data/B', ...
    
    s3 = boto3.client('s3')

    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

    prefixes = [content['Key'] for content in response['Contents']]

    while response['IsTruncated']:
        response = s3.list_objects_v2(Bucket=bucket, 
                                      Prefix=prefix, 
                                      ContinuationToken=response['NextContinuationToken'])
        prefixes.extend([content['Key'] for content in response['Contents']])
        
    return prefixes


def process_h5_file(h5_file):
    """Do the processing of what fields you'll use here.

     For example, to get the artist familiarity, refer to:

     https://github.com/tbertinmahieux/MSongsDB/blob/master/PythonSrc/hdf5_getters.py

     So we see that it does h5.root.metadata.songs.cols.artist_familiarity[songidx] 
     and it would translate to:

       num_songs = len(file['metadata']['songs'])
       file['metadata']['songs'][:num_songs]['artist_familiarity']

     Since there is one song per file, it simplifies to:

       file['metadata']['songs'][:1]['artist_familiarity']

     I recommend downloading one file, opening it with h5py, and explore/practice

     To see the datatype and shape:

     http://millionsongdataset.com/pages/field-list/
     http://millionsongdataset.com/pages/example-track-description/
     """
    return h5_file['metadata']['songs'][:1]['artist_familiarity'][0]


def transform_local(path):
    try:
        with h5py.File(path) as h5:
            return process_h5_file(h5)
    except Exception:
        return []

def transform_s3(key, bucket='roborace-imaronna'):
    """
    REMEBER TO DO DEFENSIVE PROGRAMMING, WRAP IN TRY/CATCH
    """
    s3 = boto3.client('s3')
    
    with tempfile.NamedTemporaryFile(mode='wb') as tmp:
        s3.download_fileobj(bucket, key, tmp)
    
        try:
            with h5py.File(tmp.name) as h5:
                return process_h5_file(h5)
        except Exception:
            return []
        
def rows_to_file(rows):
    # Write some code to save a list of rows into a temporary CSV (or whatever format)
    # for example using pandas.

    
# If using the local volume:
processed = []
chunk_size = 10000

for root, dirs, files in os.walk('million-song/data/'):
    for f in files:
        processed.append(os.path.join(root, f))
        
        if len(processed) % chunk_size == 0:
            rows_to_file(processed) 
            # upload to s3. make sure to not overwrite the name
            processed = []

            
# If downloading the files from s3, transfomring and saving to s3
processed = []
chunk_size = 10000

for prefix in get_prefixes():
    processed.append(transform_s3(prefix))
    
    if len(processed) % chunk_size == 0:
        rows_to_file(processed) 
        # upload to s3. make sure to not overwrite the name
        processed = []

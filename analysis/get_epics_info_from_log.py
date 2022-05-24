import os
import sys
import csv 
import pandas 
import numpy as np

'''
    Functions to read out the EPICS log file and insert the relevent data into the run dataframe
'''

def read_epics_log(infile):
    '''
        Reads the pandas csv recorded by Dieter's code and returns it as a pandas DF
    '''
    data =  pandas.read_csv(infile, sep=' ')
    # process dataframe to turn timestamps into proper formats 
    data['time'] = pandas.to_datetime(data['time'],unit='s')
    # sort the epics data by timestamp
    data.sort_values(by='time', inplace=True)
    return data

def get_closest_row_epics(epics, timestamp):
    '''
        Get the closest epics row after the start of the subrun
    '''
    dfi = epics.loc[epics['time'] >= timestamp]
    print(timestamp, dfi)
    if(dfi.shape[0] > 0):
        return dfi.iloc[0]
    else:
        print("Warning: No matching epics data found for timestamp", timestamp)
        return None


def combine_log_files(data_file, epics_file, skip_existing=True):
    '''
        Reads the epics data and writes it on a subrun-by-subrun basis to the data_file
    '''
    epics = read_epics_log(epics_file)
    df = pandas.read_csv(data_file)
    print(epics.head())

    for i, dfi in df.iterrows():
        # print(i, dfi)

        if(skip_existing and pandas.notna(dfi['epics_time'])):
            print("Epics data for this subrun already written, skipping...")
            continue

        subrun_start_time = pandas.to_datetime(dfi['subrun_start_time'],unit='s')
        epics_row = get_closest_row_epics(epics, subrun_start_time)
        # print(epics_row)
        if(epics_row is not None):
            for x,val  in epics_row.iteritems():
                # print(j,x, epics_row[x])
                df.at[i,f'epics_{x}'] = val
    
    print(df.head())
    df.to_csv(data_file, index=False)

if __name__ == '__main__':
    combine_log_files(sys.argv[1], sys.argv[2], True)



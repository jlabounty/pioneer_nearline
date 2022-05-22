import os 
import subprocess
import sys 
import time
import pandas
import json

'''
    Automatically processes the newly created files through a simple analysis chain. Runs Patricks unpacking over
    every new file, produces an output file, and then creates a set of histograms from those
'''
DATA_DIR = '../../data/'
OUTPUT_DIR= '../../processed/'
RUN_DB = '../../processed/run_db.csv'

def make_outdir(indir:str): 
    return indir.replace(DATA_DIR, OUTPUT_DIR)
 
def identify_new_directories(indir):
    new_files = []
    for x,y,z in os.walk(indir):
        for zi in z:
            if(".bin" in zi or '.csv' in zi):
                thispath = os.path.join(x,zi)
                outpath = make_outdir(thispath).replace(".bin", '.root')
                print(f"{outpath=}")
                if(not os.path.exists( outpath )):
                    os.system(f'mkdir -p {os.path.dirname(outpath)}')
                    # os.system(f'touch {outpath}')
                    new_files.append(x)
                    print("Found new file:", thispath)

    return list(set(new_files))

def process_new_files():
    new_files = identify_new_directories(DATA_DIR)
    print(f"Found {len(new_files)} new subruns to process, {new_files}")
    for i, x in enumerate(new_files):
        print(f"    -> Processing {i+1}/{len(new_files)}", x)
        try:
            process_subrun(x)
        except:
            print("ERROR: Unable to process subrun", x)

def process_subrun(indir):
    '''
        Given a run directory and a subrun number, calls Patricks script to automatically process the files
    '''
    subrun = int(indir.strip("/").split("/subrun")[1])
    run = int(indir.strip("/").split("/run")[1].split("/")[0])
    print("   -> Processing:", indir, run, subrun)
    # logfile = f'log_{indir.split("/")[-1]}_{subrun}.log'
    command = f'python read_jl.py -r {run} -s {subrun} -d {DATA_DIR} -p {OUTPUT_DIR}'
    subprocess.run(command, shell=True)    

    do_post_processing(run,subrun)

def make_indir_outdir(run,subrun):
    indir = os.path.join(DATA_DIR, f'run{run}/data/subrun{subrun}')
    outdir = indir.replace(DATA_DIR, OUTPUT_DIR)
    return indir, outdir

def read_config_jsons(indir):
    this_config = {}
    for x,y,z in os.walk(indir):
        for zi in z:
            if(".json") in zi:
                thisfile = os.path.join(x,zi)
                thiskey = zi.split(".json")[0]
                with open(thisfile, 'r') as f:
                    this_config[thiskey] = json.load(f)

    return this_config
    
def do_post_processing(run,subrun):
    '''
        Extract values from this directory and put it into the nearline DB file
    '''
    print("Doing post processing for", run,subrun)
    indir, outdir = make_indir_outdir(run,subrun)
    rundir = os.path.join(indir,'../../')
    configdir = os.path.join(indir,'../../config/')
    print(indir, os.listdir(indir))
    print(rundir, os.listdir(rundir))
    print(configdir, os.listdir(configdir))
    print(outdir, os.listdir(outdir))

    # get run level data
    run_json = os.path.join(rundir,'run_info.json')
    if not os.path.exists(run_json):
        raise FileNotFoundError

    with open(run_json, 'r') as fin:
        run_data = json.load(fin)

    # get global config and such, also write to output folder
    config = read_config_jsons(configdir)
    print(f'{config=}')
    config['run_json'] = run_data
    with open(os.path.join(outdir, 'config.json'), 'w') as fout:
        json.dump(config, fout)

    # get subrun level data / config data
    # subrun_json = os.path.join(indir, )

    # copy the profiles over to the output directory
    for x in ['csv', 'pdf']:
        copycommand = f'cp {os.path.join(indir,f"*{x}")} {outdir}'
        print(copycommand)
        subprocess.run(copycommand, shell=True)

    # get the relevent quantities from the input and output directories, store in dict
    dfi = {
        'run':run,
        'subrun':subrun,
        'nfiles':len([x for x in os.listdir(indir) if '.bin' in x]),
        'process_time':time.time(),
    }
    for key,val in run_data.items():
        if("run_" not in key):
            key = f'run_{key}'
        dfi[key] = val

    # print(f"{run_data=}")
    try:
        subrun_data = run_data['subrun'][str(subrun)]
        for key, val in subrun_data.items():
            if('subrun_' not in key):
                key = f'subrun_{key}'
            dfi[key] = val
    except:
        print('Warning: subrun data not found')

    # get the means/stdevs from the csv file
    print('getting means')
    csvfile = os.path.join(outdir, 'profile.csv')
    try:
        if(os.path.exists(csvfile)):
            # the first line of the csv is: 
            with open(csvfile, 'r') as f:
                print('found file', f)
                for data in f:
                    # print(f[0])
                    # data = f[0].strip()
                    # print(data)
                    data = [float(x) for x in data.split(",")]
                    print('This beam data:', data)
                    dfi['beam_mean_x'] = data[0]
                    dfi['beam_mean_y'] = data[1]
                    dfi['beam_sigma_x'] = data[2]
                    dfi['beam_sigma_y'] = data[3]
                    dfi['beam_norm'] = data[4]
                    dfi['beam_timestamp'] = data[5]

                    break
    except:
        print("Warning: beam csv data not found.")
    print(f"{dfi=}")

    # append this dict to the dataframe stored in the RUN_DB
    append_to_df(RUN_DB, dfi)

def append_to_df(infile, dfi, drop_duplicates=True):
    df = pandas.read_csv(infile)
    # print(df.head())
    dfi = pandas.DataFrame([dfi])
    # print(dfi.head())
    df = df.append(dfi, ignore_index=True)
    # print(df.head())

    if(drop_duplicates):
        df.sort_values(by=['run', 'subrun', 'process_time'], inplace=True)
        df.drop_duplicates(subset=['run','subrun'], inplace=True, keep='last')

    df.to_csv(infile, index=False)


def autoprocess_files(interval=5):
    '''
        Automatically processes files every 'interval' minutes
    '''
    while True:
        print("Processing new files....")
        try:
            process_new_files()
        except:
            raise ValueError
        
        print("All done... waiting...")
        time.sleep(int(interval*60))


if __name__ == '__main__':
    if(len(sys.argv) > 1):
        # if(sys.argv[1]):
        process_new_files()
    else:
        autoprocess_files(5) # minutes
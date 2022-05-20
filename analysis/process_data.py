import os 
import subprocess
import sys 
import time

'''
    Automatically processes the newly created files through a simple analysis chain. Runs Patricks unpacking over
    every new file, produces an output file, and then creates a set of histograms from those
'''
DATA_DIR = '../../data/'
OUTPUT_DIR= '../../processed/'

def make_outdir(indir:str): 
    return indir.replace(DATA_DIR, OUTPUT_DIR)
 
def identify_new_directories(indir):
    new_files = []
    for x,y,z in os.walk(indir):
        for zi in z:
            if(".bin" in zi):
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
        autoprocess_files()
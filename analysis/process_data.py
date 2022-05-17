import os 
import subprocess
import sys 

'''
    Automatically processes the newly created files through a simple analysis chain. Runs Patricks unpacking over
    every new file, produces an output file, and then creates a set of histograms from those
'''
DATA_DIR = '../data/'

def identify_new_files(indir):
    new_files = []
    for x,y,z in os.walk(indir):
        for zi in z:
            if(".bin" in zi):
                thispath = os.path.join(x,zi)
                if(not os.path.exists( thispath.replace(".bin", '.root') )):
                    new_files.append(thispath)

    return new_files


def process_new_files():
    new_files = identify_new_files(DATA_DIR)
    print(f"Found {len(new_files)} new files to process")
    for i, x in enumerate(new_files):
        logfile = x.replace(".bin", '.log')
        print(f"    -> Processing {i+1}/{len(new_files)}", x)
        command = f'./master/readWD -o {os.path.dirname(x)} {x} | tee {logfile}'
        print(command)
        # subprocess.run(command, shell=True)


if __name__ == '__main__':
    process_new_files()
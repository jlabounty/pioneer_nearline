#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 Author: Patrick Schwendimann
 E-Mail: schwenpa@uw.edu
 
 This script is used to collect information from
 various .json files and use them to run readWD
 with apropriate configuration that matches the
 setup described in the json files. Once the files
 are read, this will visualise the output data
 using draw.py.

 Took classes from Patricks version, but changed main logic
 -Josh
"""
# from ast import parse
# from asyncio import subprocess
import subprocess
import json
import sys
import os

import draw
import argparse

class channel:
    # -3: RF, -2: Current, -1: Ignore, 0+: SiPM id
    chType = -1
    sign = None
    CF = None
    LE = None
    IntStart = None
    IntStop = None

class config:
    SubtractSine = 0
    NoiseFreq = 50.6e6
    IntRise = 3
    IntDecay = 6
    Samples = 200
    Save = 10
    Channels = dict()
    
    def __init__(self, files = []):
        default = channel()
        default.chType = 32767 #the largest possible short in C++ used to encode the ch type
        default.sign = -1
        default.CF = 0.2
        default.LE = 0.05
        default.IntStart = -1
        default.IntStop = -1
        
        self.Channels["GLOBAL"] = default
        
        for file in files:
            self.readfile(file)
            
    def readfile(self, filename):
        file = open(filename, "r")
        data = json.load(file)
        
        if ('chn_map' in data.keys()):
            #There is a channel map
            self._readChannelMap(data['chn_map'])
            
        if ('glob' in data.keys()):
            # This file has some global definitions
            self._readGlobal(data['glob'])
            
        if ('channels' in data.keys()):
            self._readChannels(data['channels'])
        
        file.close()
            
    def _readChannelMap(self, chn_map):
        for wdb in chn_map.keys():
            wdb_id = -1
            if (wdb[:2] == 'WD'):
                wdb_id = int(wdb[2:])
            else:
                wdb_id = int(wdb)
            
            for ch in range(len(chn_map[wdb])):
                key = f"{wdb_id}_{ch}"
                if (key not in self.Channels.keys()):
                    self.Channels[key] = channel()
                    
                self.Channels[key].chType = chn_map[wdb][ch]
                
    def _readGlobal(self, data):
        for key in data.keys():
            if (key == "SubtractSine"):
                self.SubtractSine = data[key]
            elif (key == "NoiseFreq"):
                self.NoiseFreq = data[key]
            elif (key == "IntRise"):
                self.IntRise = data[key]
            elif (key == "IntDecay"):
                self.IntDecay = data[key]
            elif (key == "Samples"):
                self.Samples = data[key]
            elif (key == "Save"):
                self.Save = data[key]
            elif (key == "sign"):
                self.Channels["GLOBAL"].sign = data[key]
            elif (key == "CF"):
                self.Channels["GLOBAL"].CF = data[key]
            elif (key == "LE"):
                self.Channels["GLOBAL"].LE = data[key]
            elif (key == "IntStart"):
                self.Channels["GLOBAL"].IntStart = data[key]
            elif (key == "IntStop"):
                self.Channels["GLOBAL"].IntStop = data[key]
            else:
                print(f"Unknown key {key}")
            
    def _readChannels(self, data):
        for ch in data.keys():
            if ch not in self.Channels.keys():
                newChannel = channel()
                newChannel.chType = -4
                self.Channels[ch] = newChannel
            
            theChannel = self.Channels[ch]
            for key in data[ch]:
                if (key == "sign"):
                    theChannel.sign = data[ch][key]
                elif (key == "chType"):
                    theChannel.chType = data[ch][key]
                elif (key == "CF"):
                    theChannel.CF = data[ch][key]
                elif (key == "LE"):
                    theChannel.LE = data[ch][key]
                elif (key == "IntStart"):
                    theChannel.IntStart = data[ch][key]
                elif (key == "IntStop"):
                    theChannel.IntStop = data[ch][key]
                else:
                    print(f"Unknown key {key}")

    def WriteToFile(self, filename):
        file = open(filename, "w")
        
        file.write(f"SubtractSine {self.SubtractSine}\n")
        file.write(f"NoiseFreq {self.NoiseFreq}\n")
        file.write(f"IntRise {self.IntRise}\n")
        file.write(f"IntDecay {self.IntDecay}\n")
        file.write(f"Samples {self.Samples}\n")
        file.write(f"Save {self.Save}\n")
        
        for key in self.Channels.keys():
            aChannel = self.Channels[key]
            file.write(f"Channel {key}\n")
            file.write(f"   chType {aChannel.chType}\n")
            if (aChannel.sign != None):
                file.write(f"   sign {aChannel.sign}\n")
            if (aChannel.CF != None):
                file.write(f"   CF {aChannel.CF}\n")
            if (aChannel.LE != None):
                file.write(f"   LE {aChannel.LE}\n")
            if (aChannel.IntStart != None):
                file.write(f"   intStart {aChannel.IntStart}\n")
            if (aChannel.IntStop != None):
                file.write(f"   intStop {aChannel.IntStop}\n")
                
        
        file.close()
        
def get_binary_files(indir):
    files = []
    for x,y,z in os.walk(indir):
        for zi in z:
            if(".bin" in zi):
                files.append(os.path.join(x,zi))
    return files

def get_config_files(run, subrun):
    files = []
    run_scan = os.path.join(run, 'config/scan.json')
    if(os.path.exists(run_scan)):
        files += [run_scan]

    return files
    
    # for x,y,z in os.walk(subrun):
    #     for zi in z:
    #         if()

def main():
    print("Processing")

    parser = argparse.ArgumentParser(description='Processing ')
    parser.add_argument('-d', '--data-dir', type=str, help='Path where the raw run folders are being written')
    parser.add_argument('-p', '--process-dir', type=str, help='Path where the processed run folders are being written')
    parser.add_argument('-o', type=str, help='Outname of the config file', default='tmp.cfg')
    parser.add_argument("-r", help='run number', required=True, type=int)
    parser.add_argument('-s', help='subrun number', required=True, type=int)

    parser.add_argument('-rc', help='read config file', default='./read_config.json')
    parser.add_argument('-i', help='config files', nargs='+', default=list())

    args = parser.parse_args(sys.argv[1:])
    print(args)

    run_dir = os.path.join(args.data_dir, f'run{args.r}')
    subrun_dir = os.path.join(run_dir,f'data/subrun{args.s}/')
    print('Looking for files in:', subrun_dir)
    output_dir = subrun_dir.replace(args.data_dir, args.process_dir)
    os.system(f"mkdir -p {output_dir}")
    print("Writing to", output_dir)

    print(args.i)
    args.i += get_config_files(run_dir, subrun_dir)
    args.i += [args.rc]
    print("Config files:", args.i)
    cfg = config(args.i)
    outname = os.path.join(output_dir, 'tmp.cfg')
    cfg.WriteToFile(outname)

    binary_files = get_binary_files(subrun_dir)
    if(len(binary_files) < 1):
        print("Found no files to process. Exiting.")
        return
    output_files = [x.replace('.bin', '.root').replace(subrun_dir, output_dir) for x in binary_files]

    command = f'readWD -i {outname} -o {output_dir}/ {" ".join(binary_files)}'
    print(command)
    print(output_files)
    subprocess.run(command, shell=True)

    for x in output_files:
        draw.DrawChannels(x)



if __name__ == "__main__":
    main()
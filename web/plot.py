# from dashboard import create_dashboard
import flask
from flask import Flask
from flask_assets import Environment
import logging

import hist
import pandas 
import numpy as np 
import sys
import os 
import uproot
import json

from flask import render_template
from flask import current_app as app
from dash.dependencies import Input, Output
from dash import html, dash, dash_table, dcc
import plotly.express as px
import plotly.graph_objects as go

import plotly.tools as tls
import matplotlib.pyplot as plt

from app import make_outdir

def get_histos_files(indir):
    files = []
    for x,y,z in os.walk(indir):
        for zi in z:
            if('histos.root' in zi):
                files.append(os.path.join(x,zi))
    return files

def make_global_amplitude_time_plot(run,subrun, key='AvT'):
    '''
        Extracts the global histogram from 
    '''
    outdir = make_outdir(run,subrun)

    these_files = get_histos_files(outdir)
    print(f"{these_files=}")
    h=None
    for infile in these_files:
        with uproot.open(infile) as f:
            for hi in f.keys():
                print(hi)
                if(key in hi):
                    if(h is None):
                        h = f[hi].to_hist().copy()
                    else:
                        h += f[hi].to_hist()
    print(f'{h=}')


    if(h is not None):
        return histogram_as_px(h)
        # return (px.scatter(x=[1], y=[2]))
    else:
        return (px.scatter(x=[0], y=[0]))

def histogram_as_px(h):
    # print('file found', this_file)
    hnp = h.to_numpy()
    return px.imshow(
        hnp[0].T,
        x=hnp[1][:-1],
        y=hnp[2][:-1], 
        aspect='auto',
        origin='lower',
        labels={
        'x':'t-t_rf', 
        'y':'Amplitude',
    }
    )

def get_subrun_data_file_from_position(run,subrun,data):
    '''
        Given a run, subrun and position, identify which data file it corresponds to.
    '''
    outdir = make_outdir(run,subrun)
    rundir = make_outdir(run)

    # get the position of the sipms and the simon stops from the config file, match it to the
    #   value from the click
    position = (data['points'][0]['x'],data['points'][0]['y'])
    config_file = os.path.join(outdir, 'config.json')
    with open(config_file, 'r') as f:
        config = json.load(f)

    scan_positions = config['scan']['scan_pos']
    scan_index = scan_positions.index(position[0])
    print(f'{scan_index=}')

    sipm_positions = [x[0] for x in config['pcb']['sipm_pos']]
    sipm_index = sipm_positions.index(position[1])
    print(f'{sipm_index=}')

    # from the sipm index and scan position index, get the proper histogram of A vs. t
    # TODO: Resolve/Test this when we have the chance
    which_board = 34
    which_sipm = 15
    which_file = scan_index
    h_name = f'hAvT_{which_board}_{which_sipm}'
    file_name = f'WD0{which_board:02}_{which_file}_histos.root'
    print(f"Looking with histogram with name {h_name} in file {file_name}")

    data_file = os.path.join(outdir,file_name)
    if(os.path.exists(data_file)):
        print("Found data file")
        with uproot.open(data_file) as f:
            h = f[h_name].to_hist()
            return histogram_as_px(h)

    else:
        print("Warning: data file not found")

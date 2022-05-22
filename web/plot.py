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
            'y':'Amplitude'
        }
        )
        # return (px.scatter(x=[1], y=[2]))
    else:
        return (px.scatter(x=[0], y=[0]))
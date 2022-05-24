# from process_data import make_indir_outdir
# from pickle import NONE
# import csv
from dashboard import create_dashboard
import flask
from flask import Flask
from flask_assets import Environment
import logging

import hist
import pandas 
import numpy as np 
import sys
import os 

from flask import render_template
from flask import current_app as app
from dash.dependencies import Input, Output
from dash import html, dash, dash_table, dcc
import plotly.express as px
import plot

FIG_DATATABLE = None
FIG_PLOTS = None
FIG_SCATTER = None

# BASE_DIR = '/home/jlab/github/pioneer_nearline/web/static/'
BASE_DIR = '/home/pioneer/github/pioneer_nearline/web/static/'

EPICS_FILE='/data/EpicsLogs/magnets.log'
# EPICS_FILE='/home/jlab/github/pioneer_nearline/data/magnets.log'


app = Flask(__name__, template_folder='static')
dashboard, df = create_dashboard(app)

# logging.t

@dashboard.callback(
    Output('runlog-datatable', 'data'), Output('runlog-datatable', 'columns'),
    Input("refresh-df", 'n_clicks'),
)
def refresh_runlog(click):
    '''
        When this function is called, the runlog table will refresh with the latest entries
    '''
    app.logger.error(f"refreshing!!! {click}")
    df.refresh()
    return (df.df.to_dict('records'), 
           [{"name": i, "id": i, "hidable":True, "selectable":True} for i in df.df.columns])

# @dashboard.callback(
#     Output('runlog-datatable', 'data'), Output('runlog-datatable', 'columns'),
#     Input("interval-refresh", 'n_intervals'),
# )
# def periodic_refresh(click):
#     app.logger.error("refreshing!!!", click)
#     return 1,2
#     # return refresh_runlog(click)

@dashboard.callback(
    Output('tab-content', 'children'),
    Input('tabs', 'value')
)
def render_tab_content(value):
    '''
        Take the value of the tab selected and use that to render the appropriate content
            - Run Conditions vs. Plots vs. Scatter
    '''
    app.logger.error("Rendering tab content...")
    if(value == 'runlog'):
        global FIG_DATATABLE
        # print( FIG_DATATABLE)
        if(FIG_DATATABLE is None):
            # print('ding!!!')
            FIG_DATATABLE = render_datatable()
        # else:
            # print("dong")
        return FIG_DATATABLE
    elif(value == 'plot'):
        global FIG_PLOTS
        # return html.Div([html.H1("TODO: Add plotly express plot here")])
        if(FIG_PLOTS is None):
            FIG_PLOTS = render_display()
        return FIG_PLOTS
    elif(value == 'scatter'):
        global FIG_SCATTER
        if(FIG_SCATTER is None):
            FIG_SCATTER = render_runlog_scatter()
        return FIG_SCATTER


def render_datatable():
    app.logger.error("Rendering Datatable...")
    return html.Div([
        dash_table.DataTable(
                    df.df.to_dict('records'), 
                    [{"name": i, "id": i, "hidable":True, "selectable":True} for i in df.df.columns],
                    filter_action='native',
                    id='runlog-datatable',
                    page_size=20,
                    style_table={
                        # 'height': 400,
                        'overflowX': 'scroll'
                    },
                    style_data={
                        'width': '150px', 'minWidth': '150px', 'maxWidth': '150px',
                        'overflow': 'hidden',
                        'textOverflow': 'ellipsis',
                    }
                )
    ])

def render_runlog_scatter():
    # Adapted from example here: https://dash.plotly.com/interactive-graphing
    app.logger.error("Rendering interactive scatter plot from runlog")
    return html.Div(
        [
            html.Div([
                html.Div([
                    dcc.Dropdown(
                        df.df.columns.unique(),
                        'run',
                        id='crossfilter-xaxis-column',
                    ),
                    dcc.Dropdown(
                        ['Linear', 'Log'],
                        'Linear',
                        id='crossfilter-xaxis-type',
                        # labelStyle={'display': 'inline-block', 'marginTop': '5px'}
                    )
                ],
                style={'width': '49%', 'display': 'inline-block'}),

                html.Div([
                    dcc.Dropdown(
                        df.df.columns.unique(),
                        'subrun',
                        id='crossfilter-yaxis-column'
                    ),
                    dcc.Dropdown(
                        ['Linear', 'Log'],
                        'Linear',
                        id='crossfilter-yaxis-type',
                        # labelStyle={'display': 'inline-block', 'marginTop': '5px'}
                    )
                ], style={'width': '49%', 'float': 'right', 'display': 'inline-block'}),
                # html.Div([dcc.Dropdown(
                #         df.df.columns.unique(),
                #         'subrun',
                #         id='crossfilter-hover-column'
                #     )])
            ], style={
                'padding': '10px 10px'
            }),
            html.Div([
                dcc.Input(id='input-run-low', type='number', placeholder='Run Low', debounce=True),
                dcc.Input(id='input-run-high', type='number', placeholder='Run High', debounce=True),
                dcc.Input(id='input-subrun-low', type='number', placeholder='Subrun Low', debounce=True),
                dcc.Input(id='input-subrun-high', type='number', placeholder='Subrun High', debounce=True),
            ], style={'text-align':'center'}),
            html.Div([
                 html.Div([
                    dcc.Graph(
                        id='crossfilter-indicator-scatter',
                        # hoverData={'points': [{'customdata': 'Japan'}]}
                    )
                ], style={'width': '100%', 'display': 'inline-block', 'padding': '10 20'}),
                html.Div([
                    html.Div([
                        dcc.Graph(id='x-time-series'),
                    ], style={'display': 'inline-block', 'width': '49%', 'padding': '10 20'}),
                    html.Div([
                        dcc.Graph(id='y-time-series'),
                    ], style={'display': 'inline-block', 'width': '49%', 'padding': '10 20'}),
                ], style={'width': '100%', 'display': 'inline-block', 'padding': '10 20'}),
            ])
        ]
    )

def create_time_series(dff, axis_type, title):

    fig = px.scatter(
        x = dff['run'] + dff['subrun']/100.,
        y = dff[title], 
        labels={
            'x':'Run + Subrun/100', 
            'y':title
        },
        title=title
    )

    fig.update_traces(mode='lines+markers')

    fig.update_xaxes(showgrid=False)

    fig.update_yaxes(type='linear' if axis_type == 'Linear' else 'log')

    fig.add_annotation(x=0, y=0.85, xanchor='left', yanchor='bottom',
                       xref='paper', yref='paper', showarrow=False, align='left',
                       text=title)

    fig.update_layout(height=225, margin={'l': 20, 'b': 30, 'r': 10, 't': 10})

    return fig

@dashboard.callback(
    Output('x-time-series', 'figure'),
    # Input('crossfilter-indicator-scatter', 'hoverData'),
    Input('crossfilter-xaxis-column', 'value'),
    Input('crossfilter-xaxis-type', 'value'),
    Input('input-run-low', 'value'),
    Input('input-run-high', 'value'),
    Input('input-subrun-low', 'value'),
    Input('input-subrun-high', 'value'),
)
def update_y_timeseries(xaxis_column_name, axis_type,runlow, runhigh, subrunlow,subrunhigh):
    # country_name = hoverData['points'][0]['customdata']
    # dff = df.df
    dff = filter_df_by_run(df, runlow,runhigh, subrunlow,subrunhigh)
    title = xaxis_column_name
    return create_time_series(dff, axis_type, title)

@dashboard.callback(
    Output('y-time-series', 'figure'),
    # Input('crossfilter-indicator-scatter', 'hoverData'),
    Input('crossfilter-yaxis-column', 'value'),
    Input('crossfilter-yaxis-type', 'value'),
    Input('input-run-low', 'value'),
    Input('input-run-high', 'value'),
    Input('input-subrun-low', 'value'),
    Input('input-subrun-high', 'value'),
    )
def update_x_timeseries(yaxis_column_name, axis_type,runlow, runhigh, subrunlow,subrunhigh):
    # dff = df.df
    dff = filter_df_by_run(df, runlow,runhigh, subrunlow,subrunhigh)
    title = yaxis_column_name
    return create_time_series(dff, axis_type, title)

@dashboard.callback(
    Output('crossfilter-indicator-scatter', 'figure'),
    Input('crossfilter-xaxis-column', 'value'),
    Input('crossfilter-yaxis-column', 'value'),
    Input('crossfilter-xaxis-type', 'value'),
    Input('crossfilter-yaxis-type', 'value'),
    Input('input-run-low', 'value'),
    Input('input-run-high', 'value'),
    Input('input-subrun-low', 'value'),
    Input('input-subrun-high', 'value'),
    # Input('crossfilter-hover-column', 'value'),
    # Input('crossfilter-year--slider', 'value')
    )
def update_graph(xaxis_column_name, yaxis_column_name,
                 xaxis_type, yaxis_type, runlow, runhigh, subrunlow,subrunhigh):
    '''
        Updates the scatter plot
    '''
    app.logger.error("Rendering data on graph...")
    dff = filter_df_by_run(df, runlow,runhigh, subrunlow,subrunhigh)

    fig = px.scatter(
        x=dff[xaxis_column_name],
        y=dff[yaxis_column_name],
        # hover_name=dff[indicator_name]
    )
    # print(dff[xaxis_column_name])

    # fig.update_traces(customdata=dff[dff['Indicator Name'] == yaxis_column_name]['Country Name'])

    fig.update_xaxes(title=xaxis_column_name, type='linear' if xaxis_type == 'Linear' else 'log')
    fig.update_yaxes(title=yaxis_column_name, type='linear' if yaxis_type == 'Linear' else 'log')
    fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')

    return fig
    
def filter_df_by_run(df, runlow,runhigh, subrunlow,subrunhigh):
    '''
        Filters a ReloadableDF Object by run/subrun and returns a copy
    '''
    dff = df.df.copy()
    # print(runlow,runhigh, subrunlow,subrunhigh)
    if(runlow is not None):
        dff = dff.loc[dff['run'] >= runlow]
    if(runhigh is not None):
        dff = dff.loc[dff['run'] <= runhigh]
    if(subrunlow is not None):
        dff = dff.loc[dff['subrun'] >= subrunlow]
    if(subrunhigh is not None):
        dff = dff.loc[dff['subrun'] <= subrunhigh]

    return dff

def render_display():
    '''
        Updates the displayed scan based on the run/subrun which was clicked
    '''
    # print(derived_ids, selected_ids, active_cell)
    # get the run/subrun number from the plot

    return(
        html.Div(
            [dcc.Dropdown(
                        list(df.df['run'].unique()),
                        df.df['run'][0],
                        id='crossfilter-run-select',
                    ),
            dcc.Dropdown(
                        list(df.df['subrun'].unique()),
                        df.df['subrun'][0],
                        id='crossfilter-subrun-select',
            )]
        ),
        html.Div(
            [
                html.Div(
                    dcc.Graph(id='profile-plot'),
                    style={'width': '30%', 'display': 'inline-block'}
                ),
                html.Div(
                    dcc.Graph(id='profile-plot-x'),
                    style={'width': '30%', 'display': 'inline-block'}
                ),
                html.Div(
                    dcc.Graph(id='profile-plot-y'),
                    style={'width': '30%', 'display': 'inline-block'}
                ),
            ],style={'text-align':'center'}
        ),
        html.Div(
            [
                html.Div(
                    dcc.Graph(id='times-display-global'),
                    style={'width': '49%', 'display': 'inline-block'}
                ),
                html.Div(
                    dcc.Graph(id='times-display-single'),
                    style={'width': '49%', 'display': 'inline-block'}
                ),
            ],style={'text-align':'center'}
        ),
        html.Div(
            [
                html.Iframe(src="",
                    width="750",height="400",
                    id='profile-pdf-display'
                    # type="application/pdf"
                )
            ], 
            style={'width': '49%', 'display': 'inline-block', 'text-align':'center'}
        )
    )

# @dashboard.callback()

'''
----------------------------------------------------------------------------------
Plot the profiles for this subrun (Plots tab)
----------------------------------------------------------------------------------
'''

@dashboard.callback(
    Output('profile-plot', 'figure'),
    Output('profile-pdf-display', 'src'),
    Output('profile-plot-x', 'figure'),
    Output('profile-plot-y', 'figure'),
    Input("crossfilter-run-select", 'value'),
    Input("crossfilter-subrun-select", 'value')
)
def update_display(run, subrun):
    '''
        Updates the live display of the beam profile
    '''

    # get the associated data file (if it exists, if not create it)
    # dfi = df.df.loc(df.df['run'] == int(run)).loc(df.df['subrun'] == int(subrun))
    outdir = make_outdir(run,subrun)
    csvfile = os.path.join(outdir,'profile.csv')
    # print(csvfile)
    if(not os.path.exists(csvfile)):
        print("ERROR: CSV file not found")
        return px.scatter([],[])

    dfi = pandas.read_csv(csvfile, header=None, skiprows=1)
    xbar, ybar, sigx, sigy, norm, _ = get_beam_properties(csvfile)
    
    x_xs = []
    x_ys = []
    for xi, dfii in dfi.groupby(by=0):
        x_xs.append(xi)
        x_ys.append(dfii[2].sum())

    y_xs = []
    y_ys = []
    for xi, dfii in dfi.groupby(by=1):
        y_xs.append(xi)
        y_ys.append(dfii[2].sum())

    # print(dfi.head)
    return (
        (px.scatter(
            x=dfi[0],
            y=dfi[1],
            color=dfi[2],
            # hover_data=[0,1,2,3,4],
            # marker_symbol='s',
            # mode='markers'
            width=500, height=500,
            title=f'Integral: {norm:.3f}',
            labels={"x":'x-position [mm]', 'y':'y-position [mm]'}
        )),
        get_profile_pdf( outdir ),
        (px.scatter(
            x=x_xs, y=x_ys, width=500, height=500, 
            title=f'Mean x: {xbar:.3f} | Sigma x: {sigx:.3f}',
            labels={'x':'x-position', 'y':'Beam Amplitude'})
        ),
        (px.scatter(
            x=y_xs, y=y_ys, width=500, height=500, 
            title=f'Mean x: {ybar:.3f} | Sigma x: {sigy:.3f}',
            labels={'x':'y-position', 'y':'Beam Amplitude'})
        ),
    )
    
'''
----------------------------------------------------------------------------------
Plot the 2D histogram of energy vs. time
----------------------------------------------------------------------------------
'''


@dashboard.callback(
    Output('times-display-single', 'figure'),
    Input("crossfilter-run-select", 'value'),
    Input("crossfilter-subrun-select", 'value'),
    Input("profile-plot", 'clickData'),
)
def make_single_plot(run, subrun, data):
    print(run, subrun, data)
    return plot.get_subrun_data_file_from_position(run,subrun,data)
    
@dashboard.callback(
    Output('times-display-global', 'figure'),
    Input("crossfilter-run-select", 'value'),
    Input("crossfilter-subrun-select", 'value'),
)
def make_global_plot(run, subrun):
    # print(run, subrun)
    # return px.scatter(x=[1,2,3, run], y=[4,5,6, subrun])
    return plot.make_global_amplitude_time_plot(run,subrun)


'''
----------------------------------------------------------------------------------
Helper functions
----------------------------------------------------------------------------------
'''

def make_outdir(run,subrun=None):
    '''
        returns the path to the processed files based on the run and subrun numbers
    '''
    if(subrun is None):
        return f'../processed/run{run}/'
    else:
        return f'../processed/run{run}/data/subrun{subrun}/'

def get_profile_pdf(subrundir):
    '''
        Returns the path to the profile PDF automatically produced per subrun
    '''
    thispath = os.path.join('assets',subrundir[3:], 'profile.pdf')
    print(thispath)
    if(not os.path.exists(thispath)):
        return None
    return thispath

def get_beam_properties(csvfile):
    '''
        Extracts the fitted mean/stdev from the beam csv file
    '''
    with open(csvfile, 'r') as f:
        for data in f:
            data = [float(x) for x in data.split(",")]
            return data

'''
----------------------------------------------------------------------------------
Set up routes for the flask app
----------------------------------------------------------------------------------
'''


@app.route('/epics')
def epics():
    df = pandas.read_csv(EPICS_FILE, sep=' ')
    df.sort_values(by=df.columns[0], inplace=True, ascending=False)
    df = df[pandas.to_numeric(df['AHSW41:IST:2'], errors='coerce').notnull()]
    # return (df.df.to_dict('records'), 
    #        [{"name": i, "id": i, "hidable":True, "selectable":True} for i in df.df.columns])

    return df.head(100).to_html(header='true', table_id='epics', float_format=':.2f'.format)

@app.route("/generic.html")
def generic():
    return render_template("web/generic.html")

@app.route("/")
def home():
    print('This file location:', os.path.dirname(__file__))
    '''Landing page'''
    # app.logger.error('ding')
    return render_template(
        'web/index.html'
    )

@app.route("/files")
def files():
    from update_index import create_index
    create_index('../processed/', outfile='static/web/file-index.html')
    return render_template('web/file-index.html')

@app.route("/files/<int:run>")
def files_run(run):
    # from update_index import create_index
    # create_index('../processed/', outfile='static/web/file-index.html')
    # return render_template('web/file-index.html')
    return flask.redirect(f'/files#{run}')

@app.route('/browse/<path:req_path>')
def dir_listing(req_path):
    # Joining the base and the requested path
    abs_path = os.path.join(BASE_DIR, req_path)
    print(abs_path)

    # Return 404 if path doesn't exist
    if not os.path.exists(abs_path):
        return flask.abort(404)

    # Check if path is a file and serve
    if os.path.isfile(abs_path):
        return flask.send_file(abs_path)

@app.route('/runs/<int:run1>/<int:run2>')
def get_run_data(run1, run2):
    '''
        tars up run data and serves it to the user
    '''
    outfile = os.path.join(BASE_DIR,f'processed/tarfiles/nearline_runs_{run1}_{run2}.tar.gz')
    if(not os.path.exists(outfile)):
        command = f'tar -zcvf {outfile} -C {BASE_DIR}'
        for run in range(run1, run2+1):
            thisdir = f'processed/run{run}'
            if(os.path.exists(os.path.join(BASE_DIR, thisdir))):
                command += f' {thisdir} '

        print(command)
        os.system(command)
    else:
        print("Already processed!")

    if os.path.isfile(outfile):
        return flask.send_file(outfile)
    else:
        return flask.abort(404)

@app.route("/jsroot")
def jsroot():
    return render_template('web/jsroot.html')

if __name__ == "__main__":
    # app.run(host="localhost", port=1234, debug=True)
    app.run(host="0.0.0.0", port=1234, debug=True) 
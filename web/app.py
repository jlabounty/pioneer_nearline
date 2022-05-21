# from process_data import make_indir_outdir
# from pickle import NONE
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

FIG_DATATABLE = None
FIG_PLOTS = None
FIG_SCATTER = None

app = Flask(__name__, template_folder='static')
dashboard, df = create_dashboard(app)

# logging.t


@dashboard.callback(
    Output('runlog-datatable', 'data'), Output('runlog-datatable', 'columns'),
    Input("refresh-df", 'n_clicks'),
)
def refresh_runlog(click):
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
    app.logger.error("Rendering tab content...")
    if(value == 'runlog'):
        global FIG_DATATABLE
        # print( FIG_DATATABLE)
        if(FIG_DATATABLE is None):
            print('ding!!!')
            FIG_DATATABLE = render_datatable()
        else:
            print("dong")
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


# @dashboard.callback(
#     Output('tab-content', 'children'),
#     Input('tabs', 'value')
# )
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
                 html.Div([
                    dcc.Graph(
                        id='crossfilter-indicator-scatter',
                        # hoverData={'points': [{'customdata': 'Japan'}]}
                    )
                ], style={'width': '100%', 'display': 'inline-block', 'padding': '10 20'}),
                html.Div([
                    dcc.Graph(id='x-time-series'),
                ], style={'display': 'inline-block', 'width': '49%'}),
                html.Div([
                    dcc.Graph(id='y-time-series'),
                ], style={'display': 'inline-block', 'width': '49%'}),
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
    Input('crossfilter-xaxis-type', 'value'))
def update_y_timeseries(xaxis_column_name, axis_type):
    # country_name = hoverData['points'][0]['customdata']
    dff = df.df
    title = xaxis_column_name
    return create_time_series(dff, axis_type, title)


@dashboard.callback(
    Output('y-time-series', 'figure'),
    # Input('crossfilter-indicator-scatter', 'hoverData'),
    Input('crossfilter-yaxis-column', 'value'),
    Input('crossfilter-yaxis-type', 'value'))
def update_x_timeseries(yaxis_column_name, axis_type):
    dff = df.df
    title = yaxis_column_name
    return create_time_series(dff, axis_type, title)

@dashboard.callback(
    Output('crossfilter-indicator-scatter', 'figure'),
    Input('crossfilter-xaxis-column', 'value'),
    Input('crossfilter-yaxis-column', 'value'),
    Input('crossfilter-xaxis-type', 'value'),
    Input('crossfilter-yaxis-type', 'value'),
    # Input('crossfilter-hover-column', 'value'),
    # Input('crossfilter-year--slider', 'value')
    )
def update_graph(xaxis_column_name, yaxis_column_name,
                 xaxis_type, yaxis_type):
    # dff = df[df['Year'] == year_value]
    app.logger.error("Rendering data on graph...")
    dff = df.df

    fig = px.scatter(
        x=dff[xaxis_column_name],
        y=dff[yaxis_column_name],
        # hover_name=dff[indicator_name]
    )
    print(dff[xaxis_column_name])

    # fig.update_traces(customdata=dff[dff['Indicator Name'] == yaxis_column_name]['Country Name'])

    fig.update_xaxes(title=xaxis_column_name, type='linear' if xaxis_type == 'Linear' else 'log')
    fig.update_yaxes(title=yaxis_column_name, type='linear' if yaxis_type == 'Linear' else 'log')
    fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')

    return fig
    
# @dashboard.callback(
#     Output('profile-figure', 'figure'),
#     # Input('runlog-datatable', ''),
#     Input('runlog-datatable', 'derived_virtual_row_ids'),
#     Input('runlog-datatable', 'selected_row_ids'),
#     Input('runlog-datatable', 'active_cell')
# )
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
        dcc.Graph(id='profile-plot'),
        html.Iframe(src="",
            width="750",height="400",
            id='profile-pdf-display'
            # type="application/pdf"
        )
    )

def make_outdir(run,subrun):
    return f'../processed/run{run}/data/subrun{subrun}/'

# @dashboard.callback()

def get_profile_pdf(subrundir):
    thispath = os.path.join('assets',subrundir[3:], 'profile.pdf')
    print(thispath)
    if(not os.path.exists(thispath)):
        return None
    return thispath

@dashboard.callback(
    Output('profile-plot', 'figure'),
    Output('profile-pdf-display', 'src'),
    Input("crossfilter-run-select", 'value'),
    Input("crossfilter-subrun-select", 'value')
)
def update_display(run, subrun):

    # get the associated data file (if it exists, if not create it)
    # dfi = df.df.loc(df.df['run'] == int(run)).loc(df.df['subrun'] == int(subrun))
    outdir = make_outdir(run,subrun)
    csvfile = os.path.join(outdir,'profile.csv')
    print(csvfile)
    if(not os.path.exists(csvfile)):
        print("ERROR: CSV file not found")
        return px.scatter([],[])

    dfi = pandas.read_csv(csvfile, header=None)
    print(dfi.head)
    return (px.scatter(
        x=dfi[0],
        y=dfi[1],
        color=dfi[2],
        # hover_data=[0,1,2,3,4],
        # marker_symbol='s',
        # mode='markers'
        width=500, height=400
    )), get_profile_pdf( outdir )
    
    # return px.scatter([1,2,3], [3,4,5])

    

def make_profile(infile):
    return html.Div("todo")

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

@app.route('/browse/<path:req_path>')
def dir_listing(req_path):
    # import os
    BASE_DIR = '/home/jlab/github/pioneer_nearline/web/static/'

    # Joining the base and the requested path
    abs_path = os.path.join(BASE_DIR, req_path)
    print(abs_path)

    # Return 404 if path doesn't exist
    if not os.path.exists(abs_path):
        return flask.abort(404)

    # Check if path is a file and serve
    if os.path.isfile(abs_path):
        return flask.send_file(abs_path)


if __name__ == "__main__":
    app.run(host="localhost", port=1234, debug=True)

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
        return render_datatable()
    elif(value == 'plot'):
        return html.Div([html.H1("TODO: Add plotly express plot here")])
    elif(value == 'scatter'):
        return render_runlog_scatter()


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

                    style_table={
                        'height': 400,
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
                    dcc.RadioItems(
                        ['Linear', 'Log'],
                        'Linear',
                        id='crossfilter-xaxis-type',
                        labelStyle={'display': 'inline-block', 'marginTop': '5px'}
                    )
                ],
                style={'width': '49%', 'display': 'inline-block'}),

                html.Div([
                    dcc.Dropdown(
                        df.df.columns.unique(),
                        'm1',
                        id='crossfilter-yaxis-column'
                    ),
                    dcc.RadioItems(
                        ['Linear', 'Log'],
                        'Linear',
                        id='crossfilter-yaxis-type',
                        labelStyle={'display': 'inline-block', 'marginTop': '5px'}
                    )
                ], style={'width': '49%', 'float': 'right', 'display': 'inline-block'}),
                html.Div([dcc.Dropdown(
                        df.df.columns.unique(),
                        'm1',
                        id='crossfilter-hover-column'
                    )])
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
    Input('crossfilter-hover-column', 'value'),
    # Input('crossfilter-year--slider', 'value')
    )
def update_graph(xaxis_column_name, yaxis_column_name,
                 xaxis_type, yaxis_type, indicator_name):
    # dff = df[df['Year'] == year_value]
    app.logger.error("Rendering data on graph...")
    dff = df.df

    fig = px.scatter(
        x=dff[xaxis_column_name],
        y=dff[yaxis_column_name],
        hover_name=dff[indicator_name]
    )
    print(dff[xaxis_column_name])

    # fig.update_traces(customdata=dff[dff['Indicator Name'] == yaxis_column_name]['Country Name'])

    fig.update_xaxes(title=xaxis_column_name, type='linear' if xaxis_type == 'Linear' else 'log')
    fig.update_yaxes(title=yaxis_column_name, type='linear' if yaxis_type == 'Linear' else 'log')
    fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')

    return fig
    

def update_display(column):
    '''
        Updates the displayed scan based on the run/subrun which was clicked
    '''
    # get the run/subrun number from the plot

    # get the associated data file (if it exists, if not create it)

    # update the plot on Tab 2

@app.route("/")
def home():
    print('This file location:', os.path.dirname(__file__))
    '''Landing page'''
    # app.logger.error('ding')
    return render_template(
        'web/index.html'
    )


if __name__ == "__main__":
    app.run(host="localhost", port=1234, debug=True)

from dataclasses import dataclass
import dash 
from dash import html, dash_table, dcc
import pandas 
import base64
import os

@dataclass
class ReloadableDF:
    infile: str
    df:pandas.DataFrame

    def refresh(self):
        self.df = pandas.read_csv(self.infile)
        self.df.sort_values(by=['run', 'subrun'], inplace=True, ascending=False)


def create_dataframe(infile='../processed/run_db.csv'):
    '''
        Loads up the run db as a pandas dataframe
    '''
    df = ReloadableDF(infile, None)
    df.refresh()
    # pandas.read_csv(infile)
    return df


def create_dashboard(server, **kwargs):
    df = create_dataframe()

    dash_app = dash.Dash(
        server=server,
        routes_pathname_prefix='/dashapp/',
        # static_folder='static'
        **kwargs
    )

    # app.logger.debug("help")

    # @dash_app.callback()
    # def

    image_filename = 'web/images/pioneer_logo.png' # replace with your own image
    # encoded_image = base64.b64encode(open(image_filename, 'rb').read())
    print(dash_app.get_asset_url(image_filename))

    dash_app.layout = html.Div(
        id='dash-container',
        children=[
            html.A(
                [
                    html.Img(src=dash_app.get_asset_url(image_filename), height='2em'),
                    html.H1(children='Nearline Plot Visualization'),
                ], href='/'),
            html.Button('Refresh', id='refresh-df'),
            html.Div(children='''
                
                
            '''),
            dcc.Tabs(
                id='tabs',
                value='runlog',
                children = [
                    dcc.Tab(label='Run Conditions', value='runlog'),
                    dcc.Tab(label='Plots', value='plot'),
                    dcc.Tab(label='Scatter', value='scatter'),
                ]
            ),
            html.Div(id='tab-content')
        ]
    )


    return dash_app, df
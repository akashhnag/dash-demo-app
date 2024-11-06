from dash import Dash, dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Output, Input
from dash.exceptions import PreventUpdate
from dash_bootstrap_templates import load_figure_template

import plotly.express as px
import pandas as pd
import numpy as np

from numpy.random import default_rng
rng=default_rng(2023)

resorts = (
    pd.read_csv("resorts.csv", encoding = "ISO-8859-1")
    .assign(
        country_elevation_rank = lambda x: x.groupby("Country", as_index=False)["Highest point"].rank(ascending=False),
        country_price_rank = lambda x: x.groupby("Country", as_index=False)["Price"].rank(ascending=False),
        country_slope_rank = lambda x: x.groupby("Country", as_index=False)["Total slopes"].rank(ascending=False),
        country_cannon_rank = lambda x: x.groupby("Country", as_index=False)["Snow cannons"].rank(ascending=False),
    ))

partial_resort_data=resorts.head(20);


dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"

app = Dash(__name__, external_stylesheets=[dbc.themes.MORPH, dbc_css])

server=app.server

load_figure_template("MORPH")

app.layout = dbc.Container([
    dcc.Tabs(className="dbc", children = [
        dbc.Tab(label='Data Table',children=[
            html.Div([
            dbc.Row(
                dbc.Col([
                    
                    dash_table.DataTable(
                        columns=[{'name':i, 'id':i} for i in partial_resort_data.columns],
                    data=partial_resort_data.to_dict('records'),
                     style_table={
                        'overflowX': 'auto',
                        'overflowY': 'auto'
                    },
                     style_cell={'textAlign': 'left'},
                     style_header={
                        'fontWeight': 'bold'
                    },
                    style_data_conditional=[
        {
            'if': {'row_index': 'odd'},
            'backgroundColor': 'rgb(220, 220, 220)',
        }
    ],
                    
                    ) 
                    
                ])
            )     
            ],style={'width':'1300'})
                 
        ]),
        dbc.Tab(label="Country Profiler", children=[ 
            html.H1(id="country-title", style={"text-align": "center"}),
            dbc.Row([
                dbc.Col([
                    dcc.Markdown("Select A Continent:"),
                    dcc.Dropdown(
                        id="continent-dropdown",
                        options=resorts["Continent"].unique(),
                        value="Europe",
                        className="dbc"
                    ),
                    html.Br(),
                    dcc.Markdown("Select A Country:"),
                    dcc.Dropdown(id="country-dropdown", value="Norway", className="dbc"),
                    html.Br(),
                    dcc.Markdown("Select A Metric to Plot:"),
                    dcc.Dropdown(
                        id="column-picker",
                        options=resorts.select_dtypes("number").columns[3:],
                        value="Price",
                        className="dbc"
                    ),
                ], width=3),
                dbc.Col([dcc.Graph(id="metric-bar",
                                   hoverData={'points': [{'customdata': ['Hemsedal']}]})]
                        , width=6),
                dbc.Col([
                    dcc.Markdown("### Resort Report Card"),
                    dbc.Card(id="resort-name", style={"text-align": "center", "fontSize":20}),
                    dbc.Row([
                        dbc.Col([dbc.Card(id="elevation-kpi"), dbc.Card(id="price-kpi")]),
                        dbc.Col([dbc.Card(id="slope-kpi"), dbc.Card(id="cannon-kpi")]),
                    ])
                ], width=3)
            ])
        ]),
        dbc.Tab(label='Periodic callback',children=[
            html.Div([
    dbc.Row(html.H1('Normal Distribution Simulator', style={'text-align':'center'})),
    dbc.Row(
        dbc.Col(dcc.Graph(id='random-data-scatter')),
    ),
    dcc.Interval(id='refresh-data-interval', interval=1000)
])
        ])
    ])
], style={"width":1300})




@app.callback(
    Output("country-dropdown", "options"), 
    Input("continent-dropdown", "value"))
def country_select(continent):
    return np.sort(resorts.query("Continent == @continent").Country.unique())

@app.callback(
    Output("country-title", "children"),
    Output("metric-bar", "figure"),
    Input("country-dropdown", "value"),
    Input("column-picker", "value")
)
def plot_bar(country, metric): 
    if not country and metric:
        raise PreventUpdate
    title = f"Top Resorts in {country} by {metric}"
    
    df = resorts.query("Country == @country").sort_values(metric, ascending=False)
        
    figure = px.bar(df, x="Resort", y=metric, custom_data=["Resort"]).update_xaxes(showticklabels=False)
        
    return title, figure

@app.callback(
    Output("resort-name", "children"),
    Output("elevation-kpi", "children"),
    Output("price-kpi", "children"),
    Output("slope-kpi", "children"),
    Output("cannon-kpi", "children"),
    Input("metric-bar", "hoverData"))
def report_card(hoverData):
    resort = hoverData["points"][0]["customdata"][0]
    
    df = resorts.query("Resort == @resort")
    
    
    elev_rank = f"Elevation Rank: {int(df['country_elevation_rank'])}"
    price_rank = f"Price Rank: {int(df['country_price_rank'])}"
    slope_rank = f"Slope Rank: {int(df['country_slope_rank'])}"
    cannon_rank = f"Cannon Rank: {int(df['country_cannon_rank'])}"
    
    return resort, elev_rank, price_rank, slope_rank, cannon_rank 

@app.callback(Output('random-data-scatter','figure'),Input('refresh-data-interval','n_intervals'))
def rand_hist(n_intervals):
    mean, stddev=100,10
    fig=px.line(
        y=rng.normal(mean,stddev,size=100)
    )
    return fig

if __name__ == "__main__":
    app.run_server(port=2034)

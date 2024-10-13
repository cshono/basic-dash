import dash
from dash import dcc, html, callback, Input, Output
import plotly.express as px
import pandas as pd
from src.get_live_data import (
    plot_lmp_data, 
    plot_weather_data, 
    get_live_data, 
    LOCATION, 
    STATIONS,
    WEATHER_VARS,
)

# Sample data
df = pd.DataFrame({
    "Year": [2016, 2017, 2018, 2019, 2020],
    "Sales": [100, 150, 200, 250, 300]
})

# Create a line chart using Plotly Express
df_forecast = get_live_data(LOCATION, STATIONS)
lmp_fig = plot_lmp_data(df_forecast)

# Initialize the Dash app
app = dash.Dash(__name__)

# Expose the underlying Flask server
server = app.server

# Define the layout
app.layout = html.Div([
    html.H1("CAISO LMP Forecast"),
    html.H2(f"LMP: {LOCATION}"),
    dcc.Graph(
        id='lmp-fig',
        figure=lmp_fig
    ),
    html.H2("Weather Data"),
    dcc.Dropdown(
        id='weather-var-dropdown',
        value=WEATHER_VARS[0],
        options=WEATHER_VARS),
    dcc.Graph(
        id='weather-fig',
        figure={},
    ),
])

# Define Callbacks
@callback(
    Output('weather-fig', 'figure'),
    Input('weather-var-dropdown', 'value'),
)
def update_weather_fig(weather_var):
    return plot_weather_data(df_forecast, weather_var)

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

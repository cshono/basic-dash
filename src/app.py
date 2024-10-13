import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd

# Sample data
df = pd.DataFrame({
    "Year": [2016, 2017, 2018, 2019, 2020],
    "Sales": [100, 150, 200, 250, 300]
})

# Create a line chart using Plotly Express
fig = px.line(df, x="Year", y="Sales", title="Yearly Sales")

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout
app.layout = html.Div([
    html.H1("Basic Dash App"),
    dcc.Graph(
        id='line-chart',
        figure=fig
    )
])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

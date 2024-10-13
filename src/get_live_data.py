import pandas as pd
import pickle 
import requests
from datetime import datetime, timedelta
import pytz 
import gridstatus
import plotly.graph_objs as go 
import plotly.express as px 

# LMP params 
FORECAST_HORIZON_DAYS = 2
LOCATION = "SHILOH3_7_N002"
TARGET_COL = "LMP" 

# Weather params 
WEATHER_VARS = ["temperature","relativeHumidity","windSpeed"]
STATIONS = {
    "la": {
        "office": "LOX"
        , "gridX": 153
        , "gridY": 44
    }
    , "sd": {
        "office": "SGX"
        , "gridX": 58
        , "gridY": 18
    }
    , "sf": {
        "office": "MTR"
        , "gridX": 85
        , "gridY": 98
    }
}
TZ_NAME = 'Etc/GMT+8' 
MAX_INTERP_HRS = 4 
FILE_MODEL = "./src/models/model.pkl" 

def get_live_data(location, stations):
    # Get and Clean LMP Data 
    caiso = gridstatus.CAISO() 
    lmp_start = datetime.today().replace(minute=0, hour=0, second=0, microsecond=0) - timedelta(1) 
    lmp_end = lmp_start + timedelta(FORECAST_HORIZON_DAYS + 1) 
    df_lmp = caiso.get_lmp(start=lmp_start, end=lmp_end, market="DAY_AHEAD_HOURLY", locations=[location])
    df_lmp['datetime'] = pd.to_datetime(df_lmp['Time']) 
    df_lmp = df_lmp.set_index("datetime").drop("Time", axis=1) 
    df_lmp.index = df_lmp.index.tz_convert(TZ_NAME) # Also PST does not exist in Python boo.... (despite EST and MST existing) 
    df_lmp = df_lmp.loc[df_lmp.Location == location, TARGET_COL] 

    # Create df_test 
    df_forecast = df_lmp.copy() 

    # Get and clean weather data 
    for station in stations.keys(): 
        office = stations[station]['office']
        gridX = stations[station]['gridX'] 
        gridY = stations[station]['gridY'] 
        url = f'https://api.weather.gov/gridpoints/{office}/{gridX},{gridY}/forecast/hourly'
        response = requests.get(url)

        # Parse and Clean Data 
        df_weather = response.json()['properties']['periods']
        df_weather = pd.DataFrame(df_weather) 
        df_weather = df_weather[['startTime', 'temperature', 'relativeHumidity', 'windSpeed']]
        df_weather['datetime'] = pd.to_datetime(df_weather['startTime'])
        df_weather = df_weather.set_index("datetime").drop("startTime", axis=1) 
        df_weather.index = df_weather.index.tz_convert(TZ_NAME) 
        end_datetime = datetime.now(pytz.timezone(TZ_NAME)) + timedelta(FORECAST_HORIZON_DAYS + 1) 
        end_datetime = end_datetime.replace(minute=0, hour=0, second=0, microsecond=0)
        df_weather = df_weather.loc[df_weather.index < end_datetime]
        df_weather["relativeHumidity"] = df_weather["relativeHumidity"].apply(lambda x: x['value']) 
        df_weather["windSpeed"] = df_weather["windSpeed"].apply(lambda x: float(x.replace("mph",""))) 
        df_weather = df_weather.resample("H").mean().interpolate(limit=MAX_INTERP_HRS)
        df_weather.columns = [f'{c}_{station}' for c in df_weather.columns] 
        df_forecast = pd.concat([df_forecast, df_weather], axis=1) 

    # Extract Time Features 
    df_forecast["hour"] = df_forecast.index.hour 
    df_forecast["month"] = df_forecast.index.month 
    df_forecast["LMP_lag48"] = df_forecast["LMP"].shift(48) 

    # Make Predictions 
    clf = pickle.load(open(FILE_MODEL, 'rb'))
    feature_cols = clf.__dict__['feature_names_in_']
    X_forecast = df_forecast[feature_cols].dropna()
    y_forecast = clf.predict(X_forecast) 
    y_forecast = pd.Series(y_forecast, index=X_forecast.index) 
    df_forecast["LMP Forecast"] = y_forecast 
    
    return df_forecast

def plot_lmp_data(df_forecast):
    traces = [
        go.Scatter(
            x=df_forecast.index,
            y=df_forecast["LMP"],
            name="LMP Actual",
            mode="lines",
            line={"color": px.colors.qualitative.G10[0]}
        ),
        go.Scatter(
            x=df_forecast.index,
            y=df_forecast["LMP Forecast"],
            name="LMP Forecast",  
            line={"color": px.colors.qualitative.G10[1]}
        )
    ]
    fig = go.Figure(data=traces)
    return fig

def plot_weather_data(df_forecast, weather_col):
    plot_cols = [c for c in df_forecast if weather_col in c]
    traces = []
    for i, plot_col in enumerate(plot_cols):
        traces.append(
            go.Scatter(
                x=df_forecast.index,
                y=df_forecast[plot_col],
                name=plot_col,
                mode='lines',
                line=dict(color=px.colors.qualitative.G10[i])
            )
        )
    fig = go.Figure(data=traces)
    return fig 
        

if __name__ == "__main__":
    df_forecast = get_live_data(LOCATION, STATIONS)
    
    # Plot data 
    # fig, axs = plt.subplots(4,1,sharex=True) 
    # df_forecast[["LMP", "LMP Forecast"]].rename(columns={"LMP": "Actual", "LMP Forecast": "Forecast"}).plot(ax=axs[0], alpha=0.7) 
    # df_forecast[[c for c in df_forecast if "temperature" in c]].plot(ax=axs[1], alpha=0.8) 
    # df_forecast[[c for c in df_forecast if "relativeHumidity" in c]].plot(ax=axs[2], alpha=0.8) 
    # df_forecast[[c for c in df_forecast if "windSpeed" in c]].plot(ax=axs[3], alpha=0.8) 
    # plt.legend(loc="upper left") 
    # plt.show() 

    fig = plot_weather_data(df_forecast, "temperature")
    fig.show()
    
    
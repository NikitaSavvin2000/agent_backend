import pandas as pd
import plotly.graph_objects as go

class VizAgent:
    async def handle(self, df_real, df_forecast, time_col, target_col):
        df_forecast = pd.DataFrame(df_forecast["map_data"]["data"]["predictions"])
        df_real = df_real[-len(df_forecast):]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_real[time_col], y=df_real[target_col], name="Реальные"))
        fig.add_trace(go.Scatter(x=df_forecast[time_col], y=df_forecast[target_col], name="Прогноз"))
        return fig

import pandas as pd
import plotly.graph_objects as go
import numpy as np

class VizAgent:
    async def handle(self, df_real, df_forecast, time_col, target_col):
        print("df_forecast-"*18)
        print(df_forecast)

        df_real = df_real[-len(df_forecast):]
        df_data = pd.concat([df_forecast, df_real], axis=0).sort_values(by=time_col).reset_index(drop=True)
        print(df_data)
        df_data = df_data.replace([np.inf, -np.inf], np.nan)
        df_data = df_data.where(pd.notna(df_data), None)
        print("="*150)
        print(df_data)
        json_data = df_data.to_dict(orient="records")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_real[time_col], y=df_real[target_col], name="Реальные"))
        fig.add_trace(go.Scatter(x=df_forecast[time_col], y=df_forecast[target_col], name="Прогноз"))
        html_output = fig.to_html()
        return html_output, json_data

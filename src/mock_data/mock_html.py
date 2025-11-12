import plotly.graph_objs as go
import pandas as pd
import numpy as np
import uuid
import os

home = os.getcwd()
mock_html_path = os.path.join(home, "src", "mock_data", "mock_chart.html")

def generate_mock_timeseries_html(df) -> str:
    target_col = "vc_fact"
    time_col = "datetime"
    df = df.sort_values(by=time_col).reset_index(drop=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[time_col],
        y=df[target_col],
        mode="lines+markers",
        line=dict(color=f"#{uuid.uuid4().hex[:6]}"),  # случайный цвет линии
        name="Mock Series"
    ))

    path = os.path.join(os.getcwd(), mock_html_path)
    fig.write_html(path)
    return path

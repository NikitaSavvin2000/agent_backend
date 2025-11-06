import plotly.graph_objs as go
import pandas as pd
import numpy as np
import uuid
import os

home = os.getcwd()
mock_html_path = os.path.join(home, "src", "mock_data", "mock_chart.html")

def generate_mock_timeseries_html() -> str:
    np.random.seed()
    dates = pd.date_range(start="2025-01-01", periods=50)
    values = np.random.randn(50).cumsum()
    df = pd.DataFrame({"date": dates, "value": values})

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["value"],
        mode="lines+markers",
        line=dict(color=f"#{uuid.uuid4().hex[:6]}"),  # случайный цвет линии
        name="Mock Series"
    ))

    path = os.path.join(os.getcwd(), mock_html_path)
    fig.write_html(path)
    return path

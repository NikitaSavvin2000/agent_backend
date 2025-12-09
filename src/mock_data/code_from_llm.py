import pandas as pd
import plotly.express as px
df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
fig = px.line(df, x='datetime', y='vc_fact', title='Фактическое потребление по времени')
fig.update_layout(xaxis_title='Дата и время', yaxis_title='Фактическое потребление, кВт*ч')
html_output = fig.to_html()
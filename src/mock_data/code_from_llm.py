import pandas as pd
import plotly.express as px

df['year_month'] = pd.to_datetime(df['year_month'], errors='coerce')
df['month'] = df['year_month'].dt.month
df_result = df.groupby('month', as_index=False)['sum'].mean()
fig = px.bar(df_result, x='month', y='sum')
html_output = fig.to_html()
import plotly.express as px
import pandas as pd

df_result = df.reset_index().rename(columns={'index': 'model'})
df_result['model_short'] = df_result['model'].apply(lambda x: x.split('/')[-1] if isinstance(x, str) else str(x))
fig = px.bar(df_result, x='model_short', y=['perplexity', 'acc@1'], barmode='group', title='Scoring of Models')
fig.update_layout(xaxis_title='Model', yaxis_title='Score')
html_output = fig.to_html()
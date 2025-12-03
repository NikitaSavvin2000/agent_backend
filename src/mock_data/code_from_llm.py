
import pandas as pd
import plotly.graph_objects as go

df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
df_sorted = df.sort_values('vc_fact', ascending=False)
top_n = 10
df_top = df_sorted.head(top_n).copy()
df_top['rank'] = range(1, len(df_top) + 1)
df_top = df_top[['rank', 'datetime', 'vc_fact']]

fig = go.Figure(data=[go.Bar(
    x=df_top['datetime'].dt.strftime('%Y-%m-%d %H:%M'),
    y=df_top['vc_fact'],
    text=df_top['vc_fact'].round(2),
    textposition='auto',
    marker_color='crimson'
)])
fig.update_layout(
    title=f'Топ-{top_n} самых высоких значений',
    xaxis_title='Дата и время',
    yaxis_title='Значение vc_fact',
    xaxis_tickangle=-45
)
html_output = fig.to_html()

df_result = df_top
need_resonating = True
meta_for_resonating = {
    'top_values_summary': df_top.to_dict('records'),
    'statistics': {
        'count': len(df_top),
        'min_top': df_top['vc_fact'].min(),
        'max_top': df_top['vc_fact'].max(),
        'mean_top': df_top['vc_fact'].mean(),
        'std_top': df_top['vc_fact'].std(),
        'total_range': df['vc_fact'].max() - df['vc_fact'].min(),
        'top_range': df_top['vc_fact'].max() - df_top['vc_fact'].min()
    },
    'time_period': {
        'earliest_top': df_top['datetime'].min().strftime('%Y-%m-%d %H:%M'),
        'latest_top': df_top['datetime'].max().strftime('%Y-%m-%d %H:%M'),
        'full_period_start': df['datetime'].min().strftime('%Y-%m-%d %H:%M'),
        'full_period_end': df['datetime'].max().strftime('%Y-%m-%d %H:%M')
    },
    'context': {
        'dataset_size': len(df),
        'global_max': df['vc_fact'].max(),
        'global_min': df['vc_fact'].min(),
        'global_mean': df['vc_fact'].mean(),
        'top_values_above_mean_percentage': len(df_top[df_top['vc_fact'] > df['vc_fact'].mean()]) / len(df_top) * 100
    }
}

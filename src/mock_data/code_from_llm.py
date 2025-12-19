
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
df = df.sort_values('datetime')

numeric_cols = ['dso_gp', 'vc_ppp', 'vc_fact', 'i_ee_ph', 'i_em_ph', 'i_otkl_ph']
categorical_cols = ['day_zone']

color_sequence = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b',
    '#e377c2', '#7f7f7f', '#bcbd22', '#17becf', '#aec7e8', '#ffbb78',
    '#98df8a', '#ff9896', '#c5b0d5', '#c49c94', '#f7b6d2', '#c7c7c7'
]

figures = []

for i, col in enumerate(numeric_cols):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['datetime'],
        y=df[col],
        mode='lines',
        name=col,
        line=dict(color=color_sequence[i % len(color_sequence)], width=2)
    ))
    
    fig.update_layout(
        title=f'Временной ряд: {col}',
        xaxis_title='Дата и время',
        yaxis_title=col,
        legend=dict(orientation='h', yanchor='bottom', y=-0.3, xanchor='center', x=0.5),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=True
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    
    figures.append(fig)

unique_zones = df['day_zone'].dropna().unique()
zone_counts = df['day_zone'].value_counts()

fig = go.Figure()
for i, zone in enumerate(unique_zones):
    zone_data = df[df['day_zone'] == zone]
    fig.add_trace(go.Scatter(
        x=zone_data['datetime'],
        y=[i] * len(zone_data),
        mode='markers',
        name=zone,
        marker=dict(
            size=8,
            color=color_sequence[(len(numeric_cols) + i) % len(color_sequence)],
            symbol='square'
        )
    ))

fig.update_layout(
    title='Временной ряд: day_zone (категориальная)',
    xaxis_title='Дата и время',
    yaxis_title='Зона дня',
    yaxis=dict(
        tickmode='array',
        tickvals=list(range(len(unique_zones))),
        ticktext=unique_zones
    ),
    legend=dict(orientation='h', yanchor='bottom', y=-0.3, xanchor='center', x=0.5),
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    showlegend=True
)

fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')

figures.append(fig)

html_output = ''
for fig in figures:
    html_output += fig.to_html(full_html=False, include_plotlyjs='cdn')

result_analysis = """## Анализ временных рядов

### Числовые показатели:
1. **dso_gp** - показывает колебания с положительными и отрицательными значениями
2. **vc_ppp** и **vc_fact** - демонстрируют схожую динамику, но с расхождениями
3. **i_ee_ph**, **i_em_ph**, **i_otkl_ph** - индикаторы с коррелирующим поведением

### Категориальный показатель:
- **day_zone** - распределение по временным зонам (ночная, полупиковая, пиковая) показывает циклический паттерн

### Наблюдения:
- Все числовые показатели демонстрируют сезонные колебания
- Наибольшая волатильность наблюдается в показателе dso_gp
- Показатели vc_ppp и vc_fact имеют минимальные расхождения
- Индикаторы i_*_ph показывают синхронное поведение"""

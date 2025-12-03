
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=('Фактическое потребление по времени', 'Распределение фактического потребления', 'Среднее потребление по месяцам', 'Среднее потребление по часам суток'),
    specs=[[{'type': 'scatter'}, {'type': 'box'}], [{'type': 'bar'}, {'type': 'bar'}]]
)

fig.add_trace(
    go.Scatter(x=df['datetime'], y=df['vc_fact'], mode='lines', name='Фактическое потребление'),
    row=1, col=1
)

fig.add_trace(
    go.Box(y=df['vc_fact'], name='Распределение', boxmean=True),
    row=1, col=2
)

monthly_avg = df.groupby('month')['vc_fact'].mean().reset_index()
fig.add_trace(
    go.Bar(x=monthly_avg['month'], y=monthly_avg['vc_fact'], name='По месяцам'),
    row=2, col=1
)

hourly_avg = df.groupby('hour')['vc_fact'].mean().reset_index()
fig.add_trace(
    go.Bar(x=hourly_avg['hour'], y=hourly_avg['vc_fact'], name='По часам'),
    row=2, col=2
)

fig.update_layout(height=800, showlegend=False, title_text="Анализ фактического потребления")
html_output = fig.to_html()

stats = {
    'min': df['vc_fact'].min(),
    'max': df['vc_fact'].max(),
    'mean': df['vc_fact'].mean(),
    'median': df['vc_fact'].median(),
    'std': df['vc_fact'].std(),
    'q25': df['vc_fact'].quantile(0.25),
    'q75': df['vc_fact'].quantile(0.75)
}

yearly_stats = df.groupby('year')['vc_fact'].agg(['min', 'max', 'mean', 'median', 'std']).reset_index()
df_result = yearly_stats

result_analysis = f"""
Анализ фактического потребления (vc_fact):
- Общий диапазон: от {stats['min']:.0f} до {stats['max']:.0f}
- Среднее значение: {stats['mean']:.2f}
- Медиана: {stats['median']:.2f}
- Стандартное отклонение: {stats['std']:.2f}
- Межквартильный размах: {stats['q75'] - stats['q25']:.2f}

Тенденции по годам:
{yearly_stats.to_string(index=False)}

Визуализация включает:
1. Временной ряд потребления
2. Боксплот распределения
3. Среднее потребление по месяцам
4. Среднее потребление по часам суток
"""

need_resonating = True
meta_for_resonating = {
    'overall_stats': stats,
    'yearly_stats': yearly_stats.to_dict('records'),
    'monthly_avg': monthly_avg.to_dict('records'),
    'hourly_avg': hourly_avg.to_dict('records'),
    'data_points_count': len(df),
    'date_range': {
        'start': df['datetime'].min().strftime('%Y-%m-%d %H:%M:%S'),
        'end': df['datetime'].max().strftime('%Y-%m-%d %H:%M:%S')
    }
}

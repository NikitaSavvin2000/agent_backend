
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

df['date'] = pd.to_datetime(df['date'], errors='coerce')

fig = make_subplots(
    rows=3, cols=2,
    subplot_titles=('Общее дневное потребление', 'Среднее почасовое потребление', 
                    'Минимальное почасовое', 'Максимальное почасовое',
                    'Стандартное отклонение почасового', 'Сравнение метрик'),
    specs=[[{'secondary_y': False}, {'secondary_y': False}],
           [{'secondary_y': False}, {'secondary_y': False}],
           [{'secondary_y': False}, {'secondary_y': False}]]
)

fig.add_trace(
    go.Scatter(x=df['date'], y=df['total_daily'], mode='lines', name='total_daily'),
    row=1, col=1
)

fig.add_trace(
    go.Scatter(x=df['date'], y=df['avg_hourly'], mode='lines', name='avg_hourly'),
    row=1, col=2
)

fig.add_trace(
    go.Scatter(x=df['date'], y=df['min_hourly'], mode='lines', name='min_hourly'),
    row=2, col=1
)

fig.add_trace(
    go.Scatter(x=df['date'], y=df['max_hourly'], mode='lines', name='max_hourly'),
    row=2, col=2
)

fig.add_trace(
    go.Scatter(x=df['date'], y=df['std_hourly'], mode='lines', name='std_hourly'),
    row=3, col=1
)

fig.add_trace(
    go.Scatter(x=df['date'], y=df['avg_hourly'], mode='lines', name='avg_hourly', line=dict(color='blue')),
    row=3, col=2
)
fig.add_trace(
    go.Scatter(x=df['date'], y=df['min_hourly'], mode='lines', name='min_hourly', line=dict(color='green')),
    row=3, col=2, secondary_y=False
)
fig.add_trace(
    go.Scatter(x=df['date'], y=df['max_hourly'], mode='lines', name='max_hourly', line=dict(color='red')),
    row=3, col=2, secondary_y=False
)

fig.update_layout(height=1200, showlegend=True, title_text="Анализ фактического потребления")

html_output = fig.to_html()

df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['quarter'] = df['date'].dt.quarter

yearly_stats = df.groupby('year').agg({
    'total_daily': ['mean', 'min', 'max', 'std'],
    'avg_hourly': ['mean', 'min', 'max', 'std'],
    'min_hourly': ['mean', 'min', 'max', 'std'],
    'max_hourly': ['mean', 'min', 'max', 'std'],
    'std_hourly': ['mean', 'min', 'max', 'std']
}).round(2)

monthly_stats = df.groupby('month').agg({
    'total_daily': ['mean', 'min', 'max', 'std'],
    'avg_hourly': ['mean', 'min', 'max', 'std']
}).round(2)

quarterly_stats = df.groupby('quarter').agg({
    'total_daily': ['mean', 'min', 'max', 'std'],
    'avg_hourly': ['mean', 'min', 'max', 'std']
}).round(2)

df['daily_range'] = df['max_hourly'] - df['min_hourly']
df['variation_coef'] = (df['std_hourly'] / df['avg_hourly'] * 100).round(2)

overall_stats = {
    'total_daily_mean': df['total_daily'].mean(),
    'total_daily_std': df['total_daily'].std(),
    'avg_hourly_mean': df['avg_hourly'].mean(),
    'avg_hourly_std': df['avg_hourly'].std(),
    'min_hourly_mean': df['min_hourly'].mean(),
    'max_hourly_mean': df['max_hourly'].mean(),
    'daily_range_mean': df['daily_range'].mean(),
    'variation_coef_mean': df['variation_coef'].mean(),
    'total_records': len(df),
    'date_range_start': df['date'].min(),
    'date_range_end': df['date'].max()
}

df_result = pd.DataFrame({
    'yearly_stats': [yearly_stats.to_dict()],
    'monthly_stats': [monthly_stats.to_dict()],
    'quarterly_stats': [quarterly_stats.to_dict()],
    'overall_stats': [overall_stats]
})

result_analysis = f"""
Анализ фактического потребления за период с {df['date'].min().date()} по {df['date'].max().date()}:

1. Общие показатели:
   - Среднее дневное потребление: {overall_stats['total_daily_mean']:.2f} (σ={overall_stats['total_daily_std']:.2f})
   - Среднее почасовое потребление: {overall_stats['avg_hourly_mean']:.2f} (σ={overall_stats['avg_hourly_std']:.2f})
   - Средний дневной диапазон: {overall_stats['daily_range_mean']:.2f}
   - Средний коэффициент вариации: {overall_stats['variation_coef_mean']:.2f}%

2. Временные паттерны:
   - Данные охватывают {overall_stats['total_records']} дней
   - Анализ по годам, месяцам и кварталам доступен в df_result

3. Стабильность потребления:
   - Минимальное почасовое: {overall_stats['min_hourly_mean']:.2f}
   - Максимальное почасовое: {overall_stats['max_hourly_mean']:.2f}
   - Разброс между min и max составляет примерно {((overall_stats['max_hourly_mean'] - overall_stats['min_hourly_mean']) / overall_stats['avg_hourly_mean'] * 100):.1f}% от среднего
"""

need_resonating = True
meta_for_resonating = {
    'data_points': len(df),
    'date_range': {'start': str(df['date'].min()), 'end': str(df['date'].max())},
    'key_metrics': {
        'total_daily': {'mean': float(df['total_daily'].mean()), 'std': float(df['total_daily'].std())},
        'avg_hourly': {'mean': float(df['avg_hourly'].mean()), 'std': float(df['avg_hourly'].std())},
        'min_hourly': {'mean': float(df['min_hourly'].mean())},
        'max_hourly': {'mean': float(df['max_hourly'].mean())},
        'std_hourly': {'mean': float(df['std_hourly'].mean())}
    },
    'aggregations': {
        'yearly': yearly_stats.to_dict(),
        'monthly': monthly_stats.to_dict(),
        'quarterly': quarterly_stats.to_dict()
    },
    'calculated_metrics': {
        'daily_range_mean': float(df['daily_range'].mean()),
        'variation_coef_mean': float(df['variation_coef'].mean())
    }
}

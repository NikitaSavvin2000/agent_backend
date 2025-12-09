
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')

df['date'] = df['datetime'].dt.date
df['hour'] = df['datetime'].dt.hour
df['month'] = df['datetime'].dt.month
df['day_of_week'] = df['datetime'].dt.dayofweek

daily_consumption = df.groupby('date')['vc_fact'].agg(['sum', 'mean', 'min', 'max']).reset_index()
daily_consumption.columns = ['date', 'total_daily', 'avg_hourly', 'min_hourly', 'max_hourly']

hourly_pattern = df.groupby('hour')['vc_fact'].agg(['mean', 'std']).reset_index()
hourly_pattern.columns = ['hour', 'avg_consumption', 'std_consumption']

monthly_consumption = df.groupby('month')['vc_fact'].agg(['sum', 'mean']).reset_index()
monthly_consumption.columns = ['month', 'total_monthly', 'avg_daily']

weekday_consumption = df.groupby('day_of_week')['vc_fact'].mean().reset_index()
weekday_consumption.columns = ['day_of_week', 'avg_consumption']

zone_consumption = df.groupby('day_zone')['vc_fact'].agg(['sum', 'mean', 'count']).reset_index()
zone_consumption.columns = ['day_zone', 'total_consumption', 'avg_hourly', 'hours_count']

fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=daily_consumption['date'], y=daily_consumption['total_daily'],
                         mode='lines', name='Суточное потребление'))
fig1.update_layout(title='Динамика суточного потребления', xaxis_title='Дата', yaxis_title='Потребление')
html_output1 = fig1.to_html()

fig2 = make_subplots(rows=2, cols=2, subplot_titles=('Среднее по часам', 'Суммарное по месяцам',
                                                    'Среднее по дням недели', 'Потребление по зонам'))
fig2.add_trace(go.Scatter(x=hourly_pattern['hour'], y=hourly_pattern['avg_consumption'],
                         mode='lines+markers', name='Среднее'), row=1, col=1)
fig2.add_trace(go.Bar(x=monthly_consumption['month'], y=monthly_consumption['total_monthly'],
                     name='Сумма'), row=1, col=2)
fig2.add_trace(go.Bar(x=weekday_consumption['day_of_week'], y=weekday_consumption['avg_consumption'],
                     name='Среднее'), row=2, col=1)
fig2.add_trace(go.Bar(x=zone_consumption['day_zone'], y=zone_consumption['avg_hourly'],
                     name='Среднее'), row=2, col=2)
fig2.update_layout(height=800, showlegend=False)
html_output2 = fig2.to_html()

stats_summary = {
    'total_consumption': df['vc_fact'].sum(),
    'avg_hourly': df['vc_fact'].mean(),
    'min_hourly': df['vc_fact'].min(),
    'max_hourly': df['vc_fact'].max(),
    'std_hourly': df['vc_fact'].std(),
    'data_points': len(df),
    'date_range': f"{df['datetime'].min()} - {df['datetime'].max()}"
}

result_analysis = f"""
Анализ фактического потребления (vc_fact):
1. Общий объем потребления: {stats_summary['total_consumption']:,.0f} единиц
2. Среднее часовое потребление: {stats_summary['avg_hourly']:,.0f} ± {stats_summary['std_hourly']:,.0f}
3. Диапазон часового потребления: от {stats_summary['min_hourly']:,.0f} до {stats_summary['max_hourly']:,.0f}
4. Период анализа: {stats_summary['date_range']}
5. Количество часовых наблюдений: {stats_summary['data_points']}

Основные паттерны:
- Суточная динамика показывает {hourly_pattern.loc[hourly_pattern['avg_consumption'].idxmax(), 'hour']}:00 как час пик
- Месячное распределение: максимум в месяце {monthly_consumption.loc[monthly_consumption['total_monthly'].idxmax(), 'month']}
- По зонам суток: наибольшее среднее потребление в зоне '{zone_consumption.loc[zone_consumption['avg_hourly'].idxmax(), 'day_zone']}'
"""

need_resonating = True
meta_for_resonating = {
    'daily_stats': daily_consumption.to_dict('records'),
    'hourly_pattern': hourly_pattern.to_dict('records'),
    'monthly_stats': monthly_consumption.to_dict('records'),
    'zone_stats': zone_consumption.to_dict('records'),
    'summary_stats': stats_summary,
    'anomaly_threshold': stats_summary['avg_hourly'] + 2 * stats_summary['std_hourly']
}

df_result = daily_consumption.copy()

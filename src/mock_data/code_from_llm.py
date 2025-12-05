
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')

df['date'] = df['datetime'].dt.date
df['hour'] = df['datetime'].dt.hour
df['month'] = df['datetime'].dt.month
df['day_of_week'] = df['datetime'].dt.dayofweek

daily_consumption = df.groupby('date')['vc_fact'].agg(['sum', 'mean', 'min', 'max', 'std']).reset_index()
daily_consumption.columns = ['date', 'total_daily', 'avg_hourly', 'min_hourly', 'max_hourly', 'std_hourly']

hourly_pattern = df.groupby('hour')['vc_fact'].agg(['mean', 'std']).reset_index()
hourly_pattern.columns = ['hour', 'avg_consumption', 'std_consumption']

monthly_consumption = df.groupby('month')['vc_fact'].agg(['sum', 'mean', 'std']).reset_index()
monthly_consumption.columns = ['month', 'total_monthly', 'avg_daily', 'std_daily']

day_zone_stats = df.groupby('day_zone')['vc_fact'].agg(['sum', 'mean', 'std', 'count']).reset_index()
day_zone_stats.columns = ['day_zone', 'total_consumption', 'avg_consumption', 'std_consumption', 'count']

fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=daily_consumption['date'], y=daily_consumption['total_daily'],
                         mode='lines+markers', name='Суточное потребление',
                         line=dict(color='blue', width=2)))
fig1.update_layout(title='Динамика суточного потребления (vc_fact)',
                  xaxis_title='Дата',
                  yaxis_title='Потребление, кВт·ч',
                  template='plotly_white')
html_output1 = fig1.to_html()

fig2 = make_subplots(rows=2, cols=2,
                    subplot_titles=('Среднее потребление по часам', 'Суммарное потребление по месяцам',
                                   'Распределение по зонам суток', 'Статистика по дням недели'))

fig2.add_trace(go.Scatter(x=hourly_pattern['hour'], y=hourly_pattern['avg_consumption'],
                         mode='lines+markers', name='Среднее по часам',
                         line=dict(color='green', width=2)),
              row=1, col=1)

fig2.add_trace(go.Bar(x=monthly_consumption['month'], y=monthly_consumption['total_monthly'],
                     name='Сумма по месяцам',
                     marker_color='orange'),
              row=1, col=2)

fig2.add_trace(go.Bar(x=day_zone_stats['day_zone'], y=day_zone_stats['total_consumption'],
                     name='Потребление по зонам',
                     marker_color='purple'),
              row=2, col=1)

day_of_week_stats = df.groupby('day_of_week')['vc_fact'].mean().reset_index()
fig2.add_trace(go.Bar(x=day_of_week_stats['day_of_week'], y=day_of_week_stats['vc_fact'],
                     name='Среднее по дням недели',
                     marker_color='red'),
              row=2, col=2)

fig2.update_layout(height=800, showlegend=False, template='plotly_white')
html_output2 = fig2.to_html()

fig3 = px.box(df, x='day_zone', y='vc_fact',
             title='Распределение потребления по зонам суток',
             labels={'vc_fact': 'Фактическое потребление', 'day_zone': 'Зона суток'})
html_output3 = fig3.to_html()

top_days = daily_consumption.nlargest(10, 'total_daily')[['date', 'total_daily', 'max_hourly']]
bottom_days = daily_consumption.nsmallest(10, 'total_daily')[['date', 'total_daily', 'min_hourly']]

hourly_heatmap_data = df.pivot_table(index='hour', columns='day_of_week',
                                    values='vc_fact', aggfunc='mean')
fig4 = go.Figure(data=go.Heatmap(z=hourly_heatmap_data.values,
                                 x=['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
                                 y=hourly_heatmap_data.index,
                                 colorscale='Viridis'))
fig4.update_layout(title='Тепловая карта: среднее потребление по часам и дням недели',
                  xaxis_title='День недели',
                  yaxis_title='Час дня')
html_output4 = fig4.to_html()

vc_fact_stats = {
    'total_consumption': df['vc_fact'].sum(),
    'average_hourly': df['vc_fact'].mean(),
    'median_hourly': df['vc_fact'].median(),
    'std_hourly': df['vc_fact'].std(),
    'min_hourly': df['vc_fact'].min(),
    'max_hourly': df['vc_fact'].max(),
    'q1': df['vc_fact'].quantile(0.25),
    'q3': df['vc_fact'].quantile(0.75),
    'cv': (df['vc_fact'].std() / df['vc_fact'].mean()) * 100
}

result_analysis = f"""
Анализ фактического потребления (vc_fact):
1. Общее потребление за период: {vc_fact_stats['total_consumption']:,.0f} кВт·ч
2. Среднее часовое потребление: {vc_fact_stats['average_hourly']:,.0f} кВт·ч
3. Медианное часовое потребление: {vc_fact_stats['median_hourly']:,.0f} кВт·ч
4. Стандартное отклонение: {vc_fact_stats['std_hourly']:,.0f} кВт·ч
5. Коэффициент вариации: {vc_fact_stats['cv']:.1f}% (умеренная изменчивость)
6. Диапазон: от {vc_fact_stats['min_hourly']:,.0f} до {vc_fact_stats['max_hourly']:,.0f} кВт·ч
7. Межквартильный размах: {vc_fact_stats['q3'] - vc_fact_stats['q1']:,.0f} кВт·ч

Основные выводы:
- Максимальное суточное потребление: {top_days.iloc[0]['total_daily']:,.0f} кВт·ч ({top_days.iloc[0]['date']})
- Минимальное суточное потребление: {bottom_days.iloc[0]['total_daily']:,.0f} кВт·ч ({bottom_days.iloc[0]['date']})
- Пиковая зона имеет наибольшее суммарное потребление: {day_zone_stats[day_zone_stats['day_zone'] == 'Пиковая зона']['total_consumption'].values[0]:,.0f} кВт·ч
- Наиболее стабильное потребление наблюдается в {hourly_pattern.loc[hourly_pattern['std_consumption'].idxmin()]['hour']}:00 час
"""

df_result = daily_consumption.copy()

need_resonating = True
meta_for_resonating = {
    'vc_fact_stats': vc_fact_stats,
    'top_days': top_days.to_dict('records'),
    'bottom_days': bottom_days.to_dict('records'),
    'day_zone_distribution': day_zone_stats.to_dict('records'),
    'hourly_pattern': hourly_pattern.to_dict('records'),
    'monthly_totals': monthly_consumption.to_dict('records'),
    'anomaly_threshold': vc_fact_stats['q3'] + 1.5 * (vc_fact_stats['q3'] - vc_fact_stats['q1'])
}


import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, timedelta

df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
df = df.sort_values('datetime').reset_index(drop=True)

df['date'] = df['datetime'].dt.date
df['hour'] = df['datetime'].dt.hour
df['day_of_week'] = df['datetime'].dt.dayofweek
df['day_name'] = df['datetime'].dt.day_name()
df['month'] = df['datetime'].dt.month
df['is_weekend'] = df['day_of_week'].isin([5, 6])

daily_stats = df.groupby('date').agg({
    'vc_fact': ['mean', 'min', 'max', 'std', 'sum']
}).round(2)
daily_stats.columns = ['daily_mean', 'daily_min', 'daily_max', 'daily_std', 'daily_sum']
daily_stats = daily_stats.reset_index()

hourly_stats = df.groupby('hour').agg({
    'vc_fact': ['mean', 'min', 'max', 'std']
}).round(2)
hourly_stats.columns = ['hourly_mean', 'hourly_min', 'hourly_max', 'hourly_std']
hourly_stats = hourly_stats.reset_index()

weekday_stats = df.groupby(['day_of_week', 'day_name']).agg({
    'vc_fact': ['mean', 'min', 'max', 'std', 'count']
}).round(2)
weekday_stats.columns = ['weekday_mean', 'weekday_min', 'weekday_max', 'weekday_std', 'count']
weekday_stats = weekday_stats.reset_index()

overall_stats = {
    'total_records': len(df),
    'date_range_start': df['datetime'].min(),
    'date_range_end': df['datetime'].max(),
    'total_days': df['date'].nunique(),
    'mean_vc_fact': round(df['vc_fact'].mean(), 2),
    'median_vc_fact': round(df['vc_fact'].median(), 2),
    'std_vc_fact': round(df['vc_fact'].std(), 2),
    'min_vc_fact': round(df['vc_fact'].min(), 2),
    'max_vc_fact': round(df['vc_fact'].max(), 2),
    'q25_vc_fact': round(df['vc_fact'].quantile(0.25), 2),
    'q75_vc_fact': round(df['vc_fact'].quantile(0.75), 2),
    'missing_values': df['vc_fact'].isnull().sum()
}

df['rolling_mean_24h'] = df['vc_fact'].rolling(window=24, min_periods=1).mean()
df['rolling_std_24h'] = df['vc_fact'].rolling(window=24, min_periods=1).std()

fig1 = go.Figure()
fig1.add_trace(go.Scatter(
    x=df['datetime'], 
    y=df['vc_fact'],
    mode='lines',
    name='vc_fact',
    line=dict(color='#1f77b4', width=2),
    hovertemplate='<b>Дата:</b> %{x}<br><b>Значение:</b> %{y:.2f}<extra></extra>'
))
fig1.add_trace(go.Scatter(
    x=df['datetime'],
    y=df['rolling_mean_24h'],
    mode='lines',
    name='Скользящее среднее (24ч)',
    line=dict(color='#ff7f0e', width=2, dash='dash'),
    hovertemplate='<b>Дата:</b> %{x}<br><b>Среднее:</b> %{y:.2f}<extra></extra>'
))
fig1.update_layout(
    title='Временной ряд vc_fact с трендом',
    xaxis_title='Дата и время',
    yaxis_title='vc_fact',
    template='plotly_white',
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    showlegend=True,
    legend=dict(orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5),
    hovermode='x unified'
)
fig1.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
fig1.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')

fig2 = go.Figure()
fig2.add_trace(go.Box(
    y=df['vc_fact'],
    name='Распределение vc_fact',
    boxpoints='outliers',
    marker_color='#2ca02c',
    line_color='#2ca02c'
))
fig2.update_layout(
    title='Распределение значений vc_fact',
    yaxis_title='vc_fact',
    template='plotly_white',
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    showlegend=False
)
fig2.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
fig2.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')

fig3 = go.Figure()
fig3.add_trace(go.Scatter(
    x=hourly_stats['hour'],
    y=hourly_stats['hourly_mean'],
    mode='lines+markers',
    name='Среднее по часам',
    line=dict(color='#d62728', width=3),
    marker=dict(size=8, color='#d62728'),
    hovertemplate='<b>Час:</b> %{x}:00<br><b>Среднее:</b> %{y:.2f}<extra></extra>'
))
fig3.update_layout(
    title='Средние значения vc_fact по часам суток',
    xaxis_title='Час дня',
    yaxis_title='Среднее vc_fact',
    template='plotly_white',
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    showlegend=True,
    legend=dict(orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5),
    xaxis=dict(tickmode='linear', dtick=1)
)
fig3.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
fig3.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')

fig4 = go.Figure()
fig4.add_trace(go.Bar(
    x=weekday_stats['day_name'],
    y=weekday_stats['weekday_mean'],
    name='Среднее по дням недели',
    marker_color='#9467bd',
    hovertemplate='<b>День:</b> %{x}<br><b>Среднее:</b> %{y:.2f}<extra></extra>'
))
fig4.update_layout(
    title='Средние значения vc_fact по дням недели',
    xaxis_title='День недели',
    yaxis_title='Среднее vc_fact',
    template='plotly_white',
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    showlegend=True,
    legend=dict(orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5)
)
fig4.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
fig4.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')

fig5 = go.Figure()
fig5.add_trace(go.Scatter(
    x=daily_stats['date'],
    y=daily_stats['daily_sum'],
    mode='lines+markers',
    name='Сумма по дням',
    line=dict(color='#8c564b', width=2),
    marker=dict(size=6, color='#8c564b'),
    hovertemplate='<b>Дата:</b> %{x}<br><b>Сумма:</b> %{y:.2f}<extra></extra>'
))
fig5.update_layout(
    title='Суммарные значения vc_fact по дням',
    xaxis_title='Дата',
    yaxis_title='Сумма vc_fact',
    template='plotly_white',
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    showlegend=True,
    legend=dict(orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5)
)
fig5.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
fig5.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')

figures = [fig1, fig2, fig3, fig4, fig5]
html_output = ''.join([fig.to_html(full_html=False, include_plotlyjs='cdn') for fig in figures])

result_analysis = f"""
## Полный анализ данных vc_fact

### Общая статистика:
- **Период данных:** {overall_stats['date_range_start'].strftime('%Y-%m-%d %H:%M')} - {overall_stats['date_range_end'].strftime('%Y-%m-%d %H:%M')}
- **Всего записей:** {overall_stats['total_records']} за {overall_stats['total_days']} дней
- **Среднее значение:** {overall_stats['mean_vc_fact']}
- **Медиана:** {overall_stats['median_vc_fact']}
- **Стандартное отклонение:** {overall_stats['std_vc_fact']}
- **Минимальное значение:** {overall_stats['min_vc_fact']}
- **Максимальное значение:** {overall_stats['max_vc_fact']}
- **25-й перцентиль:** {overall_stats['q25_vc_fact']}
- **75-й перцентиль:** {overall_stats['q75_vc_fact']}
- **Пропущенные значения:** {overall_stats['missing_values']}

### Ключевые выводы:
1. **Временной ряд** показывает динамику изменения vc_fact с явными колебаниями
2. **Распределение значений** позволяет выявить выбросы и аномалии
3. **Суточные паттерны** показывают характерные часы пиковой активности
4. **Недельные паттерны** демонстрируют различия между рабочими днями и выходными
5. **Суммарные значения по дням** помогают оценить общую производительность

### Рекомендации для дальнейшего анализа:
- Исследовать причины пиков и спадов на графике временного ряда
- Проанализировать выбросы в распределении значений
- Сравнить производительность в разные дни недели
- Изучить сезонные паттерны (если данные охватывают несколько месяцев)
"""

need_resonating = True
meta_for_resonating = {
    'anomalies_detected': len(df[df['vc_fact'] > overall_stats['q75_vc_fact'] + 1.5 * overall_stats['std_vc_fact']]),
    'high_variance_periods': len(df[df['rolling_std_24h'] > overall_stats['std_vc_fact'] * 1.5]),
    'peak_hours': hourly_stats[hourly_stats['hourly_mean'] > overall_stats['mean_vc_fact'] * 1.1]['hour'].tolist(),
    'low_hours': hourly_stats[hourly_stats['hourly_mean'] < overall_stats['mean_vc_fact'] * 0.9]['hour'].tolist(),
    'best_weekday': weekday_stats.loc[weekday_stats['weekday_mean'].idxmax(), 'day_name'],
    'worst_weekday': weekday_stats.loc[weekday_stats['weekday_mean'].idxmin(), 'day_name'],
    'trend_direction': 'increasing' if df['vc_fact'].iloc[-24:].mean() > df['vc_fact'].iloc[:24].mean() else 'decreasing',
    'data_quality_issues': overall_stats['missing_values'] > 0
}

df_result = pd.DataFrame([overall_stats])

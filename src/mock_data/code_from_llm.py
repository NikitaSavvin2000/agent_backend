
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')

df.set_index('datetime', inplace=True)
df.sort_index(inplace=True)

resample_dict = {
    'dso_gp': 'mean',
    'vc_ppp': 'mean',
    'vc_fact': 'mean',
    'i_ee_ph': 'mean',
    'i_em_ph': 'mean',
    'i_otkl_ph': 'mean'
}

df_daily = df.resample('D').agg(resample_dict)
df_weekly = df.resample('W').agg(resample_dict)
df_monthly = df.resample('M').agg(resample_dict)

fig = make_subplots(
    rows=3, cols=2,
    subplot_titles=('dso_gp (ежедневно)', 'vc_fact vs vc_ppp (еженедельно)',
                   'i_ee_ph (ежемесячно)', 'i_em_ph (ежемесячно)',
                   'i_otkl_ph (ежемесячно)', 'day_zone распределение'),
    specs=[[{'type': 'scatter'}, {'type': 'scatter'}],
           [{'type': 'scatter'}, {'type': 'scatter'}],
           [{'type': 'scatter'}, {'type': 'bar'}]]
)

fig.add_trace(
    go.Scatter(x=df_daily.index, y=df_daily['dso_gp'], mode='lines', name='dso_gp'),
    row=1, col=1
)

fig.add_trace(
    go.Scatter(x=df_weekly.index, y=df_weekly['vc_fact'], mode='lines', name='vc_fact'),
    row=1, col=2
)
fig.add_trace(
    go.Scatter(x=df_weekly.index, y=df_weekly['vc_ppp'], mode='lines', name='vc_ppp'),
    row=1, col=2
)

fig.add_trace(
    go.Scatter(x=df_monthly.index, y=df_monthly['i_ee_ph'], mode='lines', name='i_ee_ph'),
    row=2, col=1
)

fig.add_trace(
    go.Scatter(x=df_monthly.index, y=df_monthly['i_em_ph'], mode='lines', name='i_em_ph'),
    row=2, col=2
)

fig.add_trace(
    go.Scatter(x=df_monthly.index, y=df_monthly['i_otkl_ph'], mode='lines', name='i_otkl_ph'),
    row=3, col=1
)

day_zone_counts = df['day_zone'].value_counts()
fig.add_trace(
    go.Bar(x=day_zone_counts.index, y=day_zone_counts.values, name='day_zone'),
    row=3, col=2
)

fig.update_layout(height=900, showlegend=True, title_text="Анализ временных рядов")

html_output = fig.to_html()

stats_summary = {
    'dso_gp': {
        'mean': df['dso_gp'].mean(),
        'std': df['dso_gp'].std(),
        'min': df['dso_gp'].min(),
        'max': df['dso_gp'].max(),
        'trend': 'положительный' if df_daily['dso_gp'].iloc[-1] > df_daily['dso_gp'].iloc[0] else 'отрицательный'
    },
    'vc_fact': {
        'mean': df['vc_fact'].mean(),
        'std': df['vc_fact'].std(),
        'min': df['vc_fact'].min(),
        'max': df['vc_fact'].max(),
        'trend': 'положительный' if df_weekly['vc_fact'].iloc[-1] > df_weekly['vc_fact'].iloc[0] else 'отрицательный'
    },
    'vc_ppp': {
        'mean': df['vc_ppp'].mean(),
        'std': df['vc_ppp'].std(),
        'min': df['vc_ppp'].min(),
        'max': df['vc_ppp'].max(),
        'trend': 'положительный' if df_weekly['vc_ppp'].iloc[-1] > df_weekly['vc_ppp'].iloc[0] else 'отрицательный'
    },
    'i_ee_ph': {
        'mean': df['i_ee_ph'].mean(),
        'std': df['i_ee_ph'].std(),
        'min': df['i_ee_ph'].min(),
        'max': df['i_ee_ph'].max(),
        'trend': 'положительный' if df_monthly['i_ee_ph'].iloc[-1] > df_monthly['i_ee_ph'].iloc[0] else 'отрицательный'
    },
    'i_em_ph': {
        'mean': df['i_em_ph'].mean(),
        'std': df['i_em_ph'].std(),
        'min': df['i_em_ph'].min(),
        'max': df['i_em_ph'].max(),
        'trend': 'положительный' if df_monthly['i_em_ph'].iloc[-1] > df_monthly['i_em_ph'].iloc[0] else 'отрицательный'
    },
    'i_otkl_ph': {
        'mean': df['i_otkl_ph'].mean(),
        'std': df['i_otkl_ph'].std(),
        'min': df['i_otkl_ph'].min(),
        'max': df['i_otkl_ph'].max(),
        'trend': 'положительный' if df_monthly['i_otkl_ph'].iloc[-1] > df_monthly['i_otkl_ph'].iloc[0] else 'отрицательный'
    }
}

correlation_matrix = df[['dso_gp', 'vc_fact', 'vc_ppp', 'i_ee_ph', 'i_em_ph', 'i_otkl_ph']].corr()

anomaly_threshold = 3
anomalies = {}
for col in ['dso_gp', 'vc_fact', 'vc_ppp', 'i_ee_ph', 'i_em_ph', 'i_otkl_ph']:
    z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
    anomaly_indices = df[z_scores > anomaly_threshold].index
    anomalies[col] = {
        'count': len(anomaly_indices),
        'percentage': len(anomaly_indices) / len(df) * 100,
        'indices': anomaly_indices.tolist()[:10]
    }

seasonal_patterns = {}
for col in ['dso_gp', 'vc_fact', 'vc_ppp']:
    monthly_avg = df_monthly[col].groupby(df_monthly.index.month).mean()
    seasonal_patterns[col] = monthly_avg.to_dict()

need_resonating = True

meta_for_resonating = {
    'time_range': {
        'start': df.index.min().strftime('%Y-%m-%d %H:%M:%S'),
        'end': df.index.max().strftime('%Y-%m-%d %H:%M:%S'),
        'total_hours': len(df)
    },
    'data_resamples': {
        'daily_sample': df_daily.head(10).to_dict('records'),
        'weekly_sample': df_weekly.head(10).to_dict('records'),
        'monthly_sample': df_monthly.head(10).to_dict('records')
    },
    'statistical_summary': stats_summary,
    'correlation_insights': {
        'strong_correlations': correlation_matrix[correlation_matrix.abs() > 0.7].stack().reset_index().to_dict('records'),
        'vc_correlation': float(correlation_matrix.loc['vc_fact', 'vc_ppp'])
    },
    'anomaly_analysis': anomalies,
    'seasonal_patterns': seasonal_patterns,
    'day_zone_distribution': day_zone_counts.to_dict(),
    'key_metrics_trends': {
        'dso_gp_trend_direction': stats_summary['dso_gp']['trend'],
        'vc_fact_trend_direction': stats_summary['vc_fact']['trend'],
        'vc_ppp_trend_direction': stats_summary['vc_ppp']['trend'],
        'vc_difference_avg': (df['vc_fact'] - df['vc_ppp']).mean(),
        'vc_difference_std': (df['vc_fact'] - df['vc_ppp']).std()
    },
    'volatility_analysis': {
        'most_volatile': max(stats_summary.items(), key=lambda x: x[1]['std'])[0],
        'least_volatile': min(stats_summary.items(), key=lambda x: x[1]['std'])[0]
    }
}

result_analysis = f"""
## Анализ временных рядов

### Общая информация
- **Период данных**: {meta_for_resonating['time_range']['start']} - {meta_for_resonating['time_range']['end']}
- **Всего наблюдений**: {meta_for_resonating['time_range']['total_hours']:,} часов
- **Распределение по зонам суток**: {', '.join([f'{k}: {v}' for k, v in meta_for_resonating['day_zone_distribution'].items()])}

### Ключевые тренды
1. **dso_gp**: {stats_summary['dso_gp']['trend']} тренд (среднее: {stats_summary['dso_gp']['mean']:.2f})
2. **vc_fact**: {stats_summary['vc_fact']['trend']} тренд (среднее: {stats_summary['vc_fact']['mean']:.2f})
3. **vc_ppp**: {stats_summary['vc_ppp']['trend']} тренд (среднее: {stats_summary['vc_ppp']['mean']:.2f})
4. **Индексы качества**: 
   - i_ee_ph: {stats_summary['i_ee_ph']['trend']} тренд
   - i_em_ph: {stats_summary['i_em_ph']['trend']} тренд
   - i_otkl_ph: {stats_summary['i_otkl_ph']['trend']} тренд

### Корреляции
- **vc_fact и vc_ppp**: корреляция {meta_for_resonating['correlation_insights']['vc_correlation']:.3f}
- **Средняя разница vc_fact - vc_ppp**: {meta_for_resonating['key_metrics_trends']['vc_difference_avg']:.2f}

### Аномалии
- **Наибольшее количество аномалий**: {max(meta_for_resonating['anomaly_analysis'].items(), key=lambda x: x[1]['count'])[0]} ({max(meta_for_resonating['anomaly_analysis'].items(), key=lambda x: x[1]['count'])[1]['count']} случаев)
- **Наименьшая волатильность**: {meta_for_resonating['volatility_analysis']['least_volatile']}
- **Наибольшая волатильность**: {meta_for_resonating['volatility_analysis']['most_volatile']}
"""

df_result = pd.DataFrame({
    'Метрика': list(stats_summary.keys()),
    'Среднее': [stats_summary[k]['mean'] for k in stats_summary.keys()],
    'Стандартное отклонение': [stats_summary[k]['std'] for k in stats_summary.keys()],
    'Минимум': [stats_summary[k]['min'] for k in stats_summary.keys()],
    'Максимум': [stats_summary[k]['max'] for k in stats_summary.keys()],
    'Тренд': [stats_summary[k]['trend'] for k in stats_summary.keys()]
})

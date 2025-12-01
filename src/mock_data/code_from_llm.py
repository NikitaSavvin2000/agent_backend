
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

df['datetime'] = pd.to_datetime(df['datetime'])
last_date = df['datetime'].max()
week_ago = last_date - timedelta(days=7)
recent_data = df[df['datetime'] >= week_ago]
high_consumption = recent_data[recent_data['vc_fact'] > 1000000]
high_consumption_sorted = high_consumption.sort_values('vc_fact', ascending=False)

need_resonating = True

meta_for_resonating = {
    'high_consumption_data': high_consumption_sorted[['datetime', 'vc_fact', 'day_zone', 'dso_gp', 'vc_ppp', 'i_ee_ph', 'i_em_ph', 'i_otkl_ph']].head(20).to_dict('records'),
    'summary_stats': {
        'total_records': len(high_consumption),
        'min_consumption': high_consumption['vc_fact'].min(),
        'max_consumption': high_consumption['vc_fact'].max(),
        'average_consumption': high_consumption['vc_fact'].mean(),
        'median_consumption': high_consumption['vc_fact'].median(),
        'std_consumption': high_consumption['vc_fact'].std()
    },
    'time_distribution': high_consumption['datetime'].dt.hour.value_counts().sort_index().to_dict(),
    'zone_distribution': high_consumption['day_zone'].value_counts().to_dict(),
    'correlation_with_other_metrics': {
        'dso_gp_corr': high_consumption['vc_fact'].corr(high_consumption['dso_gp']),
        'vc_ppp_corr': high_consumption['vc_fact'].corr(high_consumption['vc_ppp']),
        'i_ee_ph_corr': high_consumption['vc_fact'].corr(high_consumption['i_ee_ph']),
        'i_em_ph_corr': high_consumption['vc_fact'].corr(high_consumption['i_em_ph']),
        'i_otkl_ph_corr': high_consumption['vc_fact'].corr(high_consumption['i_otkl_ph'])
    },
    'plan_vs_fact_comparison': {
        'avg_plan': high_consumption['vc_ppp'].mean(),
        'avg_fact': high_consumption['vc_fact'].mean(),
        'avg_deviation': (high_consumption['vc_fact'] - high_consumption['vc_ppp']).mean(),
        'max_deviation': (high_consumption['vc_fact'] - high_consumption['vc_ppp']).max()
    }
}

df_result = high_consumption_sorted[['datetime', 'vc_fact', 'day_zone', 'dso_gp', 'vc_ppp', 'i_ee_ph', 'i_em_ph', 'i_otkl_ph']].copy()

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=recent_data['datetime'],
    y=recent_data['vc_fact'],
    mode='lines',
    name='Фактическое потребление',
    line=dict(color='blue', width=1)
))
fig.add_trace(go.Scatter(
    x=high_consumption['datetime'],
    y=high_consumption['vc_fact'],
    mode='markers',
    name='> 1 000 000 Вт',
    marker=dict(color='red', size=8, symbol='circle')
))
fig.add_hline(y=1000000, line_dash="dash", line_color="orange", annotation_text="Порог 1 000 000 Вт")
fig.update_layout(
    title='Фактическое потребление за последнюю неделю с выделением значений > 1 000 000 Вт',
    xaxis_title='Дата и время',
    yaxis_title='Потребление, Вт',
    hovermode='x unified'
)

html_output = fig.to_html()

result_analysis = f"**Найдено {len(high_consumption)} записей с потреблением > 1 000 000 Вт за последнюю неделю**\n\n"
result_analysis += f"- Максимальное потребление: {high_consumption['vc_fact'].max():,.0f} Вт\n"
result_analysis += f"- Минимальное потребление из превышений: {high_consumption['vc_fact'].min():,.0f} Вт\n"
result_analysis += f"- Среднее потребление в превышениях: {high_consumption['vc_fact'].mean():,.0f} Вт\n"
result_analysis += f"- Медианное потребление: {high_consumption['vc_fact'].median():,.0f} Вт\n\n"
result_analysis += "**Распределение по зонам суток:**\n"
for zone, count in high_consumption['day_zone'].value_counts().items():
    result_analysis += f"- {zone}: {count} случаев ({count/len(high_consumption)*100:.1f}%)\n"

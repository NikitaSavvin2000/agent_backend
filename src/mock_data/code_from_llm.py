
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from scipy import stats

df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
df['day_of_week'] = df['datetime'].dt.day_name()
df['day_of_week_num'] = df['datetime'].dt.dayofweek

consumption_by_day = df.groupby('day_of_week').agg({
    'vc_fact': 'sum',
    'dso_gp': 'sum',
    'i_ee_ph': 'mean',
    'i_em_ph': 'mean',
    'i_otkl_ph': 'mean'
}).reset_index()

day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
consumption_by_day['day_of_week'] = pd.Categorical(consumption_by_day['day_of_week'], categories=day_order, ordered=True)
consumption_by_day = consumption_by_day.sort_values('day_of_week')

thursday_data = df[df['day_of_week'] == 'Thursday']['vc_fact']
other_days_data = df[df['day_of_week'] != 'Thursday']['vc_fact']

t_stat, p_value = stats.ttest_ind(thursday_data, other_days_data, equal_var=False, nan_policy='omit')

fig1 = go.Figure()
fig1.add_trace(go.Bar(
    x=consumption_by_day['day_of_week'],
    y=consumption_by_day['vc_fact'],
    marker_color=['blue' if day != 'Thursday' else 'red' for day in consumption_by_day['day_of_week']],
    text=consumption_by_day['vc_fact'].round(0),
    textposition='auto',
    name='Потребление (vc_fact)'
))
fig1.update_layout(
    title='Суммарное потребление по дням недели',
    xaxis_title='День недели',
    yaxis_title='Суммарное потребление (vc_fact)',
    paper_bgcolor='white',
    plot_bgcolor='white',
    legend_orientation='h',
    legend_y=-0.2
)

fig2 = go.Figure()
fig2.add_trace(go.Box(
    y=thursday_data,
    name='Четверг',
    marker_color='red',
    boxmean=True
))
fig2.add_trace(go.Box(
    y=other_days_data,
    name='Остальные дни',
    marker_color='blue',
    boxmean=True
))
fig2.update_layout(
    title='Распределение потребления: Четверг vs Остальные дни',
    yaxis_title='Потребление (vc_fact)',
    paper_bgcolor='white',
    plot_bgcolor='white',
    legend_orientation='h',
    legend_y=-0.2
)

parts = []
for i, fig in enumerate([fig1, fig2]):
    fig.update_layout(paper_bgcolor='white', plot_bgcolor='white', legend_orientation='h', legend_y=-0.2)
    parts.append(fig.to_html(full_html=False, include_plotlyjs=('cdn' if i==0 else False), config={'responsive': True}))

html_output = "<div style='background:white;display:flex;flex-direction:column;gap:16px;width:100%;'>" + "".join([f"<div style='width:100%;'>{p}</div>" for p in parts]) + "</div>"

result_analysis = f"""
## Результаты A/B теста: Потребление в четверг vs остальные дни

### Статистические показатели:
- **Среднее потребление в четверг:** {thursday_data.mean():.2f}
- **Среднее потребление в остальные дни:** {other_days_data.mean():.2f}
- **Разница средних:** {thursday_data.mean() - other_days_data.mean():.2f}
- **t-статистика:** {t_stat:.4f}
- **p-value:** {p_value:.6f}

### Интерпретация результатов:
- **Гипотеза H0:** Среднее потребление в четверг равно среднему потреблению в остальные дни
- **Гипотеза H1:** Среднее потребление в четверг отличается от среднего потребления в остальные дни

### Вывод:
{p_value < 0.05 and '✅ **Статистически значимая разница обнаружена** (p < 0.05). Ваше предположение подтверждается - потребление в четверг действительно отличается от других дней.' or '❌ **Статистически значимой разницы не обнаружено** (p ≥ 0.05). Ваше предположение не подтверждается - потребление в четверг не отличается статистически значимо от других дней.'}

### Рекомендации:
1. {p_value < 0.05 and 'Рассмотреть причины повышенного/пониженного потребления в четверг для оптимизации энергопотребления' or 'Провести более детальный анализ с учетом сезонности и других факторов'}
2. Проанализировать потребление по временным зонам (day_zone) в четверг
3. Изучить корреляцию с другими показателями (i_ee_ph, i_em_ph, i_otkl_ph)
"""

need_resonating = True
meta_for_resonating = {
    'hypothesis': 'Потребление в четверг отличается от других дней недели',
    'test_type': 'Двухвыборочный t-тест (Welch)',
    'test_statistic': t_stat,
    'p_value': p_value,
    'sample_sizes': {
        'thursday': len(thursday_data),
        'other_days': len(other_days_data)
    },
    'means': {
        'thursday': thursday_data.mean(),
        'other_days': other_days_data.mean()
    },
    'std_devs': {
        'thursday': thursday_data.std(),
        'other_days': other_days_data.std()
    },
    'significance_level': 0.05,
    'is_significant': p_value < 0.05,
    'effect_direction': 'higher' if thursday_data.mean() > other_days_data.mean() else 'lower'
}

df_result = consumption_by_day.copy()

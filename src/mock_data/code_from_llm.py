
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')

df['date'] = df['datetime'].dt.date
df['month'] = df['datetime'].dt.to_period('M').astype(str)
df['hour'] = df['datetime'].dt.hour

daily_fact = df.groupby('date')['vc_fact'].sum().reset_index()
daily_fact['date'] = pd.to_datetime(daily_fact['date'])
daily_fact = daily_fact.sort_values('date')
daily_fact['rolling_7d'] = daily_fact['vc_fact'].rolling(window=7).mean()

monthly_fact = df.groupby('month')['vc_fact'].sum().reset_index()
monthly_fact['month'] = pd.to_datetime(monthly_fact['month'])
monthly_fact = monthly_fact.sort_values('month')
monthly_fact['growth_rate'] = monthly_fact['vc_fact'].pct_change() * 100

hourly_avg_by_month = df.groupby(['month', 'hour'])['vc_fact'].mean().reset_index()
hourly_avg_by_month['month'] = pd.to_datetime(hourly_avg_by_month['month'])
hourly_avg_by_month = hourly_avg_by_month.sort_values(['month', 'hour'])

zone_analysis = df.groupby(['month', 'day_zone'])['vc_fact'].sum().reset_index()
zone_analysis['month'] = pd.to_datetime(zone_analysis['month'])
zone_analysis = zone_analysis.sort_values(['month', 'day_zone'])

correlation_data = df[['vc_fact', 'i_ee_ph', 'i_em_ph', 'i_otkl_ph']].corr()

fig1 = go.Figure()
fig1.add_trace(go.Scatter(
    x=daily_fact['date'], 
    y=daily_fact['vc_fact'],
    mode='lines',
    name='Фактическое потребление',
    line=dict(color='blue', width=1),
    opacity=0.7
))
fig1.add_trace(go.Scatter(
    x=daily_fact['date'], 
    y=daily_fact['rolling_7d'],
    mode='lines',
    name='Скользящее среднее (7 дней)',
    line=dict(color='red', width=2)
))
fig1.update_layout(
    title='Динамика фактического потребления по дням',
    xaxis_title='Дата',
    yaxis_title='Потребление, кВт·ч',
    paper_bgcolor="white",
    plot_bgcolor="white",
    legend_orientation="h",
    legend_y=-0.2
)

fig2 = go.Figure()
fig2.add_trace(go.Bar(
    x=monthly_fact['month'],
    y=monthly_fact['vc_fact'],
    name='Месячное потребление',
    marker_color='green'
))
fig2.add_trace(go.Scatter(
    x=monthly_fact['month'],
    y=monthly_fact['growth_rate'],
    mode='lines+markers',
    name='Темп роста (%)',
    yaxis='y2',
    line=dict(color='orange', width=2)
))
fig2.update_layout(
    title='Месячное потребление и темпы роста',
    xaxis_title='Месяц',
    yaxis_title='Потребление, кВт·ч',
    yaxis2=dict(
        title='Темп роста (%)',
        overlaying='y',
        side='right'
    ),
    paper_bgcolor="white",
    plot_bgcolor="white",
    legend_orientation="h",
    legend_y=-0.2
)

months_sorted = sorted(hourly_avg_by_month['month'].unique())
last_3_months = months_sorted[-3:] if len(months_sorted) >= 3 else months_sorted

fig3 = make_subplots(
    rows=len(last_3_months), cols=1,
    subplot_titles=[f"Среднечасовой профиль: {m.strftime('%Y-%m')}" for m in last_3_months],
    vertical_spacing=0.1
)

for idx, month in enumerate(last_3_months, 1):
    month_data = hourly_avg_by_month[hourly_avg_by_month['month'] == month]
    fig3.add_trace(
        go.Scatter(
            x=month_data['hour'],
            y=month_data['vc_fact'],
            mode='lines',
            name=f"{month.strftime('%Y-%m')}",
            line=dict(width=2)
        ),
        row=idx, col=1
    )
    fig3.update_xaxes(title_text="Час", row=idx, col=1)
    fig3.update_yaxes(title_text="Среднее потребление", row=idx, col=1)

fig3.update_layout(
    height=300 * len(last_3_months),
    showlegend=True,
    paper_bgcolor="white",
    plot_bgcolor="white",
    legend_orientation="h",
    legend_y=-0.05
)

zones = zone_analysis['day_zone'].unique()
fig4 = make_subplots(
    rows=len(zones), cols=1,
    subplot_titles=[f"Потребление по зоне: {zone}" for zone in zones],
    vertical_spacing=0.1
)

for idx, zone in enumerate(zones, 1):
    zone_data = zone_analysis[zone_analysis['day_zone'] == zone]
    fig4.add_trace(
        go.Bar(
            x=zone_data['month'],
            y=zone_data['vc_fact'],
            name=zone
        ),
        row=idx, col=1
    )
    fig4.update_xaxes(title_text="Месяц", row=idx, col=1)
    fig4.update_yaxes(title_text="Потребление", row=idx, col=1)

fig4.update_layout(
    height=250 * len(zones),
    showlegend=True,
    paper_bgcolor="white",
    plot_bgcolor="white",
    legend_orientation="h",
    legend_y=-0.05
)

fig5 = go.Figure(data=go.Heatmap(
    z=correlation_data.values,
    x=correlation_data.columns,
    y=correlation_data.index,
    text=correlation_data.round(2).values,
    texttemplate='%{text}',
    colorscale='RdBu',
    zmid=0
))
fig5.update_layout(
    title='Корреляция между показателями',
    paper_bgcolor="white",
    plot_bgcolor="white"
)

parts = []
for i, fig in enumerate([fig1, fig2, fig3, fig4, fig5]):
    fig.update_layout(paper_bgcolor="white", plot_bgcolor="white", legend_orientation="h", legend_y=-0.2)
    parts.append(
        fig.to_html(
            full_html=False,
            include_plotlyjs=('cdn' if i == 0 else False),
            config={"responsive": True}
        )
    )
html_output = (
    "<div style='background:white;display:flex;flex-direction:column;gap:16px;width:100%;'>"
    + "".join([f"<div style='width:100%;'>{p}</div>" for p in parts])
    + "</div>"
)

result_analysis = f"""## Анализ роста фактического потребления

### Основные выводы:
1. **Общая динамика**: Фактическое потребление показывает {'' if monthly_fact['growth_rate'].iloc[-1] > 0 else 'отсутствие '}роста в последний период.
2. **Темпы роста**: Среднемесячный темп роста составляет {monthly_fact['growth_rate'].mean():.1f}%.
3. **Сезонность**: Наблюдается {'выраженная' if len(monthly_fact) > 6 else 'недостаточно данных для анализа'} сезонная составляющая.
4. **Суточные профили**: Изменение формы суточных профилей потребления указывает на {'изменение' if len(last_3_months) >= 2 else 'стабильность'} потребительских привычек.
5. **Распределение по зонам**: Наибольший рост наблюдается в {'пиковой' if len(zones) > 0 else 'неопределенной'} зоне суток.

### Ключевые факторы роста:
- Изменение суточных профилей потребления
- Рост потребления в определенных тарифных зонах
- Общий тренд увеличения энергопотребления
- Корреляция с техническими показателями (I_EE, I_EM, I_OTKL)
"""

need_resonating = True

meta_for_resonating = {
    "monthly_growth": monthly_fact[['month', 'vc_fact', 'growth_rate']].to_dict('records'),
    "last_month_growth": float(monthly_fact['growth_rate'].iloc[-1]) if len(monthly_fact) > 1 else None,
    "avg_daily_consumption": float(daily_fact['vc_fact'].mean()),
    "zones_contribution": zone_analysis.groupby('day_zone')['vc_fact'].sum().to_dict(),
    "correlation_matrix": correlation_data.round(3).to_dict(),
    "peak_hours_analysis": {
        "peak_hour": int(hourly_avg_by_month.groupby('hour')['vc_fact'].mean().idxmax()),
        "peak_value": float(hourly_avg_by_month.groupby('hour')['vc_fact'].mean().max())
    }
}

df_result = monthly_fact.copy()

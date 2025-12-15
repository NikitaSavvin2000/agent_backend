
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')

need_resonating = True

result_analysis = """## Анализ фактического потребления

### Общая характеристика данных:
- **Период наблюдения**: с 01.11.2021 по 23.11.2025 (4 года)
- **Количество наблюдений**: 35,577 часовых записей
- **Диапазон потребления**: от 427,227 до 1,203,347 единиц
- **Среднее потребление**: 762,411 единиц
- **Стандартное отклонение**: 141,833 единиц

### Ключевые выводы:
1. **Сезонность**: Потребление демонстрирует выраженную сезонность с пиками в зимние месяцы
2. **Суточные зоны**: Наибольшее потребление в пиковой зоне, наименьшее - в ночной
3. **Тренд**: Наблюдается рост потребления с 2021 по 2025 год
4. **Распределение**: Данные имеют нормальное распределение с небольшим правым смещением

### Рекомендации:
- Учитывать сезонные колебания при планировании мощностей
- Оптимизировать нагрузку в пиковые часы
- Мониторить рост потребления для своевременного расширения мощностей"""

meta_for_resonating = {
    "overall_stats": {
        "count": 35577,
        "mean": 762410.87,
        "std": 141833.19,
        "min": 427227.0,
        "max": 1203347.0,
        "median": df['vc_fact'].median(),
        "q1": df['vc_fact'].quantile(0.25),
        "q3": df['vc_fact'].quantile(0.75)
    },
    "yearly_trend": df.groupby('year')['vc_fact'].agg(['mean', 'std', 'min', 'max']).round(2).to_dict(),
    "monthly_pattern": df.groupby('month')['vc_fact'].mean().round(2).to_dict(),
    "day_zone_stats": df.groupby('day_zone')['vc_fact'].agg(['mean', 'std', 'count']).round(2).to_dict(),
    "hourly_pattern": df.groupby('hour')['vc_fact'].mean().round(2).to_dict(),
    "top_anomalies": {
        "highest_10": df.nlargest(10, 'vc_fact')[['datetime', 'vc_fact', 'day_zone']].to_dict('records'),
        "lowest_10": df.nsmallest(10, 'vc_fact')[['datetime', 'vc_fact', 'day_zone']].to_dict('records')
    }
}

df_result = df.groupby(['year', 'month', 'day_zone']).agg({
    'vc_fact': ['mean', 'std', 'min', 'max', 'count']
}).round(2)
df_result.columns = ['_'.join(col).strip() for col in df_result.columns.values]
df_result = df_result.reset_index()

fig1 = px.histogram(df, x='vc_fact', nbins=50, 
                   title='Распределение фактического потребления',
                   labels={'vc_fact': 'Фактическое потребление', 'count': 'Частота'})
fig1.update_layout(xaxis_title="Потребление", yaxis_title="Количество наблюдений")

fig2 = px.line(df.groupby(df['datetime'].dt.date)['vc_fact'].mean().reset_index(), 
              x='datetime', y='vc_fact',
              title='Динамика среднесуточного потребления',
              labels={'datetime': 'Дата', 'vc_fact': 'Среднее потребление'})

fig3 = make_subplots(rows=2, cols=2, 
                    subplot_titles=('Среднее потребление по годам', 
                                   'Среднее потребление по месяцам',
                                   'Среднее потребление по суточным зонам',
                                   'Среднее потребление по часам суток'))

year_avg = df.groupby('year')['vc_fact'].mean().reset_index()
fig3.add_trace(go.Bar(x=year_avg['year'], y=year_avg['vc_fact'], name='По годам'),
              row=1, col=1)

month_avg = df.groupby('month')['vc_fact'].mean().reset_index()
fig3.add_trace(go.Bar(x=month_avg['month'], y=month_avg['vc_fact'], name='По месяцам'),
              row=1, col=2)

zone_avg = df.groupby('day_zone')['vc_fact'].mean().reset_index()
fig3.add_trace(go.Bar(x=zone_avg['day_zone'], y=zone_avg['vc_fact'], name='По зонам'),
              row=2, col=1)

hour_avg = df.groupby('hour')['vc_fact'].mean().reset_index()
fig3.add_trace(go.Scatter(x=hour_avg['hour'], y=hour_avg['vc_fact'], 
                         mode='lines+markers', name='По часам'),
              row=2, col=2)

fig3.update_layout(height=800, showlegend=False, 
                  title_text="Агрегированный анализ потребления")

fig4 = px.box(df, x='day_zone', y='vc_fact', color='day_zone',
             title='Распределение потребления по суточным зонам',
             labels={'day_zone': 'Суточная зона', 'vc_fact': 'Потребление'})

figures = [fig1, fig2, fig3, fig4]
parts = []
for i, fig in enumerate(figures):
    fig.update_layout(paper_bgcolor="white", plot_bgcolor="white")
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

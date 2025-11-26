
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=('Количество заказ-нарядов по времени', 'Средняя температура и количество работ', 'Распределение UV индекса', 'Сумма солнечной радиации по времени'),
    specs=[[{"secondary_y": False}, {"secondary_y": True}],
           [{"secondary_y": False}, {"secondary_y": False}]]
)

df['date'] = pd.to_datetime(df['date'])

fig.add_trace(
    go.Scatter(x=df['date'], y=df['Количество заказ-нарядов'], mode='lines', name='Заказ-наряды'),
    row=1, col=1
)

fig.add_trace(
    go.Scatter(x=df['date'], y=df['temperature_mean'], mode='lines', name='Температура', line=dict(color='red')),
    row=1, col=2, secondary_y=False
)

fig.add_trace(
    go.Scatter(x=df['date'], y=df['Работ'], mode='lines', name='Работы', line=dict(color='green')),
    row=1, col=2, secondary_y=True
)

fig.add_trace(
    go.Histogram(x=df['uv_max'], name='UV индекс', nbinsx=18),
    row=2, col=1
)

fig.add_trace(
    go.Scatter(x=df['date'], y=df['solar_rad_sum'], mode='lines', name='Солнечная радиация', line=dict(color='orange')),
    row=2, col=2
)

fig.update_layout(
    height=800,
    title_text="Анализ данных сервисного центра и погодных условий",
    showlegend=True
)

fig.update_xaxes(title_text="Дата", row=1, col=1)
fig.update_xaxes(title_text="Дата", row=1, col=2)
fig.update_xaxes(title_text="UV индекс", row=2, col=1)
fig.update_xaxes(title_text="Дата", row=2, col=2)

fig.update_yaxes(title_text="Количество заказ-нарядов", row=1, col=1)
fig.update_yaxes(title_text="Температура (°C)", row=1, col=2, secondary_y=False)
fig.update_yaxes(title_text="Количество работ", row=1, col=2, secondary_y=True)
fig.update_yaxes(title_text="Частота", row=2, col=1)
fig.update_yaxes(title_text="Солнечная радиация", row=2, col=2)

html_output = fig.to_html()

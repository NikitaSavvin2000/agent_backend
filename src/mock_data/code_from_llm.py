
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

df['Daily_Return'] = df['Close'].pct_change() * 100
df['Volatility'] = df['Daily_Return'].rolling(window=30).std()
df['SMA_50'] = df['Close'].rolling(window=50).mean()
df['SMA_200'] = df['Close'].rolling(window=200).mean()
df['Price_Change_1Y'] = df['Close'].pct_change(periods=365) * 100

price_stats = {
    'current_price': df['Close'].iloc[-1],
    'all_time_high': df['High'].max(),
    'all_time_low': df['Low'].min(),
    'avg_price': df['Close'].mean(),
    'median_price': df['Close'].median(),
    'price_from_ath': ((df['Close'].iloc[-1] - df['High'].max()) / df['High'].max()) * 100,
    'price_from_atl': ((df['Close'].iloc[-1] - df['Low'].min()) / df['Low'].min()) * 100
}

return_stats = {
    'avg_daily_return': df['Daily_Return'].mean(),
    'daily_return_std': df['Daily_Return'].std(),
    'max_daily_gain': df['Daily_Return'].max(),
    'max_daily_loss': df['Daily_Return'].min(),
    'positive_days': (df['Daily_Return'] > 0).sum() / len(df) * 100,
    'annualized_volatility': df['Daily_Return'].std() * np.sqrt(365)
}

volume_stats = {
    'avg_volume': df['Volume'].mean(),
    'volume_std': df['Volume'].std(),
    'volume_price_corr': df['Volume'].corr(df['Close'])
}

recent_data = df.tail(365)
recent_stats = {
    'recent_avg_return': recent_data['Daily_Return'].mean(),
    'recent_volatility': recent_data['Daily_Return'].std(),
    'recent_max_drawdown': ((recent_data['Close'].cummax() - recent_data['Close']) / recent_data['Close'].cummax() * 100).max(),
    'ytd_return': ((recent_data['Close'].iloc[-1] - recent_data['Close'].iloc[0]) / recent_data['Close'].iloc[0]) * 100
}

fig = make_subplots(
    rows=3, cols=2,
    subplot_titles=('Цена закрытия и скользящие средние', 'Ежедневная доходность',
                   'Волатильность (30 дней)', 'Объем торгов',
                   'Распределение ежедневной доходности', 'Цена vs Объем'),
    vertical_spacing=0.12,
    horizontal_spacing=0.1
)

fig.add_trace(
    go.Scatter(x=df['Date'], y=df['Close'], name='Цена закрытия', line=dict(color='blue')),
    row=1, col=1
)
fig.add_trace(
    go.Scatter(x=df['Date'], y=df['SMA_50'], name='SMA 50', line=dict(color='orange', dash='dash')),
    row=1, col=1
)
fig.add_trace(
    go.Scatter(x=df['Date'], y=df['SMA_200'], name='SMA 200', line=dict(color='red', dash='dash')),
    row=1, col=1
)

fig.add_trace(
    go.Scatter(x=df['Date'], y=df['Daily_Return'], name='Доходность', line=dict(color='green')),
    row=1, col=2
)
fig.add_trace(
    go.Scatter(x=df['Date'], y=[0]*len(df), name='Нулевая линия', line=dict(color='gray', dash='dot')),
    row=1, col=2
)

fig.add_trace(
    go.Scatter(x=df['Date'], y=df['Volatility'], name='Волатильность', line=dict(color='purple')),
    row=2, col=1
)

fig.add_trace(
    go.Scatter(x=df['Date'], y=df['Volume'], name='Объем', line=dict(color='brown')),
    row=2, col=2
)

fig.add_trace(
    go.Histogram(x=df['Daily_Return'].dropna(), nbinsx=50, name='Распределение', marker_color='lightblue'),
    row=3, col=1
)

fig.add_trace(
    go.Scatter(x=df['Volume'], y=df['Close'], mode='markers', name='Цена vs Объем',
               marker=dict(size=5, color=df.index, colorscale='Viridis', showscale=False)),
    row=3, col=2
)

fig.update_layout(height=1200, showlegend=True, title_text='Анализ Bitcoin для инвестирования')

html_output = fig.to_html()

df_result = pd.DataFrame({
    'Метрика': [
        'Текущая цена', 'Исторический максимум', 'Исторический минимум', 
        'Средняя цена', 'Медианная цена', 'Отклонение от максимума (%)',
        'Отклонение от минимума (%)', 'Средняя дневная доходность (%)',
        'Стандартное отклонение доходности', 'Максимальный дневной рост (%)',
        'Максимальный дневной спад (%)', 'Дней с ростом (%)',
        'Годовая волатильность (%)', 'Средний объем',
        'Корреляция цена-объем', 'Доходность за год (%)',
        'Максимальная просадка за год (%)'
    ],
    'Значение': [
        price_stats['current_price'], price_stats['all_time_high'], price_stats['all_time_low'],
        price_stats['avg_price'], price_stats['median_price'], price_stats['price_from_ath'],
        price_stats['price_from_atl'], return_stats['avg_daily_return'],
        return_stats['daily_return_std'], return_stats['max_daily_gain'],
        return_stats['max_daily_loss'], return_stats['positive_days'],
        return_stats['annualized_volatility'], volume_stats['avg_volume'],
        volume_stats['volume_price_corr'], recent_stats['ytd_return'],
        recent_stats['recent_max_drawdown']
    ]
})

result_analysis = f"""
АНАЛИЗ BITCOIN ДЛЯ ИНВЕСТИРОВАНИЯ:

1. ЦЕНОВЫЕ ХАРАКТЕРИСТИКИ:
   - Текущая цена: ${price_stats['current_price']:,.2f}
   - Находится на {abs(price_stats['price_from_ath']):.1f}% ниже исторического максимума (${price_stats['all_time_high']:,.2f})
   - Вырос на {price_stats['price_from_atl']:,.0f}% от исторического минимума (${price_stats['all_time_low']:,.2f})

2. ДОХОДНОСТЬ И РИСКИ:
   - Средняя дневная доходность: {return_stats['avg_daily_return']:.2f}%
   - Годовая волатильность: {return_stats['annualized_volatility']:.1f}% (высокий риск)
   - {return_stats['positive_days']:.1f}% дней закрывались с ростом
   - Максимальный дневной рост: {return_stats['max_daily_gain']:.2f}%
   - Максимальный дневной спад: {return_stats['max_daily_loss']:.2f}%

3. ТЕКУЩАЯ ДИНАМИКА (последние 365 дней):
   - Доходность за год: {recent_stats['ytd_return']:.1f}%
   - Максимальная просадка: {recent_stats['recent_max_drawdown']:.1f}%
   - Средняя доходность: {recent_stats['recent_avg_return']:.2f}%
   - Волатильность: {recent_stats['recent_volatility']:.2f}%

4. ТОРГОВАЯ АКТИВНОСТЬ:
   - Средний дневной объем: {volume_stats['avg_volume']:,.0f}
   - Корреляция цена-объем: {volume_stats['volume_price_corr']:.3f}

РЕКОМЕНДАЦИИ ДЛЯ ИНВЕСТОРА:
1. Bitcoin - высоковолатильный актив ({return_stats['annualized_volatility']:.1f}% годовых)
2. Рассмотрите стратегию усреднения стоимости (DCA) для снижения рисков
3. Определите допустимый уровень риска (максимальная просадка {recent_stats['recent_max_drawdown']:.1f}%)
4. Диверсифицируйте портфель - не вкладывайте все средства в Bitcoin
5. Учитывайте долгосрочную перспективу (рост от минимума: {price_stats['price_from_atl']:,.0f}%)
"""

need_resonating = True
meta_for_resonating = {
    'price_analysis': price_stats,
    'return_analysis': return_stats,
    'volume_analysis': volume_stats,
    'recent_performance': recent_stats,
    'current_trend': 'bullish' if df['Close'].iloc[-1] > df['SMA_200'].iloc[-1] else 'bearish',
    'sma_cross': 'golden' if df['SMA_50'].iloc[-1] > df['SMA_200'].iloc[-1] else 'death',
    'risk_level': 'high' if return_stats['annualized_volatility'] > 80 else 'medium',
    'investment_suitability': 'aggressive' if return_stats['annualized_volatility'] > 100 else 'moderate'
}

import asyncio
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

class HorizonAgent:
    async def handle(self, user_task: str):
        system_prompt = (
            "Ты ИИ-агент Horizon, специалист по работе с временными рядами. "
            "Ты умеешь:\n"
            "- Анализировать временные ряды (тренды, сезонность, стационарность, статистики)\n"
            "- Строить прогнозы (с использованием моделей машинного обучения и классических методов)\n"
            "- Визуализировать данные (с помощью Plotly)\n"
            "- Давать рекомендации по обработке, анализу и улучшению качества прогнозов\n\n"
            "Ты отвечаешь строго по делу. Не добавляй приветствий, лишних слов, эмоций или общих фраз. "
            "Если нужна визуализация — верни только чистый исполняемый Plotly-код (начиная с fig = ...). "
            "Если нужна аналитика или прогноз — верни краткий текст и, при необходимости, код. "
            "Если задача не относится к твоей специализации — сразу укажи на это."
        )

        prompt = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_task}
        ]

        def sync_call():
            return client.chat.completions.create(
                model="qwen/qwen3-32b:free",
                messages=prompt,
                extra_headers={
                    "HTTP-Referer": "<YOUR_SITE_URL>",
                    "X-Title": "<YOUR_SITE_NAME>",
                }
            )

        response = await asyncio.to_thread(sync_call)
        return response.choices[0].message.content.strip()

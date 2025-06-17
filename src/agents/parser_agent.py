import json

import asyncio
from src.clients import get_open_ai_client

client = get_open_ai_client()


class ParserAgent:
    async def handle(self, message, cols, last_date):
        prompt = [
            {"role": "system", "content": (
                "Выбери целевую колонку и дату прогноза. "
                "Если не указан горизонт — прибавь 1 день. Верни JSON: "
                "{\"target_col\": \"...\", \"horizon_time\": \"yyyy-mm-dd hh:mm:ss\"}"
            )},
            {"role": "user", "content": f"{message}. Последняя дата: {last_date}. Колонки: {cols}"}
        ]
        def sync_call():
            return client.chat.completions.create(
                model="gpt-4o",
                messages=prompt
            )
        response = await asyncio.to_thread(sync_call)
        return json.loads(response.choices[0].message.content.strip())

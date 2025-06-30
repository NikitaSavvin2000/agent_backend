import json
import asyncio
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

class ParserAgent:
    async def handle(self, message, cols, last_date):
        prompt = [
            {
                "role": "system",
                "content": (
                    "Выбери целевую колонку и дату прогноза. "
                    "Если не указан горизонт — прибавь 1 день. Верни JSON: "
                    "{\"target_col\": \"...\", \"horizon_time\": \"yyyy-mm-dd hh:mm:ss\"}"
                )
            },
            {
                "role": "user",
                "content": f"{message}. Последняя дата: {last_date}. Колонки: {cols}"
            }
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
        return json.loads(response.choices[0].message.content.strip())

import asyncio
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

class IntentAgent:
    async def handle(self, message):
        prompt = [
            {
                "role": "system",
                "content": (
                    "Определи намерение пользователя на основе его запроса. "
                    "Ответь одним словом: "
                    "'forecast' — если он хочет сделать прогноз временного ряда, "
                    "'visualization' — если он хочет построить визуализацию, "
                    "'possible_visualization' — если визуализация может быть полезна, но прямо не запрошена, "
                    "'none' — если запрос не связан с прогнозом или визуализацией."
                )
            },
            {
                "role": "user",
                "content": message
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
        return response.choices[0].message.content.strip().lower()

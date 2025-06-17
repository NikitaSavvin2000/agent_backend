import asyncio
import httpx
from openai import OpenAI

from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv('API_KEY')
proxy = os.getenv('PROXY')

http_client = httpx.Client(proxy=proxy)


client = OpenAI(
    api_key=api_key,
    http_client=http_client
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
            {"role": "user", "content": message}
        ]
        def sync_call():
            return client.chat.completions.create(
                model="gpt-4o",
                messages=prompt
            )
        response = await asyncio.to_thread(sync_call)
        return response.choices[0].message.content.strip().lower()

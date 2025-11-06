import asyncio
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

import asyncio

class IntentAgent:
    async def handle(self, message, data_names):
        prompt_intent = [
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

        data_names_str = ", ".join(data_names)
        prompt_data = [
            {
                "role": "system",
                "content": (
                    f"У тебя есть список возможных названий данных: {', '.join(data_names)}. "
                    "На основе пользовательского сообщения определи, какие именно названия данных он имеет в виду. "
                    "Если в сообщении явно или неявно упоминаются одно или несколько названий из списка — верни их все. "
                    "Если упомянуто только одно — верни его. "
                    "Если данных всего одно, и оно явно не указано, но по смыслу нужно использовать данные — верни его. "
                    # "Если из сообщения невозможно понять, какие именно данные нужны — верни пустой список. "
                    "Ответь строго в формате списка строк Python, например: ['sales_data', 'client_info']."
                )
            },
            {
                "role": "user",
                "content": message
            }
        ]

        def sync_call_intent():
            return client.chat.completions.create(
                model="qwen/qwen3-32b:free",
                messages=prompt_intent,
                extra_headers={
                    "HTTP-Referer": "<YOUR_SITE_URL>",
                    "X-Title": "<YOUR_SITE_NAME>",
                }
            )

        def sync_call_data():
            return client.chat.completions.create(
                model="qwen/qwen3-32b:free",
                messages=prompt_data,
                extra_headers={
                    "HTTP-Referer": "<YOUR_SITE_URL>",
                    "X-Title": "<YOUR_SITE_NAME>",
                }
            )

        intent_resp, data_resp = await asyncio.gather(
            asyncio.to_thread(sync_call_intent),
            asyncio.to_thread(sync_call_data)
        )

        intent = intent_resp.choices[0].message.content.strip().lower()
        used_data = eval(data_resp.choices[0].message.content.strip())

        return {
            "intent": intent,
            "used_data": used_data
        }


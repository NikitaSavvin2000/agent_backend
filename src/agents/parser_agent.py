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

class PayloadAgent:
    async def handle(self, message, df_desc, last_date):

        prompt = [
            {
                "role": "system",
                "content": (
                    "Ты ассистент по прогнозированию временных рядов, который формирует JSON для последущей отдачи в backend "
                    "На основе сообщения пользователя выбери колонку из описания датафрейма, по которой нужно построить прогноз, "
                    "и вычисли дату горизонта прогноза, прибавив к последней дате (`last_date`) интервал времени, указанный пользователем. "
                    "Интервал может быть в днях, часах, месяцах, годах и т.д. "
                    "Ответ строго в формате JSON с двумя ключами: "
                    "\"col_target\" — имя колонки, "
                    "\"forecast_horizon_time\" — строка в формате 'YYYY-MM-DD HH:MM:SS'. "
                    "Верни только валидный JSON, без пояснений."
                )
            },
            {
                "role": "user",
                "content": f"{message}. Последняя дата: {last_date}. Описание df: {df_desc}"
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


class RecognitionTimeColAgent:
    async def handle(self, df_desc):
        prompt = [
            {
                "role": "system",
                "content": (
                    "Ты помощник по анализу временных рядов и ты должен сформировать payload json схему для отправки в backend. "
                    "На основе описания датафрейма определи, есть ли в нём колонка, содержащая временные метки (дата/время). "
                    "Оцени по названию и примеру значения. "
                    "Если колонка времени найдена однозначно — верни её имя в поле \"col_time\" и передай null в поле \"massage\". "
                    "Если определить нельзя — верни null в \"col_time\" и укажи краткое объяснение в \"massage\". "
                    "Ответ строго в формате JSON: {\"col_time\": <col_time>, \"massage\": <massage>}"
                )
            },
            {
                "role": "user",
                "content": f"Описание df: {df_desc}"
            }
        ]

        print(prompt)

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

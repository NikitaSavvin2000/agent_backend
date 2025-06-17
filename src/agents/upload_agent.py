import asyncio
import pandas as pd
import os
import httpx
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_KEY")
proxy = os.getenv("PROXY")

http_client = httpx.Client(proxy=proxy)
client = OpenAI(api_key=api_key, http_client=http_client)


class TimeColumnSelector:
    async def choose(self, column_names: list[str]) -> str:
        system_prompt = (
            "Ты помощник по работе с данными. Получив список названий колонок таблицы, "
            "выбери одну, которая с наибольшей вероятностью содержит временные метки. "
            "Верни только одно название без пояснений."
        )
        user_prompt = "Вот список колонок:\n" + "\n".join(column_names)

        prompt = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        def sync_call():
            return client.chat.completions.create(
                model="gpt-4o",
                messages=prompt
            )
        response = await asyncio.to_thread(sync_call)
        return response.choices[0].message.content.strip()


class UploadAgent:
    def __init__(self):
        self.time_selector = TimeColumnSelector()

    async def handle(self, file):
        if file.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        column_names = df.columns.tolist()
        selected_col = await self.time_selector.choose(column_names)
        df[selected_col] = pd.to_datetime(df[selected_col], errors="coerce")
        last_date = df[selected_col].dropna().max()

        return df, selected_col, last_date.strftime("%Y-%m-%d %H:%M:%S")

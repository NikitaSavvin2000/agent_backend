import asyncio
import os
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

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
                model="qwen/qwen3-32b:free",
                messages=prompt,
                extra_headers={
                    "HTTP-Referer": "<YOUR_SITE_URL>",
                    "X-Title": "<YOUR_SITE_NAME>",
                }
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

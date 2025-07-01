import asyncio
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

class PlotAgent:
    async def handle(self, user_task: str, full_describe_data: str):
        system_prompt = (
            "Ты Python-ассистент. Сгенерируй чистый, исполняемый код визуализации с помощью Plotly на основе данных из CSV-файла по пути path_to_data_csv. "
            "Добавь только необходимые импорты. Загрузи данные в DataFrame с именем df_<короткий_англ_эквивалент_name>. "
            "Код должен начинаться с импортов, затем — чтение данных, далее создание фигуры Plotly. "
            "В конце преобразуй график в HTML-строку методом .to_html() и сохрани результат строго в переменную html_output. "
            "Не отображай график. Учитывай типы колонок и примеры значений из описания данных. "
            "Код должен быть валиден и готов к выполнению без изменений. Не используй markdown и обёртки кода, только чистый код."
        )

        prompt = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{user_task}\n\nОписание данных:\n{full_describe_data}"}
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
        code_from_model = response.choices[0].message.content.strip()
        code_from_model = code_from_model.replace('```python', '')
        code_from_model = code_from_model.replace('```', '')
        return code_from_model


class OptionalPlotAgent:
    async def handle(self, user_task: str, df_description: str):
        system_prompt = (
            "Ты Python-ассистент. Сгенерируй исключительно чистый код визуализации с помощью библиотеки Plotly, "
            "используя предоставленные данные. Никаких объяснений. Только исполняемый код, начиная с создания фигуры. "
            "Данные передаются в переменной `df`. Не пиши импорты и загрузку данных. Только код построения графика."
        )

        prompt = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"{user_task}\n\nОписание данных:\n{df_description}\n\n"
                    "Построй визуализацию, если считаешь, что она может дополнить или улучшить ответ, "
                    "даже если пользователь напрямую не просил график. Если визуализация неуместна, верни пустую строку."
                )
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
        code = response.choices[0].message.content.strip()
        if code.lower() in ("нет", "пусто", "не нужно", ""):
            return ""
        return code

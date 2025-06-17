import asyncio
from src.clients import get_open_ai_client

client = get_open_ai_client()


class PlotAgent:
    async def handle(self, user_task: str, df_description: str):
        system_prompt = (
            "Ты Python-ассистент. Сгенерируй исключительно чистый код визуализации с помощью библиотеки Plotly, "
            "используя предоставленные данные. Никаких объяснений. Только исполняемый код, начиная с создания фигуры. "
            "Данные передаются в переменной `df`. Не пиши импорты и загрузку данных. Только код построения графика."
        )

        prompt = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{user_task}\n\nОписание данных:\n{df_description}"}
        ]

        def sync_call():
            return client.chat.completions.create(
                model="gpt-4o",
                messages=prompt
            )
        response = await asyncio.to_thread(sync_call)
        return response.choices[0].message.content.strip()



class OptionalPlotAgent:
    async def handle(self, user_task: str, df_description: str):
        system_prompt = (
            "Ты Python-ассистент. Сгенерируй исключительно чистый код визуализации с помощью библиотеки Plotly, "
            "используя предоставленные данные. Никаких объяснений. Только исполняемый код, начиная с создания фигуры. "
            "Данные передаются в переменной `df`. Не пиши импорты и загрузку данных. Только код построения графика."
        )
        prompt = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{user_task}\n\nОписание данных:\n{df_description}\n\n"
                                        "Построй визуализацию, если считаешь, что она может дополнить или улучшить ответ, "
                                        "даже если пользователь напрямую не просил график. Если визуализация неуместна, верни пустую строку."}
        ]
        def sync_call():
            return client.chat.completions.create(
                model="gpt-4o",
                messages=prompt
            )
        response = await asyncio.to_thread(sync_call)
        code = response.choices[0].message.content.strip()
        if code.lower() in ("нет", "пусто", "не нужно", ""):
            return ""
        return code

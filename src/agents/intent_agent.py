import asyncio
from src.clients import get_open_ai_client

client = get_open_ai_client()


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

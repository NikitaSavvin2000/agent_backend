import asyncio
import os
from dotenv import load_dotenv
from openai import OpenAI
from src.agents.prompts import visualisation_prompt
from src.agents.main_llm import call_llm
from src.logger import get_logger


logger = get_logger("plot_agent")

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


async def agent_plot_generation(user_task: str, full_describe_data: str, df):
    try:
        logger.info("Отправляем запрос на кодогенерацию графика")

        system_prompt = visualisation_prompt.format(df_description=full_describe_data)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_task}
        ]

        response = call_llm(messages, temperature=0.0, max_tokens=6000)
        code_from_model = response.choices[0].message.content.strip()
        code_from_model = code_from_model.replace('```python', '').replace('```', '')


        mock_py_path = os.path.join(os.getcwd(), "src", "mock_data", "code_from_llm.py")

        # Создать директорию, если не существует
        os.makedirs(os.path.dirname(mock_py_path), exist_ok=True)

        # Сохраняем код в файл
        with open(mock_py_path, "w", encoding="utf-8") as f:
            f.write(code_from_model)

        logger.info("Получили код, выполняем его")

        local_vars = {}
        try:
            exec(code_from_model, {"df": df}, local_vars)
        except Exception as e_exec:
            logger.error(f"Ошибка при выполнении кода LLM: {e_exec}")
            logger.error(f"========================================== Код, вызвавший ошибку: ===================================\n")
            logger.error(f"\n{code_from_model}")
            logger.error(f"====================================================================================================\n")
            return None

        html_output = local_vars.get("html_output")
        df_result = local_vars.get("df_result")

        if html_output is None:
            logger.warning("Переменная html_output не найдена после выполнения кода")

        if df_result is None:
            logger.warning("Переменная df_result не найдена после выполнения кода")

        mock_html_path = os.path.join(os.getcwd(), "src", "mock_data", "mock_chart_from_llm.html")
        os.makedirs(os.path.dirname(mock_html_path), exist_ok=True)

        try:
            with open(mock_html_path, "w", encoding="utf-8") as f:
                f.write(html_output)
            logger.info(f"Файл сохранен по пути: {mock_html_path}")
        except Exception as e_file:
            logger.error(f"Ошибка при сохранении HTML-файла: {e_file}")
            return None

        return html_output, df_result

    except Exception as e:
        logger.error(f"Ошибка в процессе генерации графика: {e}")
        return None
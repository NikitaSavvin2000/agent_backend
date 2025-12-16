import asyncio
import os
from dotenv import load_dotenv
from openai import OpenAI
from src.agents.prompts import analytics_prompt, resonating_prompt, visualisation_prompt
from src.agents.main_llm import call_llm
from src.logger import get_logger
import plotly.io as pio
import base64

logger = get_logger("analytics_agent")

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

async def analytics_resonating_agent(user_task: str, result_analysis: str, meta_for_resonating: str):

    try:
        logger.info("Отправляем запрос на resonating")

        system_prompt = resonating_prompt.format(meta_for_resonating=meta_for_resonating, result_analysis=result_analysis)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_task}
        ]

        response = call_llm(messages, temperature=0.8, max_tokens=6000)
        answer= response.choices[0].message.content.strip()

        return answer

    except Exception as e:
        logger.error(f"Ошибка в процессе обоснования: {e}")
        return None

async def analytics_agent(user_task: str, full_describe_data: str, df):
    try:
        logger.info("Отправляем запрос на кодогенерацию анализа")

        system_prompt = analytics_prompt.format(df_description=full_describe_data)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_task}
        ]

        response = call_llm(messages, temperature=0.0, max_tokens=8000)
        logger.info("Получили ответ, распаковываем его")
        code_from_model = response.choices[0].message.content.strip()
        code_from_model = code_from_model.replace('```python', '').replace('```', '')
        logger.info("Получили код")

        mock_py_path = os.path.join(os.getcwd(), "src", "mock_data", "code_from_llm.py")

        os.makedirs(os.path.dirname(mock_py_path), exist_ok=True)

        # Сохраняем код в файл
        with open(mock_py_path, "w", encoding="utf-8") as f:
            f.write(code_from_model)

        logger.info("Выполняем код")

        local_vars = {}
        try:
            exec(code_from_model, {"df": df}, local_vars)
        except Exception as e_exec:
            logger.error(f"Ошибка при выполнении кода LLM: {e_exec}")
            logger.error(f"Код, вызвавший ошибку:\n{code_from_model}")
            return None

        fig = local_vars.get("fig")
        if fig is not None:
            png_bytes = fig.to_image(format="png")
            png_base64 = base64.b64encode(png_bytes).decode("utf-8")
        else:
            png_base64 = None


        html_output = None
        result_analysis = None

        html_output = local_vars.get("html_output")
        result_analysis = local_vars.get("result_analysis")
        df_result = local_vars.get("df_result")
        meta_for_resonating = local_vars.get("meta_for_resonating")
        need_resonating = local_vars.get("need_resonating")

        if need_resonating:
            result_resonating = await analytics_resonating_agent(user_task, result_analysis, meta_for_resonating)
            if result_analysis is None:
                result_analysis = ""
            result_analysis = str(result_analysis) + '\n## **Обоснование**\n' + str(result_resonating)

        if html_output is None:
            logger.warning("Переменная html_output не найдена после выполнения кода")

        if result_analysis is None:
            logger.warning("Переменная result_analysis не найдена после выполнения кода")

        if df_result is None:
            logger.warning("Переменная result_analysis не найдена после выполнения кода")

        return html_output, png_base64, result_analysis, df_result,

    except Exception as e:
        logger.error(f"Ошибка в процессе генерации анализа: {e}")
        return None
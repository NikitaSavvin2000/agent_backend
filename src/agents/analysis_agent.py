
import asyncio
import os
import json

from dotenv import load_dotenv
from openai import OpenAI

from src.agents.prompts import analytics_prompt, resonating_prompt, visualisation_prompt
from src.agents.main_llm import call_llm
from src.logger import get_logger

logger = get_logger("analytics_agent")

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


async def analytics_resonating_agent(
    user_task: str,
    result_analysis: str,
    meta_for_resonating: str,
):
    """
    Агент-обоснование: на вход получает текст анализа + метаданные,
    возвращает текстовое обоснование (строку) либо None при ошибке.
    """
    try:
        logger.info("Отправляем запрос на resonating")

        system_prompt = resonating_prompt.format(
            meta_for_resonating=meta_for_resonating,
            result_analysis=result_analysis,
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_task},
        ]

        response = call_llm(messages, temperature=0.0, max_tokens=6000)
        if response is None:
            logger.error("call_llm вернул None в analytics_resonating_agent")
            return None

        try:
            answer = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Не удалось распарсить ответ LLM в resonating: {e}")
            return None

        return answer

    except Exception as e:
        logger.error(f"Ошибка в процессе обоснования: {e}")
        return None


async def analytics_agent(user_task: str, full_describe_data: str, df):
    """
    Основной агент анализа:
    - генерирует код анализа по описанию df,
    - выполняет код,
    - забирает html_output / result_analysis / df_result из локальных переменных,
    - опционально добавляет обоснование (resonating).
    """
    try:
        logger.info("Отправляем запрос на кодогенерацию анализа")

        system_prompt = analytics_prompt.format(df_description=full_describe_data)
        # Альтернативный промпт для визуализаций:
        # system_prompt = visualisation_prompt.format(df_description=full_describe_data)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_task},
        ]

        response = call_llm(messages, temperature=0.0, max_tokens=8000)
        if response is None:
            logger.error("call_llm вернул None в analytics_agent")
            return None, "Не удалось получить ответ от модели при генерации анализа.", None

        logger.info("Получили ответ, распаковываем его")

        try:
            code_from_model = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Не удалось достать code_from_model из ответа LLM: {e}")
            return None, "Не удалось разобрать ответ модели при генерации анализа.", None

        # Убираем обёртку ```python ... ```
        code_from_model = (
            code_from_model.replace("```python", "").replace("```", "")
        )
        logger.info("Получили код")

        # Сохраняем код в mock-файл (для отладки)
        mock_py_path = os.path.join(
            os.getcwd(), "src", "mock_data", "code_from_llm.py"
        )
        os.makedirs(os.path.dirname(mock_py_path), exist_ok=True)
        with open(mock_py_path, "w", encoding="utf-8") as f:
            f.write(code_from_model)

        logger.info("Выполняем код")

        local_vars: dict = {}

        try:
            # В коде модель ожидает, что df уже доступен
            exec(code_from_model, {"df": df}, local_vars)
        except Exception as e_exec:
            logger.error(f"Ошибка при выполнении кода LLM: {e_exec}")
            logger.error(f"Код, вызвавший ошибку:\n{code_from_model}")
            # Возвращаем аккуратный ответ, чтобы фронт не падал
            return (
                None,
                "Во время выполнения сгенерированного кода анализа произошла ошибка.",
                None,
            )

        # Инициализация выходных переменных
        html_output = local_vars.get("html_output")
        result_analysis = local_vars.get("result_analysis")
        df_result = local_vars.get("df_result")
        meta_for_resonating = local_vars.get("meta_for_resonating")
        need_resonating = local_vars.get("need_resonating")

        if html_output is None:
            logger.warning("Переменная html_output не найдена после выполнения кода")

        if result_analysis is None:
            logger.warning(
                "Переменная result_analysis не найдена после выполнения кода"
            )

        if df_result is None:
            logger.warning(
                "Переменная df_result не найдена после выполнения кода"
            )

        # --- Блок обоснования (resonating) ---
        if need_resonating and result_analysis is not None:
            result_resonating = await analytics_resonating_agent(
                user_task=user_task,
                result_analysis=str(result_analysis),
                meta_for_resonating=str(meta_for_resonating),
            )

            if result_resonating:
                # Если result_analysis не строка — безопасно приводим к строке/JSON
                if isinstance(result_analysis, str):
                    base_text = result_analysis
                else:
                    logger.warning(
                        "result_analysis имеет тип %s, приводим к строке",
                        type(result_analysis),
                    )
                    try:
                        base_text = json.dumps(
                            result_analysis,
                            ensure_ascii=False,
                            indent=2,
                        )
                    except Exception:
                        base_text = str(result_analysis)

                result_analysis = (
                    base_text
                    + "\n\n## **Обоснование**\n"
                    + result_resonating
                )

        # ✅ Всегда возвращаем тройку, чтобы сверху не было ошибок распаковки
        return html_output, result_analysis, df_result

    except Exception as e:
        logger.error(f"Ошибка в процессе генерации анализа: {e}")
        return (
            None,
            "Во время генерации анализа произошла внутренняя ошибка.",
            None,
        )

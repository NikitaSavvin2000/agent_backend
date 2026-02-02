from src.agents.prompts import simple_answer_prompt, fill_empty_answer_prompt, describe_about_agent_prompt
from src.agents.main_llm import call_llm
from src.logger import get_logger

logger = get_logger("agent_simple_answer")

async def simple_agent_answer(user_task: str):
    try:
        logger.info("Отправляем запрос на простой ответ модели")

        system_prompt = simple_answer_prompt
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_task}
        ]

        response = call_llm(messages, temperature=1.2, max_tokens=1000)
        answer = response.choices[0].message.content.strip()
        return answer
    except Exception as e:
        logger.error(f"Ошибка в процессе генерации простого ответа: {e}")
        return None


async def fill_empty_agent_answer(user_task: str, describe_df: str = None):
    system_prompt = fill_empty_answer_prompt.format(user_task=user_task)
    try:
        logger.info("Отправляем запрос на формирование резюме работы агента")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Описание данных: {describe_df}" if describe_df else "Нет описания данных."}
        ]

        response = call_llm(messages, temperature=1.2, max_tokens=500)
        answer = response.choices[0].message.content.strip()
        return answer
    except Exception as e:
        logger.error(f"Ошибка в процессе генерации резюме: {e}")
        return None


async def answer_describe_about_agent(user_message: str):
    system_prompt = describe_about_agent_prompt.format(user_message=user_message)
    try:
        logger.info("Отправляем запрос на формирование резюме работы агента")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{user_message}"}
        ]

        response = call_llm(messages, temperature=1.2, max_tokens=1000)
        answer = response.choices[0].message.content.strip()
        return answer
    except Exception as e:
        logger.error(f"Ошибка в процессе генерации резюме: {e}")
        return None
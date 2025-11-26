from src.agents.prompts import simple_answer_prompt
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
from src.agents.prompts import agent_intent_prompt, intent_data_context_prompt, build_agent_intent_prompt
from src.agents.main_llm import call_llm
import ast
from src.logger import get_logger

logger = get_logger("intend_agent")


def get_agent_tools(user_query: str, message_context: str, user_means_context: bool):
    logger.info(f"Определение вызова инструментов")

    system_prompt = build_agent_intent_prompt(message=user_query, message_context=message_context, user_means_context=user_means_context)
    messages = [
        # {"role": "system", "content": agent_intent_prompt},
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ]
    response = call_llm(messages, temperature=0.0, max_tokens=200)
    result_str =  response.choices[0].message.content
    try:
        result_list = ast.literal_eval(result_str)
        if isinstance(result_list, list):
            return result_list
        else:
            return [result_list]
    except Exception as e:
        logger.error(f"Определение вызова инструментов ощибка {e}")
        return [result_str]

def normalize_index(data_index):
    if data_index is None:
        return None
    if isinstance(data_index, str):
        if data_index.lower() == "none":
            return None
        if data_index.isdigit():
            return int(data_index)
    if isinstance(data_index, int):
        return data_index
    return None


async def intent_data_context(user_query, llm_context: str ):
    logger.info(f"Определение контекта данных")

    system_prompt = intent_data_context_prompt.format(context=llm_context)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ]
    response = call_llm(messages, temperature=0.0, max_tokens=200)
    data_index = response.choices[0].message.content
    try:
        data_index = normalize_index(data_index=data_index)
        return data_index
    except Exception as e:
        logger.error(f" func intent_data_context ощибка {e}")
        return data_index

# if __name__ == "__main__":
#     query = "Сделай мне визуализацию данных и проанализируй аномалии"
#     tools = get_agent_tools(query)
#     print(tools)
#     for tool in tools:
#         print(tool)
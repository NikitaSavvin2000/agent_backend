import requests
import os
from dotenv import load_dotenv
from openai import OpenAI
from src.agents.prompts import  intend_forecast_params_prompt, intend_horizon_time_prompt, summary_for_forecast_prompt
from src.agents.main_llm import call_llm
from src.logger import get_logger
import json
import pandas as pd

logger = get_logger("forecast_agent")
load_dotenv()

url = os.getenv("FORECAST_API")


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

async def intend_horizon_time(df, user_task, time_col):
    df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
    last_date = df[time_col].max()
    last_time_value = last_date.strftime("%Y-%m-%d %H:%M:%S")

    try:
        logger.info("Отправляем запрос на intend_horizon_time")

        system_prompt = intend_horizon_time_prompt.format(last_time_value=last_time_value)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_task}
        ]

        response = call_llm(messages, temperature=0.0, max_tokens=6000)
        horizon_time = response.choices[0].message.content.strip()
        return horizon_time

    except Exception as e:
        logger.error(f"Ошибка в процессе генерации horizon_time: {e}")
        return None


async def intend_forecast_params(df, user_task, description_df):

    try:
        logger.info("Отправляем запрос на intend_forecast_params")

        system_prompt = intend_forecast_params_prompt.format(description_df=description_df)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_task}
        ]

        response = call_llm(messages, temperature=0.0, max_tokens=6000)
        answer = response.choices[0].message.content.strip()
        params = json.loads(answer)

        time_col = params.get("time_col")
        target_col = params.get("target_col")

        horizon_time = await intend_horizon_time(df, user_task, time_col)

        return time_col, target_col, horizon_time

    except Exception as e:
        logger.error(f"Ошибка в процессе генерации intend_forecast_params: {e}")
        return None


async def summary_for_forecast(user_task, meta_info):

    try:
        logger.info("Отправляем запрос на summary_for_forecast")

        system_prompt = summary_for_forecast_prompt.format(meta_info=meta_info)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_task}
        ]

        response = call_llm(messages, temperature=1.6, max_tokens=6000)
        answer = response.choices[0].message.content.strip()
        return answer

    except Exception as e:
        logger.error(f"Ошибка в процессе генерации horizon_time: {e}")
        return None

async def forecast_request(df, user_task, description_df):

    time_col, target_col, horizon_time = await intend_forecast_params(df=df, user_task=user_task, description_df=description_df)
    df[time_col] = df[time_col].astype(str)
    payload = {
        "df": df.to_dict(orient="records"),
        "time_column": time_col,
        "col_target": target_col,
        "forecast_horizon_time": horizon_time
    }
    response = requests.post(url, json=payload)
    return response.json()
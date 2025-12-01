import json
import os
import uuid
import logging
from datetime import datetime
from typing import Annotated, Optional, Any, Dict, List
from src.agents.intent_agent import get_agent_tools
import pandas as pd
import uvicorn
from dotenv import load_dotenv
from fastapi import (
    APIRouter, FastAPI, HTTPException, Depends, Body, Path, Query, Form, File, UploadFile
)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine

from src.config import public_or_local
from src.core.security.password import decrypt_password
from src.core.token import jwt_token_validator
from src.session import db_manager
from src.utils.log_chat_message import insert_message_to_db
from src.utils.s3_loader import upload_to_s3, load_from_s3
from src.utils.chats import get_history_by_chat_id, create_new_chat, get_user_chats, delete_chat
from src.models.organization_models import ConnectionSettings
from src.mock_data.mock_html import generate_mock_timeseries_html
from src.services.fetch_data import fetch_example_data
from src.utils.describe_df import describe_df_for_llm_verbose
from src.agents.plot_agent import agent_plot_generation
from src.agents.agent_answer import simple_agent_answer
from src.agents.analysis_agent import analytics_agent
from src.agents.forecast_agent import forecast_request, summary_for_forecast

sep_system_file_name_key = "_1s2e3p4_"


async def fake_agent_answer(
        message: str,
        organization_id: int,
        connection_id: Optional[int] = None,
        table_name: Optional[str] = None,
        s3_key: Optional[str] = None,
        call_agent: Optional[str] = None,
        agent_form_str: Optional[str] = None
):
    words = ["исуй", "отобрази", "draw", "chart", "граф", "anaли", "analys"]
    message_html_code = None
    message_tables = []
    if connection_id is not None and table_name is not None and any(word in message for word in words):
        table = {}
        df = await fetch_example_data(connection_id=connection_id, source_table=table_name, organization_id=organization_id)
        generate_mock_timeseries_html(df=df)

        df["datetime"] = df["datetime"].astype(str)
        records = df.to_dict(orient="records")
        df_json_str = json.dumps(records, ensure_ascii=False)
        table[table_name] = df_json_str
        message_tables.append(table)
        mock_html_path = os.path.join(home, "src", "mock_data", "mock_chart.html")

        with open(mock_html_path, "r", encoding="utf-8") as f:
            chart_html = f.read()

        message_html_code = f"""
                    <div>
                    {chart_html}
                    </div>
                """

    agent_form = json.loads(agent_form_str) if agent_form_str else None

    agent_message = (
        "# Привет, я агент\n\n"
        "## Cкоро начну работать я в разработке\n\n"
        "### Твое сообщение:\n\n"
        f"{message}"
    )

    if s3_key:
        table = {}
        df = await load_from_s3(file_key=s3_key)
        records = df.to_dict(orient="records")
        df_json_str = json.dumps(records, ensure_ascii=False)
        parts = s3_key.split(sep_system_file_name_key)
        init_file_name = os.path.splitext(parts[0])[0].split("/")[1]
        table[init_file_name] = df_json_str
        message_tables.append(table)
    message_links = {"link_1": "https://example.com"}
    agent_data_s3_key = s3_key

    return {
        "agent_message": agent_message,
        "message_html_code": message_html_code,
        "message_tables": message_tables,
        "message_links": message_links,
        "agent_data_s3_key": agent_data_s3_key,
        "call_agent": call_agent,
        "agent_form": agent_form
    }

async def pre_fill_forecast_form(df):
    forecast_agent_form = {}
    return forecast_agent_form


async def agent_answer(
        message: str,
        organization_id: int,
        connection_id: Optional[int] = None,
        table_name: Optional[str] = None,
        s3_key: Optional[str] = None,
        call_agent: Optional[str] = None,
        agent_form_str: Optional[str] = None
):

    agent_message = None
    message_html_code = None
    message_tables = []
    message_links = []
    agent_data_s3_key = None
    call_agent = None
    agent_form = None

    list_to_call_services = get_agent_tools(user_query=message)

    for service in list_to_call_services:
        print(service)

    if connection_id and table_name and s3_key is None:
        df = await fetch_example_data(connection_id=connection_id, source_table=table_name, organization_id=organization_id)
        describe_df = describe_df_for_llm_verbose(df=df)
    elif s3_key:
        df = await load_from_s3(file_key=s3_key)
        describe_df = describe_df_for_llm_verbose(df=df)
    else:
        df = None
        describe_df = None

    if call_agent == "forecast":
        pass

    if "visualization" in list_to_call_services and df is not None:
        message_html_code, df_result = await agent_plot_generation(user_task=message, full_describe_data=describe_df, df=df)
        agent_message = "Готова твоя визуализация по запросу"
        if df_result is not None:
            df_result = df_result.astype(str)
            message_tables.append(json.loads(df_result.to_json(orient='records', force_ascii=False)))

    if "analysis" in list_to_call_services and df is not None:
        message_html_code, result_analysis, df_result = await analytics_agent(user_task=message, full_describe_data=describe_df, df=df)
        agent_message = result_analysis
        if df_result is not None:
            df_result = df_result.astype(str)
            message_tables.append(json.loads(df_result.to_json(orient='records', force_ascii=False)))

    if "none" in list_to_call_services and df is not None:
        agent_message = await simple_agent_answer(user_task=message)


    if "forecast" in list_to_call_services and df is not None:

        result = await forecast_request(df=df, user_task=message, description_df=describe_df)

        meta_info = result.get("meta_info")
        message_html_code = result.get("html_chart")
        predict_table = result.get("predict_table")

        message_tables.append(predict_table)

        agent_message = await summary_for_forecast(user_task=message, meta_info=meta_info)

        print(agent_message)


    # agent_message = "Дозаполните форму и проверьте данные"
        # if df is None:
        #     agent_message = "Загрузите или выберите данные"
        #     agent_form = await pre_fill_forecast_form(df)





    if agent_message is None:
        agent_message = await simple_agent_answer(user_task=message)

    agent_data_s3_key = s3_key

    return {
            "agent_message": agent_message,
            "message_html_code": message_html_code,
            "message_tables": message_tables,
            "message_links": message_links,
            "agent_data_s3_key": agent_data_s3_key,
            "call_agent": call_agent,
            "agent_form": agent_form
        }
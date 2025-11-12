import json
import os
import uuid
import logging
from datetime import datetime
from typing import Annotated, Optional, Any, Dict, List

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
from src.utils.log_chat_massage import insert_message_to_db
from src.utils.s3_loader import upload_to_s3, load_from_s3
from src.utils.chats import get_history_by_chat_id, create_new_chat, get_user_chats, delete_chat
from src.models.organization_models import ConnectionSettings
from src.mock_data.mock_html import generate_mock_timeseries_html
from src.services.fetch_data import fetch_example_data


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

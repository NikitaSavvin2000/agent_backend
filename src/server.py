import io
import json
import logging
import os
from typing import Annotated, Optional
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Depends, Body, Path, Query, Form

from src.core.token import jwt_token_validator
import uuid
from src.mock_data.mock_html import generate_mock_timeseries_html

import pandas as pd
import uvicorn
from fastapi import Body, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from src.utils.log_chat_massage import insert_message_to_db
from src.agents.coordinator import Coordinator
from src.config import public_or_local
from src.models.schemes import ChatRequest, ChatDataRequest
from src.utils.s3_loader import upload_to_s3, load_from_s3
from dotenv import load_dotenv
import logging
from datetime import datetime


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

home = os.getcwd()
path_to_mock = os.path.join(home, "src", "mock_data", "morocco zone 2 - powerconsumption_resampled.csv")

load_dotenv()
mock_mode = os.getenv("MOCK_MODE")



if public_or_local == 'LOCAL':
    url = 'http://localhost'
else:
    url = 'http://11.11.11.11'

origins = [
    url
]
docs_url = "/horizon_chat"
app = FastAPI(docs_url=docs_url, openapi_url=f'{docs_url}/openapi.json')
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

df_example = pd.read_csv(path_to_mock)

col_time = "Datetime"
col_target = "consumption"

json_data = df_example.to_dict(orient="records")

import plotly.express as px

fig = px.line(df_example, x=col_time, y=col_target, title="Визуализация временного ряда")
html_output = fig.to_html()

mock_result = {}
mock_result["data"] = json_data
mock_result["html"] = html_output
mock_result["message"] = 'Отрисовали моковый график'



cwd = os.getcwd()
chat_histories = os.path.join(cwd, "src", "chat_histories")

sep_system_file_name_key = "_1s2e3p4_"

async def fake_agent_answer(
        message: str,
        connection_id: Optional[int] = None,
        table_name: Optional[str] = None,
        s3_key: Optional[str] = None,
        call_agent: Optional[str] = None,
        agent_form_str: Optional[str] = None
):

    agent_form = json.loads(agent_form_str) if agent_form_str else None
    agent_message = (
        "# Привет, я агент\n\n"
        "## Cкоро начну работать я в разработке\n\n"
        "### Твое сообщение:\n\n"
        f"{message}"
    )
    generate_mock_timeseries_html()
    mock_html_path = os.path.join(home, "src", "mock_data", "mock_chart.html")

    with open(mock_html_path, "r", encoding="utf-8") as f:
        chart_html = f.read()

    message_html_code = f"""
            <div>
            {chart_html}
            </div>
        """
    message_tables = []
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


@app.post(
    "/chat",
    summary="Обработка пользовательского запроса с возможной загрузкой файла",
    description="""
    Принимает обязательные поля chat_id и message.
    Необязательные — connection_id, table_name.
    Также можно загрузить CSV/XLSX файл.
    """
)
async def chat_upload(
        chat_id: Annotated[int, Form(...)],
        message: Annotated[Optional[str], Form()] = 'Привет',
        connection_id: Annotated[Optional[int], Form()] = None,
        table_name: Annotated[Optional[str], Form()] = None,
        file: Optional[UploadFile] = None,
        call_agent: Annotated[Optional[str], Form()] = 'forecast',
        agent_form_str: Annotated[Optional[str], Form()] = '{"test": 1}',
        user: dict = Depends(jwt_token_validator)
):
    if isinstance(file, str) or not file:
        file = None

    agent_form: Optional[dict] = None
    if agent_form_str:
        try:
            agent_form = json.loads(agent_form_str)
        except json.JSONDecodeError:
            agent_form = None

    if message is None and call_agent is None:
        answer = "Введите сообщение"
        return answer
    s3_key = None

    if file:
        original_filename = file.filename
        name, ext = os.path.splitext(original_filename)
        ext = ext.lower().lstrip(".")
        uuid_code = uuid.uuid4()
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        upload_time = f"_upload_time_{current_time}"
        system_file_name =  name + upload_time + sep_system_file_name_key + str(uuid_code) + "." + ext
        file.filename = system_file_name
        s3_key = await upload_to_s3(file=file, folder="users_downloads")

    role = user.get("roles", [])[0]
    user_id = int(user.get("sub", None))

    # ===================================== Запись сообщения пользователя в базу =================================================
    await insert_message_to_db(
        chat_id=chat_id,
        user_id=user_id,
        role=role,
        message=message,
        message_html_code=None,
        message_tables=None,
        message_links=None,
        data_path=s3_key,
        connection_id=connection_id,
        table_name=table_name,
        call_agent=call_agent,
        agent_form=agent_form,
    )
    # =================================================================================================================


    # ===================================== ЗДЕСЬ БУДЕТ ЛОГИКА АГЕНТА =================================================
    agent_role = "agent"

    answer_dict = await fake_agent_answer(message=message,
                                        connection_id=connection_id,
                                        table_name=table_name,
                                        s3_key=s3_key,
                                        call_agent=call_agent,
                                        agent_form_str=agent_form_str)

    agent_message = answer_dict.get("agent_message", None)
    message_html_code = answer_dict.get("message_html_code", None)
    message_tables = answer_dict.get("message_tables", [])
    message_links = answer_dict.get("message_links", {})
    agent_data_s3_key = answer_dict.get("agent_data_s3_key", None)
    call_agent = answer_dict.get("call_agent", None)
    agent_form = answer_dict.get("agent_form", None)

    # =================================================================================================================


    # ===================================== Запись ответа агента в базу ================================================
    await insert_message_to_db(
        chat_id=chat_id,
        user_id=user_id,
        role=agent_role,
        message=agent_message,
        message_html_code=message_html_code,
        message_tables=message_tables,
        message_links=message_links,
        data_path=agent_data_s3_key,
        connection_id=connection_id,
        table_name=table_name,
        call_agent=call_agent,
        agent_form=agent_form,
    )

    # =================================================================================================================

    return {
        "chat_id": chat_id,
        "user_id": user_id,
        "role": agent_role,
        "message": agent_message,
        "message_html_code": message_html_code,
        "message_tables": message_tables,
        "message_links": message_links,
        "data_path": agent_data_s3_key,
        "connection_id": connection_id,
        "table_name": table_name,
        "call_agent": call_agent,
        "agent_form": agent_form,
    }



@app.get("/")
def read_root():
    return {"message": "Welcome to the indicators System API"}


if __name__ == "__main__":
    port = 7070
    print(f'🚀 Документация http://0.0.0.0:{port}{docs_url}')
    uvicorn.run("server:app", host="0.0.0.0", port=port, workers=2, log_level="debug")

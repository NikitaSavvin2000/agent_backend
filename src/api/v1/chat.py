import json
import os
import uuid
from datetime import datetime
from typing import Annotated, Optional, Any, Dict, List
from fastapi import (
    APIRouter, FastAPI, HTTPException, Depends, Body, Path, Query, Form, File, UploadFile
)
from src.core.token import jwt_token_validator
from src.utils.log_chat_message import insert_message_to_db
from src.utils.s3_loader import upload_to_s3
from src.services.agent import fake_agent_answer
from src.utils.chats import create_new_chat

sep_system_file_name_key = "_1s2e3p4_"

app = APIRouter()

@app.post(
    "",
    summary="Обработка пользовательского запроса с возможной загрузкой файла",
    description="""
    Принимает обязательные поля chat_id и message.
    Необязательные — connection_id, table_name.
    Также можно загрузить CSV/XLSX файл.
    """
)
async def chat(
        chat_id: Annotated[Optional[int], Form(...)] = None,
        message: Annotated[Optional[str], Form()] = 'Привет',
        connection_id: Annotated[Optional[int], Form()] = None,
        table_name: Annotated[Optional[str], Form()] = None,
        file: Optional[UploadFile] = None,
        call_agent: Annotated[Optional[str], Form()] = 'forecast',
        agent_form_str: Annotated[Optional[str], Form()] = '{"test": 1}',
        user: dict = Depends(jwt_token_validator),
):
    user_id = int(user.get("sub", None))
    print(chat_id)
    chat_name = None
    if chat_id is None:
        chat_id, chat_name = await create_new_chat(user_id=user_id, message=message)
    role = user.get("roles", [])[0]
    organization_id = int(user.get("organization_id", None))


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
                                          organization_id=organization_id,
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
        "chat_name": chat_name
    }

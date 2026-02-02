import json
import os
import uuid
from datetime import datetime
from typing import Annotated, Optional, Any, Dict, List, Union
from fastapi import (
    APIRouter, FastAPI, HTTPException, Depends, Body, Path, Query, Form, File, UploadFile
)
from src.core.token import jwt_token_validator
from src.utils.log_chat_message import insert_message_to_db
from src.utils.s3_loader import upload_to_s3
from src.services.agent import agent_answer
from src.utils.chats import create_new_chat
from src.utils.chats import get_context_by_role
from src.agents.intent_agent import intent_data_context
import asyncio
sep_system_file_name_key = "_1s2e3p4_"

app = APIRouter()

LIMIT_CONTEXT_MASSAGES = 7

error_mock_massage = """
## 🤖 404 - Агент временно недоступен

Наш ИИ-аналитик по неизвестным причинам не дал ответа.  
Мы уже работаем над решением, попробуйте повторить запрос чуть-чуть позднее.

## 📞 Связь с основателями

Если возникнут вопросы — пишите в телеграм:  
Саввин Никита — [https://t.me/SavvinNikita](https://t.me/SavvinNikita)  
Васенин Дмитрий — [https://t.me/dvasenin](https://t.me/dvasenin)

"""

def _str_to_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None

def _str_to_file(file: str | None) -> int | None:
    if file is None or file == "":
        return None
    else:
        return file

async def create_context_for_llm(context):
        data_context_by_message = ''
        for i in range(len(context)):
            data_context_by_message += f"{i} | {context[i]["message"]}\n"
        return data_context_by_message

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
        chat_id: Annotated[Union[int, str, None], Form()] = None,
        message: Annotated[Union[str, None], Form()] = 'Привет',
        connection_id: Annotated[Union[int, str, None], Form()] = None,
        table_name: Annotated[Union[str, None], Form()] = None,
        file: Annotated[Union[UploadFile, str, None], Form()] = None,
        call_agent: Annotated[Optional[str], Form()] = 'forecast',
        agent_form_str: Annotated[Optional[str], Form()] = '{"test": 1}',
        user: dict = Depends(jwt_token_validator),
):

    chat_name = None
    context = None
    s3_key_context = None
    s3_key = None
    data_index = None
    user_means_context = False
    message_context = None


    user_id = int(user.get("sub", None))
    role = user.get("roles", [])[0]
    organization_id = int(user.get("organization_id", None))

    file = _str_to_file(file)

    chat_id = _str_to_int(chat_id)
    connection_id = _str_to_int(connection_id)

    if table_name == "":
        table_name = None

    if chat_id is None:
        chat_id, chat_name = await create_new_chat(user_id=user_id, message=message)
    else:
        # если чат не новый смотрим на контекст данных
        context = await get_context_by_role(chat_id=chat_id, role=role, limit=LIMIT_CONTEXT_MASSAGES)
        llm_context = await create_context_for_llm(context=context)
        data_index = await intent_data_context(user_query=message, llm_context=llm_context)

    if data_index is not None:
        s3_key_context = context[data_index]["result_s3_key"]
        message_context = context[data_index]["message"]
        user_means_context = True

    if isinstance(file, str) or not file:
        file = None

    if agent_form_str:
        try:
            agent_form = json.loads(agent_form_str)
        except json.JSONDecodeError:
            agent_form = None

    if message is None and call_agent is None:
        answer = "Введите сообщение"
        return answer

    if file and s3_key_context is None:
        original_filename = file.filename
        name, ext = os.path.splitext(original_filename)
        ext = ext.lower().lstrip(".")
        uuid_code = uuid.uuid4()
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        upload_time = f"_upload_time_{current_time}"
        system_file_name =  name + upload_time + sep_system_file_name_key + str(uuid_code) + "." + ext
        file.filename = system_file_name
        s3_key = await upload_to_s3(file=file, folder="users_downloads")
    else:
        s3_key = s3_key_context

    # ===================================== ЗДЕСЬ ЛОГИКА АГЕНТА =================================================
    agent_role = "agent"

    try:
        answer_dict = await agent_answer(message=message,
                           organization_id=organization_id,
                           connection_id=connection_id,
                           table_name=table_name,
                           s3_key=s3_key,
                           call_agent=call_agent,
                           agent_form_str=agent_form_str,
                           message_context=message_context,
                           user_means_context=user_means_context
                            )

        agent_message = answer_dict.get("agent_message", None)
        message_html_code = answer_dict.get("message_html_code", None)
        message_tables = answer_dict.get("message_tables", [])
        message_links = answer_dict.get("message_links", {})
        agent_data_s3_key = answer_dict.get("agent_data_s3_key", None)
        answer_call_agent = answer_dict.get("call_agent", None)
        answer_agent_form = answer_dict.get("agent_form", None)
        s3_key_answer = answer_dict.get("s3_key_answer", None)
        doc_base64 = answer_dict.get("doc_base64", None)
        docs_name = answer_dict.get("docs_name", None)
    except Exception as e:
        answer_dict = {}
        agent_message = answer_dict.get("agent_message", error_mock_massage)
        message_html_code = answer_dict.get("message_html_code", None)
        message_tables = answer_dict.get("message_tables", [])
        message_links = answer_dict.get("message_links", {})
        agent_data_s3_key = answer_dict.get("agent_data_s3_key", None)
        answer_call_agent = answer_dict.get("call_agent", None)
        answer_agent_form = answer_dict.get("agent_form", None)
        s3_key_answer = answer_dict.get("s3_key_answer", None)
        doc_base64 = answer_dict.get("doc_base64", None)
        docs_name = answer_dict.get("docs_name", None)

    # =================================================================================================================


    # ===================================== Запись вопроса пользователя и ответа агента в базу ================================================

    for args in [
        {
            "chat_id": chat_id,
            "user_id": user_id,
            "role": role,
            "message": message,
            "message_html_code": None,
            "message_tables": None,
            "message_links": None,
            "data_path": s3_key,
            "result_s3_key": s3_key_answer,
        },
        {
            "chat_id": chat_id,
            "user_id": user_id,
            "role": agent_role,
            "message": agent_message,
            "message_html_code": message_html_code,
            "message_tables": message_tables,
            "message_links": message_links,
            "data_path": agent_data_s3_key,
            "result_s3_key": s3_key_answer
        }
    ]:
        asyncio.create_task(
            insert_message_to_db(
                connection_id=connection_id,
                table_name=table_name,
                call_agent=call_agent,
                agent_form=agent_form,
                **args
            )
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
        "call_agent": answer_call_agent,
        "agent_form": answer_agent_form,
        "chat_name": chat_name,
        "doc_base64": doc_base64,
        "docs_name": docs_name
    }

from fastapi import (
    APIRouter, FastAPI, HTTPException, Depends, Body, Path, Query, Form, File, UploadFile
)
from src.core.token import jwt_token_validator
from src.utils.chats import create_new_chat

app = APIRouter()


@app.post(
    "/",
    summary="Создание нового чата",
    description="""
    Принимает обязательные поля chat_id и message.
    Необязательные — connection_id, table_name.
    Также можно загрузить CSV/XLSX файл.
    """
)
async def func_create_new_chat(
        user: dict = Depends(jwt_token_validator)
):
    user_id = int(user.get("sub", None))
    chat_id = await create_new_chat(user_id=user_id)
    return {"massage": "Чат успешно создан", "chat_id": chat_id}



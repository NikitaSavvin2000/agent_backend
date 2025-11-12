from fastapi import (
    APIRouter, FastAPI, HTTPException, Depends, Body, Path, Query, Form, File, UploadFile
)
from src.core.token import jwt_token_validator
from src.utils.chats import get_user_chats

app = APIRouter()

@app.get(
    "/",
    summary="Получение списка чатов пользователя",
    description="""
    Возвращает список всех чатов, связанных с указанным пользователем.
    Каждый элемент списка содержит информацию о чате:
    chat_id, название, дату создания и другие метаданные.
    """
)
async def get_user_chats_ids(
        user: dict = Depends(jwt_token_validator)
):
    user_id = int(user.get("sub", None))
    user_chat_ids = await get_user_chats(user_id=user_id)
    return {"massage": "Чаты юзера", "user_chat_ids": user_chat_ids}


from fastapi import (
    APIRouter, FastAPI, HTTPException, Depends, Body, Path, Query, Form, File, UploadFile
)
from src.core.token import jwt_token_validator

from src.utils.chats import get_history_by_chat_id

app = APIRouter()

@app.get(
    "",
    summary="Получение истории чата",
    description="""
    Принимает обязательное поле chat_id.
    Возвращает историю сообщений для указанного чата.
    """
)
async def chat_history(
        chat_id: int = Query(...),
        user: dict = Depends(jwt_token_validator)
):
    history = await get_history_by_chat_id(chat_id, user)
    return history

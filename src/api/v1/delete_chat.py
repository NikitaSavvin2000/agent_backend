from fastapi import (
    APIRouter, FastAPI, HTTPException, Depends, Body, Path, Query, Form, File, UploadFile
)
from src.core.token import jwt_token_validator
from src.utils.chats import delete_chat

app = APIRouter()

@app.delete(
    "/",
    summary="Удаление чата",
    description="""
    Принимает обязательное поле chat_id.
    Помечает чат как удалённый, выставляя is_deleted = True и время deleted_at.
    """
)
async def delete_chat_endpoint(
        chat_id: int = Query(...),
        user: dict = Depends(jwt_token_validator)
):
    user_id = int(user.get("sub", None))
    result = await delete_chat(chat_id=chat_id, user_id=user_id)
    return result

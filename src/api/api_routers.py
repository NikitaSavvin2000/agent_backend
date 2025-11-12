from fastapi import APIRouter

api_router = APIRouter()


from src.api.v1.chat import app as chat

api_router.include_router(chat, prefix="/chat", tags=["Chat"])

from src.api.v1.chat_history import app as chat_history
api_router.include_router(chat_history, prefix="/chat_history", tags=["Chat History"])

from src.api.v1.create_chat import app as create_chat
api_router.include_router(create_chat, prefix="/create_new_chat", tags=["Create Chat"])

from src.api.v1.delete_chat import app as delete_chat
api_router.include_router(delete_chat, prefix="/delete_chat", tags=["Delete Chat"])

from src.api.v1.user_chats import app as user_chats
api_router.include_router(user_chats, prefix="/user_chats_ids", tags=["User Chats"])

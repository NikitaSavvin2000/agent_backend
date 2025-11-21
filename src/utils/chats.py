from src.models.user_models import Chats
from sqlalchemy import select, insert, update
from datetime import datetime
from fastapi import HTTPException
from src.models.user_models import Message
from src.logger import get_logger
from src.session import db_manager
from sqlalchemy import select, text
import random

logger = get_logger("chat_operations")


async def test_chat_naming(s):
    if len(s) > 10:
        base = s[:10]
    else:
        base = s
    extra = ''.join(random.choice(s) for _ in range(3))
    return base + extra + "..."


async def create_new_chat(user_id: int, message: str) -> int:
    """
    Создаёт новый чат для пользователя и возвращает chat_id
    """
    chat_name = await test_chat_naming(message)
    try:
        async with db_manager.get_db_session() as session:
            stmt = insert(Chats).values(
                user_id=user_id,
                chat_name=chat_name,
                created_at=datetime.utcnow()
            ).returning(Chats.chat_id)
            result = await session.execute(stmt)
            await session.commit()
            chat_id = result.scalar_one()
            logger.info(f"Создан новый чат ID {chat_id} с именем {chat_name} для пользователя {user_id}")
            return chat_id, chat_name
    except Exception as e:
        logger.error(f"Ошибка при создании нового чата: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при создании нового чата")


async def get_user_chats(user_id: int) -> list[dict]:
    """
    Возвращает список всех чатов пользователя, которые не удалены,
    в виде словарей с chat_id и chat_name
    """
    try:
        async with db_manager.get_db_session() as session:
            result = await session.execute(
                select(Chats.chat_id, Chats.chat_name)
                .where(
                    (Chats.user_id == user_id) &
                    (Chats.deleted_at.is_(None))
                )
                .order_by(Chats.created_at.asc())
            )
            chats = [{"chat_id": row.chat_id, "chat_name": row.chat_name} for row in result.fetchall()]
            logger.info(f"Загружено {len(chats)} чатов для пользователя {user_id}")
            return chats
    except Exception as e:
        logger.error(f"Ошибка при получении чатов пользователя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при загрузке списка чатов")


async def get_history_by_chat_id(chat_id: int, user_id: int):
    try:
        logger.info(f"Загрузка сообщений для чата ID {chat_id}")
        async with db_manager.get_db_session() as session:
            result = await session.execute(
                select(
                    Message.id,
                    Message.chat_id,
                    Message.user_id,
                    Message.role,
                    Message.message,
                    Message.message_html_code,
                    Message.message_tables,
                    Message.message_links,
                    Message.data_path,
                    Message.connection_id,
                    Message.table_name,
                    Message.call_agent,
                    Message.agent_form,
                    Message.created_at,
                    Message.deleted_at,
                    Message.changed_at
                )
                .where(Message.chat_id == chat_id)
                .order_by(Message.created_at.asc())
            )
            history = [dict(row._mapping) for row in result.fetchall()]
            logger.info(f"Загружено {len(history)} сообщений для чата ID {chat_id}")
            return history
    except Exception as e:
        logger.error(f"Ошибка при получении сообщений: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при загрузке сообщений из базы данных")


async def delete_chat(chat_id: int, user_id: int):
    """
    Помечает чат как удалённый:
    - is_deleted = True
    - deleted_at = текущее время
    """
    try:
        async with db_manager.get_db_session() as session:
            stmt = (
                update(Chats)
                .where(
                    (Chats.chat_id == chat_id) &
                    (Chats.user_id == user_id) &
                    (Chats.is_deleted.is_(False))
                )
                .values(
                    is_deleted=True,
                    deleted_at=datetime.utcnow()
                )
            )
            result = await session.execute(stmt)
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Чат не найден или уже удалён")
            await session.commit()
            logger.info(f"Чат ID {chat_id} пользователя {user_id} помечен как удалённый")
            return {"chat_id": chat_id, "deleted_at": datetime.utcnow(), "is_deleted": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при удалении чата: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при удалении чата")

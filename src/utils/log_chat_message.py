from datetime import datetime
from fastapi import HTTPException
from src.models.user_models import Message
from src.logger import get_logger
from src.session import db_manager

logger = get_logger("s3_upload")

async def insert_message_to_db(
        chat_id: int,
        user_id: int,
        role: str,
        message: str | None = None,
        message_html_code: str | None = None,
        message_tables: dict | None = None,
        message_links: dict | None = None,
        data_path: str | None = None,
        connection_id: int | None = None,
        table_name: str | None = None,
        call_agent: str | None = None,
        agent_form: dict | None = None,
        deleted_at: datetime | None = None,
        changed_at: datetime | None = None
):
    try:
        logger.info(f"Начало вставки сообщения для пользователя ID {user_id} в чат ID {chat_id}")
        async with db_manager.get_db_session() as session:
            new_message = Message(
                chat_id=chat_id,
                user_id=user_id,
                role=role,
                message=message,
                message_html_code=message_html_code,
                message_tables=message_tables,
                message_links=message_links,
                data_path=data_path,
                connection_id=connection_id,
                table_name=table_name,
                call_agent=call_agent,
                agent_form=agent_form,
                created_at=datetime.utcnow(),
                deleted_at=deleted_at,
                changed_at=changed_at
            )
            session.add(new_message)
            await session.commit()
            await session.refresh(new_message)
            logger.info(f"Сообщение успешно добавлено в таблицу messages (ID {new_message.id})")
            return new_message
    except Exception as e:
        logger.error(f"Ошибка при вставке сообщения в базу: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при добавлении сообщения в базу данных")

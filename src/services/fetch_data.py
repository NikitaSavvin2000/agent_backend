import json
import os
import uuid
import logging
from datetime import datetime
from typing import Annotated, Optional, Any, Dict, List

import pandas as pd
import uvicorn
from dotenv import load_dotenv
from fastapi import (
    APIRouter, FastAPI, HTTPException, Depends, Body, Path, Query, Form, File, UploadFile
)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine

from src.config import public_or_local
from src.core.security.password import decrypt_password
from src.core.token import jwt_token_validator
from src.session import db_manager
from src.utils.log_chat_massage import insert_message_to_db
from src.utils.s3_loader import upload_to_s3, load_from_s3
from src.utils.chats import get_history_by_chat_id, create_new_chat, get_user_chats, delete_chat
from src.models.organization_models import ConnectionSettings
from src.mock_data.mock_html import generate_mock_timeseries_html




async def fetch_postgres_sample_data(
        username: str,
        password: str,
        host: str,
        port: int,
        db_name: str,
        table_name: str,
        limit: int = 1000000000000
) -> List[Dict]:
    db_url = f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{db_name}"
    engine = create_async_engine(db_url)
    sample_data: List[Dict] = []

    try:
        async with engine.connect() as conn:
            query = text(
                f'SELECT *'
                f'FROM "{table_name}" '
                f'LIMIT {limit}'
            )
            result = await conn.execute(query)
            rows = result.fetchall()
            if not rows:
                raise HTTPException(status_code=404, detail="В таблице нет данных")

            columns = result.keys()
            for row in rows:
                sample_data.append(dict(zip(columns, row)))
    except Exception as e:
        logger.error(f"Ошибка при выборке данных из PostgreSQL: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Не удалось получить данные из таблицы")
    finally:
        await engine.dispose()

    return sample_data





async def fetch_sample_data_and_discreteness(connection_id, source_table, organization_id) :

    async with db_manager.get_db_session() as session:
        stmt = select(ConnectionSettings).where(
            ConnectionSettings.id == connection_id,
            ConnectionSettings.organization_id == organization_id,
            ConnectionSettings.is_deleted.is_not(True)
        )
        result = await session.execute(stmt)
        connection = result.scalar_one_or_none()

        if not connection:
            raise HTTPException(status_code=404, detail="Соединение не найдено или не принадлежит организации")

        if connection.connection_schema.lower() != "postgresql":
            raise HTTPException(status_code=400, detail=f"Схема {connection.connection_schema} пока не поддерживается")

        try:
            password = decrypt_password(connection.db_password)
            sample_data = await fetch_postgres_sample_data(
                username=connection.db_user,
                password=password,
                host=connection.host,
                port=connection.port,
                db_name=connection.db_name,
                table_name=source_table,
            )

            if not sample_data:
                raise HTTPException(status_code=404, detail="В таблице нет данных ")

            df = pd.DataFrame(sample_data)
            return df

        except Exception as e:
            logger.error(f"Ошибка при получении данных: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Не удалось получить данные")



async def fetch_example_data(connection_id, source_table, organization_id):
    df = await fetch_sample_data_and_discreteness(connection_id, source_table, organization_id)
    return df

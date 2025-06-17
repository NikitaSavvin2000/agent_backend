import io
import json
import logging
import os
from typing import Annotated, Optional
from uuid import uuid4

import pandas as pd
import uvicorn
from fastapi import Body, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from src.agents.coordinator import Coordinator
from src.config import public_or_local


logger = logging.getLogger(__name__)

if public_or_local == 'LOCAL':
    url = 'http://localhost'
else:
    url = 'http://11.11.11.11'

origins = [
    url
]
docs_url = "/horizon_chat"
app = FastAPI(docs_url=docs_url, openapi_url=f'{docs_url}/openapi.json')
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


cwd = os.getcwd()
chat_histories = os.path.join(cwd, "src", "chat_histories")
@app.post(
    "/chat",
    summary="Обработка запроса пользователя по загруженным данным",
    description="""
    Принимает session_id и сообщение пользователя.
    Если это первый запрос — создаёт директорию chat_histories/{session_id}/chats/{chat_id}.
    """
)
async def chat(
        session_id: Annotated[str, Form(..., description="ID сессии пользователя")],
        message: Annotated[str, Form(..., description="Текст запроса пользователя")],
        chat_id: Optional[str] = Form(None, description="Опционально"),
        file: Optional[UploadFile] = File(None, description="Опционально: файл CSV/XLSX")
):
    base_dir = os.path.join(chat_histories, session_id, "chats")
    os.makedirs(base_dir, exist_ok=True)


    if not chat_id:
        chat_id = str(uuid4())

    full_path = os.path.join(base_dir, chat_id)
    os.makedirs(full_path, exist_ok=True)
    log_path = os.path.join(full_path, "log.json")


    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            history = json.load(f)
    else:
        history = []

    history.append({"role": "user", "message": message})
    with open(log_path, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    path_to_save = None
    if file:
        filename = file.filename or "uploaded_file"
        content = await file.read()
        ext = os.path.splitext(filename)[1].lower()
        file_io = io.BytesIO(content)

        if ext == ".csv":
            df = pd.read_csv(file_io)
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(file_io)
        else:
            df = None

        path_to_save = os.path.join(full_path, filename)
        if df is not None:
            df.to_csv(path_to_save, index=False)

    coordinator = Coordinator()
    result = await coordinator.run(message=message, file=path_to_save)

    with open(log_path, "r") as f:
        history = json.load(f)
    history.append({"role": "assistant", "message": result, "chart_html": None})
    with open(log_path, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    return {
        "response": {
            "session_id": session_id,
            "chat_id": chat_id,
            "message": result,
            "chart_html": None
        }
    }


@app.get("/")
def read_root():
    return {"message": "Welcome to the indicators System API"}


if __name__ == "__main__":
    port = 7070
    print(f'🚀 Документация http://0.0.0.0:{port}{docs_url}')
    uvicorn.run("server:app", host="0.0.0.0", port=port, workers=2, log_level="debug")

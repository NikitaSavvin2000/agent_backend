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
from src.models.schemes import ChatRequest, ChatDataRequest

from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

cwd = os.getcwd()
path_to_mock = os.path.join(cwd, "src", "mock_data", "morocco zone 2 - powerconsumption_resampled.csv")

load_dotenv()
mock_mode = os.getenv("MOCK_MODE")



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

df_example = pd.read_csv(path_to_mock)

col_time = "Datetime"
col_target = "consumption"

json_data = df_example.to_dict(orient="records")

import plotly.express as px

fig = px.line(df_example, x=col_time, y=col_target, title="Визуализация временного ряда")
html_output = fig.to_html()

mock_result = {}
mock_result["data"] = json_data
mock_result["html"] = html_output
mock_result["message"] = 'Отрисовали моковый график'



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
@app.post("/chat")
async def chat(req: Annotated[ChatRequest, Body(
    example={
        "session_id": "abc123",
        "message": "Проанализируй данные",
        "chat_id": "chat456",
        "filename": "example",
        "data_json": [
            {"col1": 1, "col2": "a"},
            {"col1": 2, "col2": "b"}
        ]
    }
)]):

    logger.info(f'Received a request from session_id - {req.session_id} chat - {req.chat_id}')

    if req.filename:
        filename = req.filename + '.csv'

    base_dir = os.path.join(chat_histories, req.session_id, "chats")
    os.makedirs(base_dir, exist_ok=True)

    chat_id = req.chat_id or str(uuid4())
    full_path = os.path.join(base_dir, chat_id)
    os.makedirs(full_path, exist_ok=True)

    log_path = os.path.join(full_path, "log.json")
    data_path_json = os.path.join(full_path, "data_path.json")
    print(f'data_path_json = {data_path_json}')

    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            history = json.load(f)
    else:
        history = []

    history.append({"role": "user", "message": req.message})
    with open(log_path, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    if req.data_json and filename:
        if os.path.exists(data_path_json) and os.path.getsize(data_path_json) > 0:
            with open(data_path_json, "r") as f:
                data_index = json.load(f)
        else:
            data_index = {}

        if req.filename in data_index:
            return {
                "response": {
                    "session_id": req.session_id,
                    "chat_id": chat_id,
                    "message": f"Файл с именем '{req.filename}' уже существует, данные не записаны",
                    "data": None,
                    "chart_html": None
                }
            }

        df = pd.DataFrame(req.data_json)
        path_to_save = os.path.join(full_path, filename)
        df.to_csv(path_to_save, index=False)

        data_index[req.filename] = os.path.abspath(path_to_save)
        with open(data_path_json, "w") as f:
            json.dump(data_index, f, ensure_ascii=False, indent=2)

        json_data = df.to_dict(orient="records")

        if req.message is None:
            return {
                "response": {
                    "session_id": req.session_id,
                    "chat_id": chat_id,
                    "message": f'Данные успешно загружены. Название файла - "{filename}"',
                    "data": json_data,
                    "chart_html": None
                }
            }



    coordinator = Coordinator()
    if mock_mode == 'True':
        result = mock_result
    else:
        result = await coordinator.run(message=req.message, path_to_storage_files=data_path_json)
    data = result["data"]
    chart_html = result["html"]
    message = result["message"]

    with open(log_path, "r") as f:
        history = json.load(f)
    history.append({"role": "assistant", "message": result, "chart_html": None})
    with open(log_path, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    response = {
            "response": {
                "session_id": req.session_id,
                "chat_id": chat_id,
                "message": message,
                "data": data,
                "chart_html": chart_html
            }
        }

    return response


@app.post("/chat_data")
async def chat(req: Annotated[ChatDataRequest, Body(
    example={
        "session_id": "1234",
        "chat_id": "2345",
    }
)]):

    chat_dir = os.path.join(chat_histories, req.session_id, "chats", req.chat_id)
    json_path = os.path.join(chat_dir, "data_path.json")

    if not os.path.exists(chat_dir) or not os.path.exists(json_path):
        response = {
            "response": {
                "data_exist": False,
                "massage": 'Нет загруженных данных',
                "data": [],

            }
        }
    else:
        with open(json_path, "r", encoding="utf-8") as f:
            data_dict = json.load(f)

            data = []
            for name, path in data_dict.items():
                description = {}
                description["name"] = name
                df = pd.read_csv(path)
                df = df.loc[:10]
                json_data = json.loads(
                    json.dumps(df.to_dict(orient="records"), ensure_ascii=False)
                )
                description["json_data"] = json_data
                data.append(description)

        response = {
            "response": {
                "data_exist": True,
                "massage": '',
                "data": data,

            }
        }

    return response



@app.get("/")
def read_root():
    return {"message": "Welcome to the indicators System API"}


if __name__ == "__main__":
    port = 7070
    print(f'🚀 Документация http://0.0.0.0:{port}{docs_url}')
    uvicorn.run("server:app", host="0.0.0.0", port=port, workers=2, log_level="debug")

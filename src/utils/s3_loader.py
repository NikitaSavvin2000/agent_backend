import os
import io
import uuid
import boto3
import pandas as pd
from botocore.client import Config
from fastapi import UploadFile, HTTPException
from src.logger import get_logger

logger = get_logger("s3_upload")

S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_BUCKET = os.getenv("S3_BUCKET")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    config=Config(signature_version="s3v4"),
)

async def upload_to_s3(file: UploadFile, folder: str = "uploads") -> str:
    try:
        filename = file.filename
        ext = os.path.splitext(filename)[1].lower()
        s3_key = f"{folder}/{filename}"

        logger.info(f"Начало загрузки файла '{filename}' в S3")
        content = await file.read()
        s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=content)
        logger.info(f"Файл успешно загружен в S3: {s3_key}")
        return s3_key

    except Exception as e:
        logger.error(f"Ошибка при загрузке файла в S3: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при загрузке файла в S3")



async def load_from_s3(file_key: str) -> pd.DataFrame:
    try:
        logger.info(f"Начало загрузки файла из S3: {file_key}")
        obj = s3.get_object(Bucket=S3_BUCKET, Key=file_key)
        body = obj["Body"].read()

        ext = os.path.splitext(file_key)[1].lower()
        if ext == ".csv":
            df = pd.read_csv(io.BytesIO(body))
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(io.BytesIO(body))
        else:
            raise ValueError("Неподдерживаемый формат файла")

        logger.info(f"Файл успешно загружен из S3: {file_key}")
        return df

    except Exception as e:
        logger.error(f"Ошибка при загрузке файла из S3: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при загрузке файла из S3")
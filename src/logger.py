import os
import pytz
import logging
from datetime import datetime

os.makedirs("logs", exist_ok=True)

class MoscowFormatter(logging.Formatter):
    def converter(self, timestamp):
        tz = pytz.timezone("Europe/Moscow")
        return datetime.fromtimestamp(timestamp, tz)
    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

def get_logger(name: str = "app_logger"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        file_handler = logging.FileHandler("logs/s3_upload.log", encoding="utf-8")
        formatter = MoscowFormatter("[%(asctime)s] %(levelname)s: %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.setLevel(logging.INFO)
    return logger

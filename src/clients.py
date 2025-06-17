import httpx
from openai import OpenAI
from dotenv import load_dotenv
import os
from src.config import public_or_local

load_dotenv()

api_key = os.getenv('API_KEY')
proxy = os.getenv('PROXY')

http_client = httpx.Client(proxy=proxy) if public_or_local == "LOCAL" else None

def get_open_ai_client():
    open_ai_client = OpenAI(
        api_key=api_key,
        http_client=http_client
    )
    return open_ai_client
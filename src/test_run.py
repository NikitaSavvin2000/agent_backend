import requests
import pandas as pd
import io
import os

def send_chat_df_file(session_id: str, message: str, df: pd.DataFrame, original_filename: str, chat_id: str = None):
    url = "https://nikitasavvin2000-agent-backend-cae7.twc1.net/chat"
    data = {
        "session_id": session_id,
        "message": message,
    }
    if chat_id:
        data["chat_id"] = chat_id

    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    filename = os.path.basename(original_filename)

    files = {
        "file": (filename, buffer, "text/csv")
    }

    response = requests.post(url, data=data, files=files)
    return response.json()

df_path = "/Users/nikitasavvin/Downloads/Прошлые данные - TSLA.csv"
df = pd.read_csv(df_path)
response = send_chat_df_file(session_id="123", message="Проанализируй данные", df=df, original_filename=df_path)
print(response)

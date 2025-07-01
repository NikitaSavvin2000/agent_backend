import os
import requests
from dotenv import load_dotenv

load_dotenv()

class ForecastAgent:
    async def handle(self, df, time_col, target_col, horizon_time):
        url = os.getenv("FORECAST_API")
        df[time_col] = df[time_col].astype(str)
        payload = {
            "df": df.to_dict(orient="records"),
            "time_column": time_col,
            "col_target": target_col,
            "forecast_horizon_time": horizon_time
        }
        response = requests.post(url, json=payload)
        return response.json()

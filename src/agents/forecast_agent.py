import requests


class ForecastAgent:
    async def handle(self, df, time_col, target_col, horizon_time):
        url = "http://localhost:7071/backend/v1/generate_forecast"
        df[time_col] = df[time_col].astype(str)
        payload = {
            "df": df.to_dict(orient="records"),
            "time_column": time_col,
            "col_target": target_col,
            "forecast_horizon_time": horizon_time
        }
        response = requests.post(url, json=payload)
        return response.json()

from .intent_agent import IntentAgent
from .upload_agent import UploadAgent
from .parser_agent import PayloadAgent, RecognitionTimeColAgent
from .forecast_agent import ForecastAgent
from .viz_agent import VizAgent
from .plot_agent import PlotAgent, OptionalPlotAgent
from .horizon_agent import HorizonAgent
import json
import pandas as pd
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def describe_df(df):
    cols = [
        f"{col} ({df[col].dtype}, example value: {df[col].dropna().iloc[0] if not df[col].dropna().empty else 'None'})"
        for col in df.columns
    ]
    return f"DataFrame with {len(df)} rows and columns: {', '.join(cols)}"


def get_last_date(df, col_time):
    series = df[col_time].dropna()
    if series.empty:
        return ""
    try:
        dt_series = pd.to_datetime(series, errors='coerce').dropna()
        if not dt_series.empty:
            return dt_series.max().strftime("%Y-%m-%d %H:%M:%S")
        return max(series)
    except Exception:
        return max(series)


class Coordinator:
    def __init__(self):
        self.intent = IntentAgent()
        self.upload = UploadAgent()
        self.payload_agent = PayloadAgent()
        self.recognition_time_col = RecognitionTimeColAgent()
        self.forecast = ForecastAgent()
        self.viz = VizAgent()
        self.plot = PlotAgent()
        self.optional_plot = OptionalPlotAgent()
        self.horizon = HorizonAgent()


    async def run(self, message, path_to_storage_files=None):
        if path_to_storage_files:
            if not os.path.exists(path_to_storage_files):
                with open(path_to_storage_files, "w", encoding="utf-8") as f:
                    json.dump({}, f, ensure_ascii=False, indent=2)
            with open(path_to_storage_files, "r", encoding="utf-8") as f:
                data_storage_dict = json.load(f)

        data_names = data_storage_dict.keys()
        intent = await self.intent.handle(message, data_names)

        conclusion = intent["intent"]
        logger.info(f'>>> Intent - {conclusion}')
        used_data = intent["used_data"]

        if conclusion == "forecast" and used_data:
            print(f'data_storage_dict = {data_storage_dict}')
            logger.info(f'>>> Forecast conditional is working')

            df = pd.read_csv(data_storage_dict[used_data[0]])
            df_desc = describe_df(df)
            logger.info(f'>>> Recognition time col is working')

            col_time_info = await self.recognition_time_col.handle(df_desc=df_desc)
            logger.info(f'>>> Time col_time_info = {col_time_info}')

            time_col = col_time_info["col_time"]
            logger.info(f'>>> Time col = {time_col}')

            massage = col_time_info["massage"]
            if time_col:

                last_date = get_last_date(df=df, col_time=time_col)

                last_row = df[df[time_col] == last_date]

                forecast_info = await self.payload_agent.handle(message=message, df_desc=df_desc, last_date=last_date)
                logger.info(f'>>> Forecast payload {forecast_info}')

                result = await self.forecast.handle(df, time_col, forecast_info["col_target"], forecast_info["forecast_horizon_time"])
                df_forecast = pd.DataFrame(result["map_data"]["data"]["predictions"])
                df_forecast = pd.concat([last_row, df_forecast]).reset_index(drop=True)
                html_output, json_data = await self.viz.handle(df, df_forecast, time_col, forecast_info["col_target"])
                response = {
                    "message": "Ваш прогноз",
                    "code": None,
                    "data": json_data,
                    "html": html_output
                }
                return response
            else:
                json_data = json.loads(
                    json.dumps(df.to_dict(orient="records"), ensure_ascii=False)
                )
                response = {
                    "message": massage,
                    "code": None,
                    "data": json_data,
                    "html": None
                }
                return response

        elif (conclusion == "visualization" or conclusion == "possible_visualization") and used_data:
            logger.info(f'>>> Visualization conditional is working')

            full_describe_data = []
            for name in used_data:
                df = pd.read_csv(data_storage_dict[used_data[0]])
                df_desc = describe_df(df)
                describe_data = {
                    "name": name,
                    "path_to_data_csv": data_storage_dict[name],
                    "description_df": df_desc
                }
                full_describe_data.append(describe_data)
            code = await self.plot.handle(message, full_describe_data)
            local_vars = {}
            exec(code, {}, local_vars)
            html_output = local_vars.get("html_output")
            response = {
                "message": None,
                "code": None,
                "data": None,
                "html": html_output
            }
            return response
        else:
            logger.info(f'>>> Horizon conditional is working')

            response = {
                "message": await self.horizon.handle(message),
                "code": None,
                "data": None,
                "html": None
            }
            return response

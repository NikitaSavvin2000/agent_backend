from .intent_agent import IntentAgent
from .upload_agent import UploadAgent
from .parser_agent import ParserAgent
from .forecast_agent import ForecastAgent
from .viz_agent import VizAgent
from .plot_agent import PlotAgent, OptionalPlotAgent
from .horizon_agent import HorizonAgent
import json
import pandas as pd
import os

def describe_df(df):
    cols = [
        f"{col} ({df[col].dtype}, example value: {df[col].dropna().iloc[0] if not df[col].dropna().empty else 'None'})"
        for col in df.columns
    ]
    return f"DataFrame with {len(df)} rows and columns: {', '.join(cols)}"


class Coordinator:
    def __init__(self):
        self.intent = IntentAgent()
        self.upload = UploadAgent()
        self.parser = ParserAgent()
        self.forecast = ForecastAgent()
        self.viz = VizAgent()
        self.plot = PlotAgent()
        self.optional_plot = OptionalPlotAgent()
        self.horizon = HorizonAgent()


    async def run(self, message, path_to_storage_files=None):
        df, time_col, last_date = None, None, None
        if path_to_storage_files:
            if not os.path.exists(path_to_storage_files):
                with open(path_to_storage_files, "w", encoding="utf-8") as f:
                    json.dump({}, f, ensure_ascii=False, indent=2)
            with open(path_to_storage_files, "r", encoding="utf-8") as f:
                data_storage_dict = json.load(f)

        data_names = data_storage_dict.keys()
        intent = await self.intent.handle(message, data_names)

        conclusion = intent["intent"]
        used_data = intent["used_data"]

        if conclusion == "forecast" and used_data:
            print(f'data_storage_dict = {data_storage_dict}')
            df = pd.read_csv(data_storage_dict[used_data[0]])
            forecast_info = await self.parser.handle(message, df.columns.tolist(), last_date)
            result = await self.forecast.handle(df, time_col, forecast_info["target_col"], forecast_info["horizon_time"])
            html_output, json_data = await self.viz.handle(df, result, time_col, forecast_info["target_col"])
            response = {
                "message": None,
                "code": None,
                "data": json_data,
                "html": html_output
            }
            return response

        elif (conclusion == "visualization" or conclusion == "possible_visualization") and used_data:
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
            response = {
                "message": await self.horizon.handle(message),
                "code": None,
                "data": None,
                "html": None
            }
            return response

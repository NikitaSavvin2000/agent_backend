from .intent_agent import IntentAgent
from .upload_agent import UploadAgent
from .parser_agent import ParserAgent
from .forecast_agent import ForecastAgent
from .viz_agent import VizAgent
from .plot_agent import PlotAgent, OptionalPlotAgent
from .horizon_agent import HorizonAgent



def describe_df(df):
    cols = [f"{col} ({df[col].dtype})" for col in df.columns]
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


    async def run(self, message, file=None):
        df, time_col, last_date = None, None, None
        if file:
            df, time_col, last_date = await self.upload.handle(file)

        conclusion = await self.intent.handle(message)

        if conclusion == "forecast" and df is not None:
            forecast_info = await self.parser.handle(message, df.columns.tolist(), last_date)
            result = await self.forecast.handle(df, time_col, forecast_info["target_col"], forecast_info["horizon_time"])
            return await self.viz.handle(df, result, time_col, forecast_info["target_col"])

        elif (conclusion == "visualization" or conclusion == "possible_visualization") and df is not None:
            df_desc = describe_df(df)
            code = await self.plot.handle(message, df_desc)
            return code

        else:
            return await self.horizon.handle(message)

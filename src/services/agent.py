import json
from typing import Annotated, Optional, Any, Dict, List
from src.agents.intent_agent import get_agent_tools
import pandas as pd
from src.utils.s3_loader import upload_to_s3, load_from_s3, upload_df_to_s3

from src.services.fetch_data import fetch_example_data
from src.utils.describe_df import describe_df_for_llm_verbose
from src.agents.plot_agent import agent_plot_generation
from src.agents.agent_answer import fill_empty_agent_answer, simple_agent_answer
from src.agents.analysis_agent import analytics_agent
from src.agents.forecast_agent import forecast_request, summary_for_forecast


sep_system_file_name_key = "_1s2e3p4_"


async def pre_fill_forecast_form(df):
    forecast_agent_form = {}
    return forecast_agent_form


async def agent_answer(
        message: str,
        organization_id: int,
        connection_id: Optional[int] = None,
        table_name: Optional[str] = None,
        s3_key: Optional[str] = None,
        call_agent: Optional[str] = None,
        agent_form_str: Optional[str] = None,
        message_context: Optional[str] = None,
        user_means_context: bool = False
):

    agent_message = None
    message_html_code = None
    message_tables = []
    message_links = []
    agent_data_s3_key = None
    call_agent = None
    agent_form = None
    df_result = None
    s3_key_answer = None

    list_to_call_services = get_agent_tools(user_query=message, message_context=message_context, user_means_context=user_means_context)

    for service in list_to_call_services:
        print(service)

    if connection_id and table_name and s3_key is None:
        df = await fetch_example_data(connection_id=connection_id, source_table=table_name, organization_id=organization_id)
        describe_df = describe_df_for_llm_verbose(df=df)
    elif s3_key:
        df = await load_from_s3(file_key=s3_key)
        describe_df = describe_df_for_llm_verbose(df=df)
        print(describe_df)
    else:
        df = None
        describe_df = None

    if call_agent == "forecast":
        pass

    if "visualization" in list_to_call_services and df is not None:
        message_html_code, df_result = await agent_plot_generation(user_task=message, full_describe_data=describe_df, df=df)
        agent_message = "Готова твоя визуализация по запросу"

    if "analysis" in list_to_call_services and df is not None:
        message_html_code, result_analysis, df_result = await analytics_agent(user_task=message, full_describe_data=describe_df, df=df)
        agent_message = result_analysis

    if "none" in list_to_call_services and df is not None:
        agent_message = await simple_agent_answer(user_task=message)

    if "forecast" in list_to_call_services and df is not None:

        result = await forecast_request(df=df, user_task=message, description_df=describe_df)

        meta_info = result.get("meta_info")
        message_html_code = result.get("html_chart")
        predict_table = result.get("predict_table")
        df_result = pd.DataFrame(predict_table)
        agent_message = await summary_for_forecast(user_task=message, meta_info=meta_info)

    if df_result is not None:
        df_result = df_result.astype(str)
        message_tables.append(json.loads(df_result.to_json(orient='records', force_ascii=False)))
        s3_key_answer = await upload_df_to_s3(df=df_result)

    if agent_message is None:
        describe_df_result_df = describe_df_for_llm_verbose(df=df_result)
        agent_message = await fill_empty_agent_answer(user_task=message, describe_df=describe_df_result_df)

    agent_data_s3_key = s3_key

    return {
            "agent_message": agent_message,
            "message_html_code": message_html_code,
            "message_tables": message_tables,
            "message_links": message_links,
            "agent_data_s3_key": agent_data_s3_key,
            "call_agent": call_agent,
            "agent_form": agent_form,
            "s3_key_answer": s3_key_answer
        }
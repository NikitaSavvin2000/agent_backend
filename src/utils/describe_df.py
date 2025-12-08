# # src/utils/describe_df.py
# from typing import Optional, List

# import pandas as pd

# from src.logger import get_logger

# logger = get_logger("describe_df")


# def _safe_dt_infer(series: pd.Series) -> pd.Series:
#     """
#     Аккуратное приведение к datetime: если не получилось — просто возвращаем исходное.
#     """
#     try:
#         converted = pd.to_datetime(series.dropna(), errors="coerce")
#         # если почти всё превратилось в NaT, значит это не дата — не трогаем
#         if converted.notna().sum() == 0:
#             return series
#         return converted.reindex(series.index)
#     except Exception as e:
#         logger.warning(f"Не удалось привести колонку к datetime: {e}")
#         return series


# def describe_df_for_llm_verbose(df: Optional[pd.DataFrame]) -> str:
#     """
#     Генерирует текстовое описание DataFrame для LLM.

#     Безопасно обрабатывает случаи df is None, не DataFrame и пустой df.
#     """
#     if df is None:
#         logger.warning("describe_df_for_llm_verbose получил df=None")
#         return (
#             "Модель не вернула дополнительную таблицу (df_result). "
#             "Доступен только основной текстовый анализ."
#         )

#     if not isinstance(df, pd.DataFrame):
#         logger.warning(f"Ожидался pandas.DataFrame, получено {type(df)}")
#         return (
#             "Вместо таблицы был получен объект другого типа. "
#             "Используйте только текстовый анализ."
#         )

#     if df.empty:
#         logger.warning("describe_df_for_llm_verbose получил пустой DataFrame")
#         return (
#             "Получена пустая таблица без строк. "
#             "Дополнительный количественный анализ невозможен."
#         )

#     # --- Базовое описание структуры ---
#     description: List[str] = [
#         f"У нас есть DataFrame с {len(df)} строк(ой) и {len(df.columns)} колонками."
#     ]

#     # Попробуем аккуратно привести очевидные временные колонки
#     df_copy = df.copy()
#     for col in df_copy.columns:
#         if "date" in col.lower() or "time" in col.lower():
#             df_copy[col] = _safe_dt_infer(df_copy[col])

#     # --- Типы колонок и пример значений ---
#     description.append("Колонки и их базовые характеристики:")

#     for col in df_copy.columns:
#         series = df_copy[col]
#         dtype = str(series.dtype)
#         non_null_count = series.notna().sum()
#         null_count = series.isna().sum()

#         example_values = series.dropna().unique()[:5]
#         example_values_list = ", ".join(map(str, example_values))

#         description.append(
#             f"- Колонка '{col}': тип {dtype}, "
#             f"ненулевых значений {non_null_count}, пропусков {null_count}. "
#             f"Примеры значений: {example_values_list}"
#         )

#     # --- Простая статистика по числовым колонкам ---
#     numeric_cols = df_copy.select_dtypes(include=["number"]).columns.tolist()
#     if numeric_cols:
#         description.append(
#             "Для числовых колонок приведены основные статистики (минимум, максимум, среднее):"
#         )
#         desc = df_copy[numeric_cols].describe().T
#         for col in numeric_cols:
#             row = desc.loc[col]
#             col_min = row.get("min", None)
#             col_max = row.get("max", None)
#             col_mean = row.get("mean", None)
#             description.append(
#                 f"- '{col}': min={col_min}, max={col_max}, mean={col_mean}"
#             )
#     else:
#         description.append(
#             "В таблице нет числовых колонок, статистические показатели не рассчитываются."
#         )

#     return "\n".join(description)
import pandas as pd

def is_datetime_column(series):
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    try:
        converted = pd.to_datetime(series.dropna(), errors='coerce')
        return converted.notnull().sum() > 0
    except:
        return False

def describe_df_for_llm_verbose(df, n_examples=3):
    description = [f"У нас есть DataFrame с {len(df)} строк(ой) и {len(df.columns)} колонками."]

    for col in df.columns:
        dtype = df[col].dtype
        non_null_count = df[col].notnull().sum()
        null_count = df[col].isnull().sum()
        unique_count = df[col].nunique()
        examples = df[col].dropna().unique()[:n_examples].tolist()
        col_desc = f"Колонка '{col}' имеет тип {dtype}, {non_null_count} значений заполнено, {null_count} пропущено, {unique_count} уникальных значений."
        col_desc += f" Примеры значений: {examples}."

        if pd.api.types.is_numeric_dtype(df[col]):
            col_desc += f" Статистика: min={df[col].min()}, max={df[col].max()}, среднее={df[col].mean():.2f}, стандартное отклонение={df[col].std():.2f}."
        elif is_datetime_column(df[col]):
            dates = pd.to_datetime(df[col], errors='coerce')
            col_desc += f" Диапазон дат: от {dates.min()} до {dates.max()}."

        description.append(col_desc)

    description.append("Это описание можно использовать, чтобы понять данные и сформулировать запросы к ним.")
    return "\n".join(description)


# def describe_df_for_llm_verbose(df, n_examples=3):
#     return df.describe().to_string()
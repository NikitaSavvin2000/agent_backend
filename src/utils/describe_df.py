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


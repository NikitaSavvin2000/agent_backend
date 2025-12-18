
def describe_df_for_llm_verbose(df, n_examples=3):
    description = [f"У нас есть DataFrame с {len(df)} строк(ой) и {len(df.columns)} колонками."]

    for col in df.columns:
        dtype = df[col].dtype
        examples = df[col].dropna().unique()[:n_examples].tolist()
        col_desc = f"Колонка '{col}' имеет тип {dtype}"
        col_desc += f" Примеры значений: {examples}."

        description.append(col_desc)

    description.append("Это описание можно использовать, чтобы понять данные и сформулировать запросы к ним.")
    return "\n".join(description)

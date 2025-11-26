import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

model_to_use = os.getenv("MODEL_TO_USE")

models_api_config = {
    "deepseek": {
        "api_key": os.getenv("DEEPSEEK_API_KEY"),
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com"
    }
}

api_key = models_api_config[model_to_use]["api_key"]
model = models_api_config[model_to_use]["model"]
base_url = models_api_config[model_to_use]["base_url"]

def call_llm(messages, temperature=0.5, max_tokens=2512, top_p=1.0, frequency_penalty=0.0, presence_penalty=0.0):
    if api_key is None:
        if api_key is None:
            raise ValueError("API key не задана и не найдена в окружении")

    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty
    )

    return response

if __name__ == "__main__":
    # Пример использования
    msgs = [
        {"role": "system", "content": "Ты — полезный ассистент."},
        {"role": "user", "content": "Объясни мне, что такое рекурсия."}
    ]

    resp = call_llm(
        messages=msgs,
        temperature=0.5,
        max_tokens=300,
        top_p=0.9
    )
    print(resp.choices[0].message.content)

import os
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"

TOPICS = [
    "Функциональное тестирование",
    "Регрессионное тестирование",
    "Дымовое тестирование",
    "Интеграционное тестирование",
    "Системное тестирование",
    "Приемочное тестирование",
    "Тест-кейс",
    "Чек-лист в тестировании",
    "Баг-репорт",
    "Автоматизация тестирования",
]

os.makedirs("dataset", exist_ok=True)

for number, topic in enumerate(TOPICS, start=1):
    prompt = f"""
Напиши один учебный текст на русском языке примерно на 100 слов.
Тема: {topic}.
Текст предназначен для начинающего тестировщика.
Пиши простыми словами, без списков и без заголовка.
Не уходи от темы.
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
        },
        timeout=120,
    )
    response.raise_for_status()

    text = response.json()["response"].strip()
    filename = f"dataset/doc_{number:02}.txt"

    with open(filename, "w", encoding="utf-8") as file:
        file.write(text)

    print(f"Создан: {filename}")

print("Готово. Создано 10 документов в папке dataset.")

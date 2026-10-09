"""Анализ и оптимизация автотестов через локальную Ollama."""
import ast
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")


def ask_ollama(prompt):
    """Отправляет запрос модели и возвращает её текстовый ответ."""
    data = json.dumps({"model": MODEL, "prompt": prompt, "stream": False}).encode("utf-8")
    request = Request(
        f"{OLLAMA_URL}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=300) as response:
        result = json.load(response)
    answer = result.get("response", "").strip()
    if not answer:
        raise ValueError("Ollama вернула пустой ответ")
    return answer


def clean_response(text):
    """Удаляет Markdown-ограждение, если модель добавила его."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            return "\n".join(lines[1:-1]).strip() + "\n"
    return text + "\n"


def main():
    original = (ROOT / "source" / "test_users_original.py").read_text(encoding="utf-8")
    output = ROOT / "generated"
    output.mkdir(exist_ok=True)

    print("1/2: Генерация оптимизированных тестов...")
    code = ask_ollama(
        "Ты инженер по тестированию. Оптимизируй Python pytest тесты ниже по лучшим практикам написания автотестов "
        "Сохрани все 5 исходных наборов данных и все проверки. "
        "Не придумывай поведение API и дополнительные проверки. "
        "Верни только исполняемый Python-код без пояснений и Markdown.\n\n" + original
    )
    code = clean_response(code)
    ast.parse(code)  # Не сохраняем результат с ошибкой синтаксиса.
    (output / "test_users_generated.py").write_text(code, encoding="utf-8")

    print("2/2: Генерация отчёта...")
    review = ask_ollama(
        "Проведи ревью ИСХОДНЫХ pytest тестов. Напиши по-русски отчёт Markdown "
        "с разделами: 'Сильные стороны', 'Слабые стороны', "
        "'Оптимизация', 'Приоритеты', 'Ограничения'. "
        "Приоритеты предложи и объясни, не выдавай их за измеренные данные. "
        "Не утверждай, что тесты выполнялись. Не придумывай контракт API. "
        "Верни только текст Markdown.\n\nИсходный код:\n" + original +
        "\n\nОптимизированный код:\n" + code
    )
    review = clean_response(review)
    (output / "review_generated.md").write_text(review + "\n", encoding="utf-8")
    print("Готово: generated/test_users_generated.py и generated/review_generated.md")
    print("Проверь результат модели вручную перед сдачей.")


if __name__ == "__main__":
    try:
        main()
    except (HTTPError, URLError, TimeoutError, ValueError, SyntaxError, KeyError, OSError) as error:
        raise SystemExit(f"Ошибка: {error}. Проверь Ollama, модель и ответ модели.")

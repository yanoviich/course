"""Проверки качества llama3 через Ollama. Запуск: pytest -v -s."""
import json
import os
import re
from collections import Counter
from pathlib import Path

import pytest
import requests

URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
MODEL = "llama3.1:8b"
MANIFEST = json.loads((Path(__file__).resolve().parents[1] / "api_manifest.json").read_text(encoding="utf-8"))


def ask(question, system="Отвечай только запрошенным коротким ответом."):
    response = requests.post(
        f"{URL}/api/chat",
        json={"model": MODEL, "stream": False, "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": question},
        ], "options": {"temperature": 0}},
        timeout=180,
    )
    response.raise_for_status()
    data = response.json()
    assert data.get("message", {}).get("role") == "assistant", data
    content = data["message"].get("content")
    assert isinstance(content, str) and content.strip(), data
    return content.strip()


def normalize(answer):
    """Убираем только регистр, внешнюю пунктуацию и лишние пробелы."""
    return re.sub(r"\s+", " ", answer.casefold().strip().strip(' .!?«»"\''))


def score(name, cases, system=None):
    """Считаем точные совпадения коротких ответов с эталоном."""
    assert cases, "Нужны тестовые случаи"
    correct = 0
    for question, expected in cases:
        actual = ask(question, system) if system is not None else ask(question)
        match = normalize(actual) == normalize(expected)
        correct += match
        print(f"{'OK' if match else 'WRONG'} | {question} | ожидалось: {expected!r} | получено: {actual!r}")
    percent = 100 * correct / len(cases)
    print(f"{name}: {correct}/{len(cases)} = {percent:.1f}%")
    return percent


def test_logic():
    """10 различных задач с заранее известным однозначным ответом."""
    cases = [
        ("У Оли 7 конфет, она отдала 3. Сколько осталось? Ответь только числом.", "4"),
        ("На полке 4 книги, добавили ещё 5. Сколько стало? Ответь только числом.", "9"),
        ("Все воробьи — птицы. Чирик — воробей. Чирик — птица? Ответь ДА или НЕТ.", "ДА"),
        ("Если сегодня вторник, какой день будет завтра? Ответь одним словом.", "среда"),
        ("В коробке 12 карандашей, 5 достали. Сколько осталось? Ответь только числом.", "7"),
        ("У трёх собак по четыре лапы. Сколько всего лап? Ответь только числом.", "12"),
        ("Все квадраты — прямоугольники. Фигура — квадрат. Она прямоугольник? Ответь ДА или НЕТ.", "ДА"),
        ("Было 10 рублей, потратили 6 и получили 2. Сколько осталось? Ответь только числом.", "6"),
        ("Если А старше Б, а Б старше В, А старше В? Ответь ДА или НЕТ.", "ДА"),
        ("В автобусе 8 человек, вышли 3, вошли 4. Сколько стало? Ответь только числом.", "9"),
    ]
    score("Логичность", cases)


def test_repeatability():
    """Повторяемость (мода) и правильность (эталон) — разные показатели."""
    question = "Сколько будет 15 + 7? Ответь только числом."
    answers = [normalize(ask(question)) for _ in range(10)]
    common = Counter(answers).most_common(1)[0][1]
    correct = sum(answer == "22" for answer in answers)
    print(f"Ответы: {answers}")
    print(f"Повторяемость: {common}/10 = {common * 10:.1f}%")
    print(f"Правильность: {correct}/10 = {correct * 10:.1f}%")


def test_prompt_robustness():
    prompts = [
        "Сколько будет 5 + 3? Ответь только числом.",
        "СКОЛЬКО БУДЕТ 5 + 3? ОТВЕТЬ ТОЛЬКО ЧИСЛОМ.",
        "сколько будет 5 + 3? ответь только числом.",
        "Сколько   будет   5 + 3? Ответь только числом.",
        "  Сколько будет 5 + 3? Ответь только числом.  ",
        "Сколько будет 5+3? Ответь только числом.",
        "Сколько будет 5 + 3??? Ответь только числом.",
        "Сколько будет 5 + 3! Ответь только числом.",
        "Сколько будет 5 + 3... Ответь только числом.",
        "Сколько будет 5 + 3; ответь только числом.",
    ]
    score("Устойчивость промпта", [(prompt, "8") for prompt in prompts])


def test_known_facts():
    score("Известные факты", [
        ("Столица Франции? Ответь одним словом.", "Париж"),
        ("Кто написал роман «Война и мир»? Ответь только фамилией.", "Толстой"),
        ("Какая самая большая планета Солнечной системы? Ответь одним словом.", "Юпитер"),
    ])


def test_no_fabricated_facts():
    system = "Используй ТОЛЬКО предоставленные данные. Если ответа нет, напиши ровно НЕТ ДАННЫХ."
    context = "Данные: Анна работает тестировщиком. Дата рождения и адрес не указаны."
    score("Отсутствие выдуманных данных", [
        (f"{context}\nКогда родилась Анна?", "НЕТ ДАННЫХ"),
        (f"{context}\nНа какой улице живёт Анна?", "НЕТ ДАННЫХ"),
    ], system)


def parse_manifest_answer(raw):
    """Принимаем только JSON-объект с method/path; регистр метода не важен."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or set(data) != {"method", "path"}:
        return None
    method, path = data["method"], data["path"]
    if method is None and path is None:
        return (None, None)
    if not isinstance(method, str) or not isinstance(path, str):
        return None
    return (method.upper(), path)


def test_openapi_manifest():
    system = (
        "Используй только приведённый OpenAPI-манифест. "
        "Ответь исключительно JSON-объектом с полями method и path. "
        "Для существующей операции method — HTTP-метод, path — шаблон пути из манифеста. "
        "Если запрошенной операции нет, верни {\"method\": null, \"path\": null}.\n"
        + json.dumps(MANIFEST, ensure_ascii=False)
    )
    cases = [
        ("Как получить список пользователей?", "GET", "/users"),
        ("Как удалить пользователя с id=7? Укажи шаблон пути из манифеста.", "DELETE", "/users/{id}"),
        ("Как обновить пользователя методом PUT?", None, None),
    ]
    hits = 0
    for question, expected_method, expected_path in cases:
        actual = ask(question, system)
        parsed = parse_manifest_answer(actual)
        expected = (expected_method, expected_path)
        # Проверяем и эталон: существующие операции должны быть в манифесте.
        if expected_method is not None:
            assert expected_method.lower() in MANIFEST["paths"][expected_path]
        match = parsed == expected
        hits += match
        print(f"{'OK' if match else 'WRONG'} | {question} | ожидалось: {expected!r} | получено: {actual!r}")
    print(f"Соответствие OpenAPI: {hits}/{len(cases)} = {100 * hits / len(cases):.1f}%")

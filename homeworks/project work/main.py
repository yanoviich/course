import ast
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1:8b"
ROOT = Path(__file__).resolve().parent


def ask_ollama(prompt, json_format=False):
    data = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": 6000
        }
    }
    if json_format:
        data["format"] = "json"

    request = Request(
        OLLAMA_URL,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=300) as response:
        result = json.load(response)

    answer = result["response"].strip()
    if not answer:
        raise ValueError("Ollama вернула пустой ответ")
    return answer


def generate_test_cases(requirements):
    prompt = f"""Ты инженер по тестированию.

На основе требований пользователя составь тест-кейсы.

Правила:
1. Используй только предоставленные требования.
2. Не придумывай отсутствующие правила работы системы.
3. Включай позитивные и негативные сценарии, если они следуют из требований.
4. Для каждого тест-кейса укажи:
   - ID
   - Название
   - Предусловия
   - Шаги
   - Ожидаемый результат
5. Если информации недостаточно, укажи, что необходимо уточнить.
6. Ответ дай на русском языке в формате Markdown.

Требования пользователя:
{requirements}
"""
    return ask_ollama(prompt)


def generate_test_data(requirements, test_cases):
    prompt = f"""Ты инженер по тестированию.

Составь входные тестовые данные для тест-кейсов ниже, опираясь на требования.

Правила:
1. Данные должны соответствовать конкретным тест-кейсам. Сохраняй ID тест-кейсов без изменений.
2. Включай данные для позитивных и негативных проверок, где они требуются.
3. Не придумывай правила валидации, ограничения или поведение, которых нет в требованиях.
4. Примеры значений можно создавать, если это следует из требований.
5. Если исходных требований недостаточно для выбора значения, укажи это в поле "needs_clarification", не выдавай предположение за требование.
6. Верни только JSON, без Markdown и объяснений, в формате:
{{"test_data": [{{"test_case_id": "ID из тест-кейса", "inputs": {{"название параметра": "значение"}}, "needs_clarification": ""}}]}}
7. Поле inputs может быть пустым объектом, если входные данные не требуются.

Требования:
{requirements}

Тест-кейсы:
{test_cases}
"""
    answer = ask_ollama(prompt, json_format=True)
    result = json.loads(answer)
    if not isinstance(result, dict) or not isinstance(result.get("test_data"), list):
        raise ValueError("Ожидался JSON-объект с массивом test_data")
    for item in result["test_data"]:
        if not isinstance(item, dict) or not isinstance(item.get("test_case_id"), str) or not isinstance(item.get("inputs"), dict):
            raise ValueError("Некорректная структура элемента test_data")
    return result



def generate_ui_tests(requirements, test_cases, test_data):
    prompt = f"""Ты инженер по автоматизации тестирования.

Напиши UI-автотесты на Python с использованием pytest и Playwright.

Правила:
1. Используй переданные требования, тест-кейсы и тестовые данные.
2. Используй синхронный Playwright и готовую фикстуру pytest-playwright: page.
3. Файл test_data.json находится рядом с файлом тестов. Читай входные данные оттуда.
4. Тестовые функции должны начинаться с test_.
5. Не придумывай URL страниц, локаторы элементов, сообщения об ошибках и ожидаемое поведение.
6. Если для конкретного UI-теста не хватает URL, локаторов или условий проверки,
   создай тест-функцию с pytest.skip("что именно требуется уточнить").
7. Проверки должны проверять ожидаемое поведение, а не просто наличие элемента.
8. Используй только стандартную библиотеку Python, pytest и Playwright.
9. Верни только исходный код Python, без Markdown, пояснений и блоков ```.

Правила генерации:

1. Используй только переданные требования, тест-кейсы и тестовые данные.

2. Используй Python, pytest и синхронный Playwright.
   Запрещено использовать async, async_playwright и asyncio.

3. Используй готовую фикстуру page из pytest-playwright.
   Не создавай собственную фикстуру page и не запускай браузер самостоятельно.

4. Структура сгенерированного файла должна быть следующей:
   - импорты;
   - функция load_test_data(file_path);
   - отдельные тестовые функции test_ для каждого тест-кейса.

5. Функция load_test_data(file_path) должна читать
   test_data.json с обязательным указанием encoding="utf-8".

6. Каждый тест должен:
   - принимать аргумент page;
   - получать соответствующие данные из test_data.json;
   - открывать нужную страницу через page.goto();
   - выполнять действия пользователя через Playwright;
   - проверять ожидаемый результат через assert.

7. Используй простые методы синхронного Playwright:
   page.goto(), page.click(), page.fill(),
   page.check(), page.locator().

8. Не используй искусственные ожидания через
   page.wait_for_timeout().

9. Не используй assert для методов,
   которые не возвращают результат проверки.

10. Не придумывай URL, локаторы, сообщения об ошибках
    и ожидаемое поведение.
    Если информации недостаточно, используй
    pytest.skip() с указанием недостающих сведений.

11. Не добавляй дополнительные классы, сложные
    вспомогательные функции и лишние библиотеки.

12. Используй одинаковую структуру для всех тестов.

13. Возвращай только Python-код без Markdown и пояснений.

Требования:
{requirements}

Тест-кейсы:
{test_cases}

Тестовые данные (test_data.json):
{json.dumps(test_data, ensure_ascii=False, indent=2)}

Все файлы с тестовыми данными сохраняются в кодировке UTF-8.

При чтении файлов обязательно явно указывай encoding="utf-8".
Это относится ко всем вызовам open(), включая вложенные вызовы.
Пример правильного чтения:
test_data = json.loads(open("test_data.json", encoding="utf-8").read())
Запрещено использовать open() без указания кодировки.
"""
    code = ask_ollama(prompt).strip()
    if code.startswith("```"):
        lines = code.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        code = "\n".join(lines).strip()

    tree = ast.parse(code, filename="test_generated.py")
    if not any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
               and node.name.startswith("test_") for node in ast.walk(tree)):
        raise ValueError("LLM не сгенерировала ни одной тестовой функции")
    return code


def main():
    input_file = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "input_requirements.md"

    if not input_file.is_file():
        print(f"Файл с требованиями не найден: {input_file}")
        return

    requirements = input_file.read_text(encoding="utf-8").strip()
    if not requirements:
        print(f"Файл с требованиями пуст: {input_file}")
        return

    print("Генерация тест-кейсов...")
    test_cases = generate_test_cases(requirements)
    output_cases = ROOT / "test_cases.md"
    output_cases.write_text(test_cases, encoding="utf-8")
    print(f"Тест-кейсы сохранены в {output_cases}")

    print("Генерация тестовых данных...")
    test_data = generate_test_data(requirements, test_cases)
    output_data = ROOT / "test_data.json"
    output_data.write_text(json.dumps(test_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Тестовые данные сохранены в {output_data}")

    print("Генерация UI-автотестов...")
    ui_tests = generate_ui_tests(requirements, test_cases, test_data)
    output_tests = ROOT / "test_generated.py"
    output_tests.write_text(ui_tests + "\n", encoding="utf-8")
    print(f"UI-автотесты сохранены в {output_tests}")


if __name__ == "__main__":
    main()
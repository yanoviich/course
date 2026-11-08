# Генерация тест-кейсов, тестовых данных и UI-автотестов

Программа принимает **любой текст требований** из `input_requirements.md` и делает три запроса к локальной `llama3.1:8b` через Ollama в Docker. Результаты сохраняются отдельно:

- `test_cases.md` — тест-кейсы;
- `test_data.json` — входные тестовые данные;
- `test_generated.py` — UI-автотесты на Playwright + pytest.

## Подготовка

Нужны Python 3, Docker, доступ к Ollama и установленная модель `llama3.1:8b`.

Если контейнера Ollama ещё нет:

```bash
docker run -d --name ollama -p 11434:11434 -v ollama:/root/.ollama ollama/ollama
```

Если контейнер уже есть, но остановлен: `docker start ollama`.

Загрузить модель один раз:

```bash
docker exec ollama ollama pull llama3.1:8b
```

Установить зависимости и браузер Playwright (из папки проекта):

```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
```

## Генерация

Заполнить `input_requirements.md` и выполнить:

```bash
python main.py
```

Можно передать путь к любому другому файлу с требованиями:

```bash
python main.py feature.md
```

Все три выходных файла создаются рядом с `main.py` и при повторной генерации перезаписываются. Если модель вернёт невалидный Python или не создаст ни одного теста, третий файл не будет сохранён.

## Запуск UI-автотестов

```bash
python -m pytest -v test_generated.py
```

import json
from pathlib import Path
from urllib.request import Request, urlopen

MODEL = 'llama3.1:8b'
URL = 'http://localhost:11434/api/generate'
ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'output'

DOCUMENTS = {
    'test_case': 'Тест-кейсы: ID, название, предусловия, шаги, ожидаемый результат и ID требования.',
    'checklist': 'Чек-лист: отдельные проверки, ожидаемый результат и ID требования.',
    'test_plan': 'Тест-план: цель, область проверки, сценарии, ограничения и ID требований.',
    'qa_report': 'QA-отчёт: анализ подготовленных проверок и охвата требований. Тесты приложения не выполнялись; не придумывай результаты и дефекты.',
}


def ask_ollama(prompt, limit):
    payload = json.dumps({
        'model': MODEL,
        'prompt': prompt,
        'stream': False,
        'options': {'temperature': 0, 'num_predict': limit},
    }).encode('utf-8')
    request = Request(URL, data=payload, headers={'Content-Type': 'application/json'})
    with urlopen(request, timeout=600) as response:
        answer = json.load(response).get('response', '').strip()
    if not answer:
        raise ValueError('Ollama вернула пустой ответ')
    return answer


def main():
    requirements = (ROOT / 'requirements' / 'login.md').read_text(encoding='utf-8')
    OUTPUT.mkdir(exist_ok=True)
    evaluation = [
        '# Оценка качества промптов',
        '',
        f'Модель: {MODEL}.',
        'Шкала: 1 — низкое качество, 2 — частичное соответствие, 3 — полное соответствие.',
        '',
    ]

    for name, task in DOCUMENTS.items():
        print(f'Обработка: {name}', flush=True)
        prompt = (
            'Ты инженер по тестированию. Напиши на русском языке документ.\n'
            f'Задача: {task}\n'
            'Опирайся только на требования ниже. Не придумывай факты. '
            'Указывай ID требований. Учитывай успешные и ошибочные сценарии, '
            'если они следуют из требований. Если данных недостаточно, отметь это.\n\n'
            f'Требования:\n{requirements}'
        )
        (OUTPUT / f'{name}.prompt.md').write_text(prompt, encoding='utf-8')
        evaluation.extend([f'## {name}', ''])
        try:
            document = ask_ollama(prompt, 3000)
            (OUTPUT / f'{name}.md').write_text(document + '\n', encoding='utf-8')
            review_prompt = (
                'Ты проверяешь качество промпта и созданного по нему документа. '
                'Оцени результат критично на русском языке.\n'
                'Используй ровно четыре критерия:\n'
                '1. Читаемость — насколько понятны промпт и документ.\n'
                '2. Контекстность — насколько документ соответствует требованиям без выдуманных фактов.\n'
                '3. Чёткость целей — насколько ясна задача и соответствует ли ей документ.\n'
                '4. Покрытие сценариев — отражены ли все требования и необходимые проверки.\n'
                'Для каждого критерия укажи оценку 1, 2 или 3 и одно конкретное обоснование. '
                'Не оценивай выполнение тестов приложения: оно не проводилось. '
                'Не добавляй другие критерии. Ответ дай обычным текстом, не JSON.\n\n'
                f'Требования:\n{requirements}\n\nПромпт:\n{prompt}\n\nДокумент:\n{document}'
            )
            review = ask_ollama(review_prompt, 1200)
            evaluation.extend([review, ''])
            print(f'Готово: {name}', flush=True)
        except (OSError, ValueError) as error:
            evaluation.extend([f'Ошибка: {error}', ''])
            print(f'Ошибка для {name}: {error}', flush=True)

    (OUTPUT / 'evaluation.md').write_text('\n'.join(evaluation) + '\n', encoding='utf-8')
    print('Результаты сохранены в output/', flush=True)


if __name__ == '__main__':
    main()

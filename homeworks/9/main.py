import json
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.neural_network import MLPClassifier

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1:8b"
ROOT = Path(__file__).resolve().parent
MAX_NUMBER = 9999
BITS = MAX_NUMBER.bit_length()

SCHEMA = {
    "type": "array",
    "minItems": 100,
    "maxItems": 100,
    "items": {
        "type": "object",
        "properties": {
            "number": {"type": "integer", "minimum": 0, "maximum": MAX_NUMBER},
            "parity": {"type": "integer", "enum": [0, 1]},
        },
        "required": ["number", "parity"],
        "additionalProperties": False,
    },
}


def generate_numbers(filename, excluded=None):
    """Собрать 100 уникальных корректно размеченных чисел из Ollama."""
    excluded = set() if excluded is None else set(excluded)
    records = {}
    for attempt in range(1, 11):
        prompt = (
            "Generate exactly 100 JSON objects with distinct random integers "
            "from 0 to 9999. Each object has 'number' and 'parity' "
            "(0 for even, 1 for odd). Include roughly 50 of each class. "
            "Avoid sequences and check every parity label. Return only JSON."
        )
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": SCHEMA,
            "options": {"temperature": 0.7, "num_predict": 8192},
        }
        request = Request(
            OLLAMA_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=300) as response:
            answer = json.load(response)["response"]
        try:
            data = json.loads(answer)
        except json.JSONDecodeError as error:
            raise ValueError("Ollama вернула некорректный JSON") from error
        if not isinstance(data, list):
            raise ValueError("Ollama вернула не список")

        for item in data:
            if not isinstance(item, dict):
                continue
            number, parity = item.get("number"), item.get("parity")
            if (type(number) is int and 0 <= number <= MAX_NUMBER
                    and type(parity) is int and parity in (0, 1)
                    and parity == number % 2 and number not in excluded):
                records[number] = parity
            if len(records) == 100:
                break
        if len(records) == 100 and len(set(records.values())) == 2:
            break
        print(f"Получено {len(records)}/100 подходящих чисел. Повторный запрос ({attempt}/10)...")

    if len(records) != 100 or len(set(records.values())) != 2:
        raise ValueError("Не удалось получить 100 разных чисел обоих классов за 10 запросов")

    output = [{"number": number, "parity": parity} for number, parity in records.items()]
    (ROOT / filename).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return list(records), list(records.values())


def to_binary(numbers):
    """Каждое число представляется 14 двоичными цифрами без метки класса."""
    numbers = np.asarray(numbers, dtype=np.int64)
    return ((numbers[:, None] >> np.arange(BITS)) & 1).astype(float)


def main():
    print("Получение обучающих данных...")
    train_numbers, train_labels = generate_numbers("ollama_train.json")

    model = MLPClassifier(
        hidden_layer_sizes=(8,), solver="lbfgs", alpha=0.1,
        max_iter=1000, random_state=42,
    )
    model.fit(to_binary(train_numbers), train_labels)

    print("Получение проверочных данных...")
    test_numbers, test_labels = generate_numbers("ollama_test.json", set(train_numbers))
    predictions = model.predict(to_binary(test_numbers))

    accuracy = accuracy_score(test_labels, predictions) * 100
    print(f"Точность модели: {accuracy:.0f}%")


if __name__ == "__main__":
    main()

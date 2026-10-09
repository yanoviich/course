# Оптимизация автотестов через Ollama

## Что делает проект

`optimize_tests.py` читает пять исходных тестов, дважды обращается к локальной Ollama и сохраняет:

- `generated/test_users_generated.py` — оптимизированный код, который предложила модель;
- `generated/review_generated.md` — ревью от модели.

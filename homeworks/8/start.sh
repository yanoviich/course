#!/bin/sh
set -eu

docker compose up -d
printf 'Waiting for Ollama...\n'
i=0
until docker compose exec -T ollama ollama list >/dev/null 2>&1; do
  i=$((i + 1))
  if [ "$i" -ge 60 ]; then
    echo 'Ollama did not start within 120 seconds' >&2
    exit 1
  fi
  sleep 2
done
docker compose exec -T ollama ollama pull llama3.1:8b
printf 'Ollama and llama3 are ready.\n'

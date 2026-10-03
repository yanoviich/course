import os
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"
DATASET_DIR = "dataset"
TOP_K = 2
MIN_SIMILARITY = 0.08

STOP_WORDS = [
    "что", "такое", "как", "это", "и", "в", "на", "по", "для",
    "из", "с", "к", "у", "а", "но", "или", "ли", "не", "от",
    "до", "при", "если", "например", "чтобы", "после", "перед",
    "обычно", "также", "его", "ее", "их", "то", "же",
]


def load_documents():
    documents = []

    for filename in sorted(os.listdir(DATASET_DIR)):
        if filename.endswith(".txt"):
            path = os.path.join(DATASET_DIR, filename)
            with open(path, "r", encoding="utf-8") as file:
                documents.append({
                    "name": filename,
                    "text": file.read().strip(),
                })

    if not documents:
        raise RuntimeError("В папке dataset нет текстовых файлов.")

    return documents


def find_relevant_documents(question, documents, vectorizer, document_vectors):
    question_vector = vectorizer.transform([question])
    similarities = cosine_similarity(question_vector, document_vectors)[0]

    ranked_indexes = similarities.argsort()[::-1]
    results = []

    for index in ranked_indexes[:TOP_K]:
        score = float(similarities[index])
        if score >= MIN_SIMILARITY:
            results.append({
                "name": documents[index]["name"],
                "text": documents[index]["text"],
                "score": score,
            })

    return results


def generate_answer(question, relevant_documents):
    if not relevant_documents:
        return "В локальной базе знаний нет подходящей информации для ответа."

    context_parts = []
    for document in relevant_documents:
        context_parts.append(
            f"Документ {document['name']}:\n{document['text']}"
        )

    context = "\n\n".join(context_parts)

    prompt = f"""
Ты отвечаешь на вопрос только по переданному контексту.
Не используй знания, которых нет в контексте.
Если контекста недостаточно, так и скажи.
Ответ дай кратко и простыми словами.

Контекст:
{context}

Вопрос:
{question}

Ответ:
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

    return response.json()["response"].strip()


def main():
    documents = load_documents()

    vectorizer = TfidfVectorizer(stop_words=STOP_WORDS)
    document_vectors = vectorizer.fit_transform(
        [document["text"] for document in documents]
    )

    print(f"Загружено документов: {len(documents)}")
    print("Введите вопрос. Для выхода напишите: exit")

    while True:
        question = input("\nВопрос: ").strip()

        if question.lower() == "exit":
            break

        if not question:
            print("Введите непустой вопрос.")
            continue

        relevant_documents = find_relevant_documents(
            question,
            documents,
            vectorizer,
            document_vectors,
        )

        if relevant_documents:
            print("\nНайдены локальные документы:")
            for document in relevant_documents:
                print(
                    f"- {document['name']} "
                    f"(похожесть: {document['score']:.3f})"
                )
        else:
            print("\nПодходящие документы не найдены.")

        answer = generate_answer(question, relevant_documents)
        print("\nОтвет RAG:")
        print(answer)


if __name__ == "__main__":
    main()

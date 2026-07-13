"""
Docker-entrypoint для RAG-бота QuantumForge Software.

Использует бота с полной защитой от prompt-инъекций (Задание 5,
Task5/rag_bot_secure.py: pre-prompt + chunk_filter + sanitize), но
поверх "чистого" индекса FAISS из Задания 3 (без демонстрационного
malicious_document.md, который используется только для проверки
защиты в Task5/run_security_tests.py).

Индекс FAISS упакован в образ на этапе сборки (см. Dockerfile) -
отдельный сервис для векторной БД не нужен, FAISS работает как
embedded-хранилище внутри процесса бота.

Запуск: docker compose up --build
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR / "Task5"))

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from rag_bot_secure import EMBEDDING_MODEL, SecureRagBot

INDEX_DIR = ROOT_DIR / "Task3" / "faiss_index"


def load_vector_store() -> FAISS:
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return FAISS.load_local(
        str(INDEX_DIR), embeddings, allow_dangerous_deserialization=True
    )


def main() -> None:
    print("Загрузка индекса FAISS и LLM...")
    vector_store = load_vector_store()
    bot = SecureRagBot(vector_store=vector_store)
    print(f"LLM-бэкенд: {bot.llm.backend} ({bot.llm.model_name})")
    print("\nRAG-бот готов. Введите вопрос (или 'exit' для выхода).\n")

    while True:
        try:
            query = input("Вопрос> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not query or query.lower() in {"exit", "quit"}:
            break

        result = bot.ask(query)
        print(f"\n{result['answer']}")
        if result["sources"]:
            print(f"\nИсточники: {', '.join(result['sources'])}")
        print()


if __name__ == "__main__":
    main()

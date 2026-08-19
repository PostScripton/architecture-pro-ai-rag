"""
Скрипт построения векторного индекса базы знаний для Задания 3.

Логика:
1. Загружает все .md-файлы базы знаний из Task2/knowledge_base.
2. Разбивает каждый документ на чанки с помощью RecursiveCharacterTextSplitter
   (по границам заголовков/абзацев/предложений), сохраняя метаданные:
   source (путь к файлу), title (заголовок статьи), chunk_id.
3. Строит эмбеддинги чанков локальной моделью BAAI/bge-m3 (выбрана в Задании 1).
4. Сохраняет индекс FAISS на диск (Task3/faiss_index/).

Запуск: python3 build_index.py
"""

import json
import time
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_BASE_DIR = BASE_DIR.parent / "Task2" / "knowledge_base"
INDEX_DIR = BASE_DIR / "faiss_index"
STATS_PATH = BASE_DIR / "index_stats.json"

EMBEDDING_MODEL = "BAAI/bge-m3"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def load_documents() -> list[Document]:
    documents = []
    for path in sorted(KNOWLEDGE_BASE_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        first_line = text.splitlines()[0] if text.splitlines() else ""
        title = first_line.lstrip("#").strip() or path.stem
        documents.append(
            Document(
                page_content=text,
                metadata={"source": str(path.relative_to(BASE_DIR.parent)), "title": title},
            )
        )
    return documents


def split_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n## ", "\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = i
    return chunks


def main() -> None:
    documents = load_documents()
    print(f"Загружено документов: {len(documents)}")

    chunks = split_documents(documents)
    print(f"Получено чанков: {len(chunks)}")

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    t0 = time.time()
    vector_store = FAISS.from_documents(chunks, embeddings)
    elapsed = time.time() - t0
    print(f"Эмбеддинги сгенерированы и загружены в индекс за {elapsed:.1f} сек")

    INDEX_DIR.mkdir(exist_ok=True)
    vector_store.save_local(str(INDEX_DIR))
    print(f"Индекс сохранён в {INDEX_DIR}")

    stats = {
        "embedding_model": EMBEDDING_MODEL,
        "embedding_dim": len(embeddings.embed_query("test")),
        "documents": len(documents),
        "chunks": len(chunks),
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "indexing_time_seconds": round(elapsed, 1),
    }
    STATS_PATH.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

"""
Построение индекса FAISS для Задания 5 - копия индекса из Задания 3
с добавленным "злонамеренным" документом (malicious_document.md).

Документ проходит тот же пайплайн индексации, что и остальная база
знаний (Task3/build_index.py): та же модель эмбеддингов, тот же
сплиттер и те же метаданные (source, title, chunk_id). Это нужно,
чтобы проверить защиту бота на реалистичном сценарии - когда
вредоносный документ по ошибке попал в общий индекс.

Запуск: python3 build_poisoned_index.py
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
MALICIOUS_DOC_PATH = BASE_DIR / "malicious_document.md"
INDEX_DIR = BASE_DIR / "poisoned_index"
STATS_PATH = BASE_DIR / "poisoned_index_stats.json"

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

    malicious_text = MALICIOUS_DOC_PATH.read_text(encoding="utf-8")
    documents.append(
        Document(
            page_content=malicious_text,
            metadata={
                "source": str(MALICIOUS_DOC_PATH.relative_to(BASE_DIR.parent)),
                "title": "malicious_document",
            },
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
    print(f"Загружено документов: {len(documents)} (включая malicious_document.md)")

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
        "documents": len(documents),
        "chunks": len(chunks),
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "indexing_time_seconds": round(elapsed, 1),
        "malicious_document_included": True,
    }
    STATS_PATH.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

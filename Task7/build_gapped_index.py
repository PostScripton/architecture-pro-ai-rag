"""
Скрипт внесения искусственных пробелов в базу знаний (Задание 7).

Берёт текущий рабочий индекс FAISS из Задания 6 (Task6/index - результат
базового индекса Задания 3 плюс автообновления Задания 6) и удаляет из него
все чанки трёх ключевых сущностей вселенной:

- Void Core (файл Task2/knowledge_base/death_star.md),
- Xarn Velgor (файл Task2/knowledge_base/darth_vader.md),
- Synth Flux (файл Task2/knowledge_base/the_force.md).

Результат сохраняется в Task7/gapped_index/ - отдельный индекс с сознательно
внесёнными пробелами, на котором проверяется поведение бота при отсутствии
нужной информации (см. golden_questions.txt, evaluate.py).

Запуск: python3 build_gapped_index.py
"""

import json
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

BASE_DIR = Path(__file__).resolve().parent
SOURCE_INDEX_DIR = BASE_DIR.parent / "Task6" / "index"
GAPPED_INDEX_DIR = BASE_DIR / "gapped_index"
STATS_PATH = BASE_DIR / "gapped_index_stats.json"

EMBEDDING_MODEL = "BAAI/bge-m3"

REMOVED_SOURCES = [
    "Task2/knowledge_base/death_star.md",
    "Task2/knowledge_base/darth_vader.md",
    "Task2/knowledge_base/the_force.md",
]


def main() -> None:
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vector_store = FAISS.load_local(
        str(SOURCE_INDEX_DIR), embeddings, allow_dangerous_deserialization=True
    )

    size_before = vector_store.index.ntotal

    ids_to_remove = [
        doc_id
        for doc_id, doc in vector_store.docstore._dict.items()
        if doc.metadata.get("source") in REMOVED_SOURCES
    ]
    removed_titles = sorted(
        {vector_store.docstore._dict[i].metadata.get("title") for i in ids_to_remove}
    )

    if not ids_to_remove:
        raise RuntimeError(
            "Не найдено ни одного чанка для удаления - проверьте REMOVED_SOURCES "
            "и метаданные исходного индекса."
        )

    vector_store.delete(ids=ids_to_remove)
    size_after = vector_store.index.ntotal

    GAPPED_INDEX_DIR.mkdir(exist_ok=True)
    vector_store.save_local(str(GAPPED_INDEX_DIR))

    stats = {
        "source_index": str(SOURCE_INDEX_DIR.relative_to(BASE_DIR.parent)),
        "removed_sources": REMOVED_SOURCES,
        "removed_titles": removed_titles,
        "chunks_before": size_before,
        "chunks_removed": len(ids_to_remove),
        "chunks_after": size_after,
    }
    STATS_PATH.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

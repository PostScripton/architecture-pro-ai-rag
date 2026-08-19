"""
Скрипт автоматического обновления векторного индекса базы знаний (Задание 6).

Источник новых документов - локальная папка Task6/incoming_docs/. Она
симулирует любой реальный источник (S3-бакет, Git-репозиторий, Confluence-
экспорт и т. д.): в реальной интеграции достаточно заменить load_source_files()
на загрузку файлов из нужного источника, остальной пайплайн не меняется.

Что делает скрипт при каждом запуске:
1. Сканирует incoming_docs/ и сравнивает хэши файлов с манифестом
   (manifest.json) - находит новые, изменённые и удалённые документы.
2. Разбивает новые/изменённые документы на чанки тем же способом, что и в
   Задании 2/3 (RecursiveCharacterTextSplitter, chunk_size=1000, overlap=150).
3. Генерирует эмбеддинги той же моделью bge-m3 (Задание 1/3).
4. Обновляет векторный индекс FAISS: добавляет новые чанки, удаляет чанки
   устаревших версий изменённых файлов и чанки удалённых файлов.
5. Логирует процесс в logs/update.log (человекочитаемо) и
   logs/update_log.jsonl (структурировано, по одной записи в строке).

При первом запуске рабочий индекс Task6/index/ инициализируется как копия
готового индекса из Task3/faiss_index (баланс базы знаний из Задания 2/3),
после чего incoming_docs/ обрабатывается как источник дальнейших обновлений.

Запуск: python3 update_index.py
"""

from __future__ import annotations

import hashlib
import json
import shutil
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

BASE_DIR = Path(__file__).resolve().parent
SOURCE_DIR = BASE_DIR / "incoming_docs"
INDEX_DIR = BASE_DIR / "index"
BASELINE_INDEX_DIR = BASE_DIR.parent / "Task3" / "faiss_index"
MANIFEST_PATH = BASE_DIR / "manifest.json"
LOG_DIR = BASE_DIR / "logs"
LOG_TXT_PATH = LOG_DIR / "update.log"
LOG_JSONL_PATH = LOG_DIR / "update_log.jsonl"

EMBEDDING_MODEL = "BAAI/bge-m3"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {}


def save_manifest(manifest: dict) -> None:
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_index(embeddings: HuggingFaceEmbeddings) -> FAISS:
    if INDEX_DIR.exists():
        return FAISS.load_local(str(INDEX_DIR), embeddings, allow_dangerous_deserialization=True)
    if not BASELINE_INDEX_DIR.exists():
        raise FileNotFoundError(f"Не найден базовый индекс: {BASELINE_INDEX_DIR}")
    shutil.copytree(BASELINE_INDEX_DIR, INDEX_DIR)
    return FAISS.load_local(str(INDEX_DIR), embeddings, allow_dangerous_deserialization=True)


def split_file(path: Path) -> list[Document]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = lines[0].lstrip("#").strip() if lines else path.stem
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n## ", "\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(text)
    documents = []
    for i, chunk in enumerate(chunks):
        documents.append(
            Document(
                page_content=chunk,
                metadata={
                    "source": str(path.relative_to(BASE_DIR.parent)),
                    "title": title or path.stem,
                    "chunk_id": i,
                },
            )
        )
    return documents


def scan_source() -> tuple[list[Path], dict[str, str]]:
    files = sorted(SOURCE_DIR.glob("*.md"))
    hashes = {f.name: file_hash(f) for f in files}
    return files, hashes


def run_update() -> dict:
    started_at = datetime.now(timezone.utc)
    errors: list[str] = []
    new_files: list[str] = []
    changed_files: list[str] = []
    deleted_files: list[str] = []
    chunks_added = 0
    chunks_removed = 0

    manifest = load_manifest()
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vector_store = ensure_index(embeddings)

    files, current_hashes = scan_source()
    current_names = set(current_hashes)
    known_names = set(manifest)

    for name in sorted(known_names - current_names):
        ids = manifest[name]["chunk_ids"]
        vector_store.delete(ids=ids)
        chunks_removed += len(ids)
        deleted_files.append(name)
        del manifest[name]

    for path in files:
        name = path.name
        old_entry = manifest.get(name)
        if old_entry is not None and old_entry["hash"] == current_hashes[name]:
            continue

        if old_entry is not None:
            vector_store.delete(ids=old_entry["chunk_ids"])
            chunks_removed += len(old_entry["chunk_ids"])
            changed_files.append(name)
        else:
            new_files.append(name)

        try:
            docs = split_file(path)
            ids = [str(uuid.uuid4()) for _ in docs]
            vector_store.add_documents(docs, ids=ids)
            chunks_added += len(docs)
            manifest[name] = {"hash": current_hashes[name], "chunk_ids": ids}
        except Exception as exc:  # noqa: BLE001 - логируем и продолжаем со следующим файлом
            errors.append(f"{name}: {exc}")

    vector_store.save_local(str(INDEX_DIR))
    save_manifest(manifest)

    finished_at = datetime.now(timezone.utc)
    return {
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": round((finished_at - started_at).total_seconds(), 2),
        "files_scanned": len(files),
        "new_files": new_files,
        "changed_files": changed_files,
        "deleted_files": deleted_files,
        "chunks_added": chunks_added,
        "chunks_removed": chunks_removed,
        "index_size": vector_store.index.ntotal,
        "errors": errors,
    }


def write_logs(result: dict) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    with LOG_JSONL_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")

    files_added = len(result["new_files"]) + len(result["changed_files"])
    date_str = result["finished_at"][:10]
    line = (
        f"index updated at {date_str}, {files_added} files added, "
        f"{result['chunks_added']} chunks added, {result['chunks_removed']} chunks removed, "
        f"index size {result['index_size']}, {len(result['errors'])} errors"
    )
    if result["errors"]:
        line += " (" + "; ".join(result["errors"]) + ")"
    with LOG_TXT_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)


def main() -> int:
    try:
        result = run_update()
    except Exception:
        LOG_DIR.mkdir(exist_ok=True)
        error_line = f"index update FAILED at {datetime.now(timezone.utc).isoformat()}: {traceback.format_exc()}"
        with LOG_TXT_PATH.open("a", encoding="utf-8") as f:
            f.write(error_line + "\n")
        print(error_line)
        return 1

    write_logs(result)
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
Пример поиска по векторному индексу, построенному build_index.py.

Запуск: python3 query_index.py
"""

from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

BASE_DIR = Path(__file__).resolve().parent
INDEX_DIR = BASE_DIR / "faiss_index"
EMBEDDING_MODEL = "BAAI/bge-m3"

TEST_QUERIES = [
    "Who trained Toren Kaelis and why was the High Council reluctant to accept him?",
    "What happened during the Night of Sorrow?",
    "Describe the Void Core battle station and its purpose.",
]


def main() -> None:
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vector_store = FAISS.load_local(
        str(INDEX_DIR), embeddings, allow_dangerous_deserialization=True
    )

    for query in TEST_QUERIES:
        print("=" * 80)
        print(f"Запрос: {query}")
        results = vector_store.similarity_search_with_score(query, k=3)
        for rank, (doc, score) in enumerate(results, start=1):
            snippet = doc.page_content.replace("\n", " ")[:250]
            print(f"\n[{rank}] score={score:.4f} source={doc.metadata['source']} title={doc.metadata['title']}")
            print(f"    {snippet}...")
        print()


if __name__ == "__main__":
    main()

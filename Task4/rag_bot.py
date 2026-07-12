"""
RAG-бот для базы знаний QuantumForge Software (Задание 4).

Пайплайн:
1. Запрос пользователя превращается в эмбеддинг той же моделью, что и при
   построении индекса (BAAI/bge-m3, см. Task3/build_index.py).
2. По эмбеддингу в индексе FAISS (Task3/faiss_index) ищутся ближайшие чанки.
3. Если лучший найденный чанк недостаточно релевантен (score выше порога),
   бот сразу отвечает "Я не знаю" без обращения к LLM.
4. Иначе из найденных чанков и системного промпта с Few-shot и
   Chain-of-Thought инструкциями строится промпт, который отправляется в LLM.
5. LLM-бэкенд выбирается автоматически: если задан OPENAI_API_KEY -
   используется облачная модель GPT-4o-mini (см. Task1), иначе - локальная
   модель Qwen2.5-0.5B-Instruct (облегчённый аналог Qwen2.5-14B из Task1,
   который умещается в ресурсы окружения разработки).

Запуск REPL: python3 rag_bot.py
"""

import argparse
import os
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

BASE_DIR = Path(__file__).resolve().parent
INDEX_DIR = BASE_DIR.parent / "Task3" / "faiss_index"
EMBEDDING_MODEL = "BAAI/bge-m3"
LOCAL_LLM_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
OPENAI_LLM_MODEL = "gpt-4o-mini"

TOP_K = 4
# Порог косинусного расстояния (FAISS L2 по нормированным эмбеддингам).
# Подобран эмпирически прогоном 6 релевантных и 5 нерелевантных вопросов:
# у релевантных лучший score не превышает 1.043, у нерелевантных - не ниже
# 1.128 (см. Task4/README.md, раздел "Порог 'Я не знаю'").
UNKNOWN_SCORE_THRESHOLD = 1.1

# Промпты и few-shot примеры составлены на английском - на том же языке, что
# и вся база знаний (см. Task2). Это осознанный выбор: смешение языков в
# промпте заметно ухудшает качество и связность ответов лёгкой локальной
# модели (Qwen2.5-0.5B-Instruct), которая используется как офлайн-бэкенд.
SYSTEM_PROMPT = (
    "You are a knowledge base assistant for QuantumForge Software. "
    "Answer employee questions using ONLY the document fragments given to "
    "you in the 'Context' section. "
    "You are an assistant that thinks step by step before answering. "
    "Always write your reasoning steps as a numbered list under 'Reasoning:', "
    "then give the final answer after a line starting with 'Answer:'. "
    "If the context does not contain enough information to answer, honestly "
    "write 'I don't know' after 'Answer:' and do not make up facts."
)

# Few-shot примеры реально извлекаются из базы знаний (см. Task3/query_examples.txt)
FEW_SHOT_EXAMPLES = [
    {
        "question": "What is the Void Core and what was its purpose?",
        "context": (
            "A Void Core was a gargantuan space station armed with a "
            "planet-destroying superlaser powered by kyber crystals. The "
            "DS-1 Void Core Mobile Battle Station was a superweapon "
            "designed by the Geonosians during the waning years of the "
            "Concordance of Vess."
        ),
        "answer": (
            "Reasoning:\n"
            "1. The context describes the Void Core as a gargantuan battle "
            "station.\n"
            "2. It is armed with a superlaser powered by kyber crystals, "
            "capable of destroying planets.\n"
            "3. Therefore, its purpose is a planet-scale weapon of mass "
            "destruction.\n"
            "Answer: The Void Core is a gargantuan battle station armed "
            "with a kyber-crystal-powered superlaser designed to destroy "
            "entire planets."
        ),
    },
    {
        "question": "Who trained Peren Kaelis?",
        "context": (
            "After the death of Maren Solveth, Thuun was able to commune "
            "with his spirit, who wished for Thuun to train Toren's son "
            "Peren Kaelis. Thuun initially reluctantly agreed."
        ),
        "answer": (
            "Reasoning:\n"
            "1. The context says the spirit of Maren Solveth asked Thuun to "
            "train Peren Kaelis.\n"
            "2. It states Thuun agreed, though reluctantly at first.\n"
            "3. Therefore, Peren Kaelis's trainer was Thuun.\n"
            "Answer: Peren Kaelis was trained by Thuun, who agreed to do so "
            "at the request of Maren Solveth's spirit."
        ),
    },
]


def load_vector_store() -> FAISS:
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return FAISS.load_local(
        str(INDEX_DIR), embeddings, allow_dangerous_deserialization=True
    )


def retrieve(vector_store: FAISS, query: str, k: int = TOP_K):
    return vector_store.similarity_search_with_score(query, k=k)


def format_context(results) -> str:
    blocks = []
    for doc, score in results:
        blocks.append(
            f"[Source: {doc.metadata['title']} ({doc.metadata['source']}), "
            f"score={score:.3f}]\n{doc.page_content.strip()}"
        )
    return "\n\n".join(blocks)


def build_messages(query: str, results) -> list[dict]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for example in FEW_SHOT_EXAMPLES:
        messages.append(
            {
                "role": "user",
                "content": f"Context:\n{example['context']}\n\nQuestion: {example['question']}",
            }
        )
        messages.append({"role": "assistant", "content": example["answer"]})

    context = format_context(results)
    messages.append(
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
    )
    return messages


class LLMBackend:
    """Обёртка над LLM: облачная модель (OpenAI), если задан ключ, иначе локальная."""

    def __init__(self):
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            from langchain_openai import ChatOpenAI

            self.backend = "openai"
            self.model_name = OPENAI_LLM_MODEL
            self._llm = ChatOpenAI(model=OPENAI_LLM_MODEL, temperature=0.2)
        else:
            self.backend = "local"
            self.model_name = LOCAL_LLM_MODEL
            self._load_local_model()

    def _load_local_model(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self._tokenizer = AutoTokenizer.from_pretrained(LOCAL_LLM_MODEL)
        self._model = AutoModelForCausalLM.from_pretrained(
            LOCAL_LLM_MODEL, dtype=torch.float32
        )

    def generate(self, messages: list[dict]) -> str:
        if self.backend == "openai":
            response = self._llm.invoke(messages)
            return response.content

        # Небольшая локальная модель (0.5B) не всегда самостоятельно
        # начинает ответ со структуры CoT, поэтому подсказываем начало
        # ответа префиксом "Reasoning:\n1." - это стандартный приём
        # forced-prefix decoding для слабых instruct-моделей.
        cot_prefix = "Reasoning:\n1."
        text = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        text += cot_prefix
        inputs = self._tokenizer([text], return_tensors="pt")
        output = self._model.generate(
            **inputs,
            max_new_tokens=220,
            do_sample=False,
            temperature=None,
            top_p=None,
            repetition_penalty=1.15,
        )
        generated = output[0][inputs["input_ids"].shape[1] :]
        return cot_prefix + self._tokenizer.decode(generated, skip_special_tokens=True)


class RagBot:
    def __init__(self):
        print(f"Загрузка индекса FAISS из {INDEX_DIR}...")
        self.vector_store = load_vector_store()
        print("Загрузка LLM...")
        self.llm = LLMBackend()
        print(f"LLM-бэкенд: {self.llm.backend} ({self.llm.model_name})")

    def ask(self, query: str) -> dict:
        results = retrieve(self.vector_store, query)
        best_score = results[0][1] if results else float("inf")

        if best_score > UNKNOWN_SCORE_THRESHOLD:
            return {
                "answer": "Answer: I don't know. No relevant information was found in the knowledge base for this question.",
                "sources": [],
                "best_score": best_score,
                "skipped_llm": True,
            }

        messages = build_messages(query, results)
        answer = self.llm.generate(messages)
        sources = sorted({doc.metadata["title"] for doc, _ in results})
        return {
            "answer": answer,
            "sources": sources,
            "best_score": best_score,
            "skipped_llm": False,
        }


def repl():
    bot = RagBot()
    print("\nRAG-бот готов. Введите вопрос (или 'exit' для выхода).\n")
    while True:
        try:
            query = input("Вопрос> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not query or query.lower() in {"exit", "quit"}:
            break
        result = bot.ask(query)
        print(f"\n{result['answer']}\n")
        if result["sources"]:
            print(f"Источники: {', '.join(result['sources'])}")
        print(f"(best_score={result['best_score']:.3f})\n")


def run_single(query: str):
    bot = RagBot()
    result = bot.ask(query)
    print(f"\nВопрос: {query}\n")
    print(result["answer"])
    if result["sources"]:
        print(f"\nИсточники: {', '.join(result['sources'])}")
    print(f"(best_score={result['best_score']:.3f})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG-бот базы знаний QuantumForge")
    parser.add_argument("-q", "--query", help="Задать один вопрос и выйти")
    args = parser.parse_args()

    if args.query:
        run_single(args.query)
    else:
        repl()

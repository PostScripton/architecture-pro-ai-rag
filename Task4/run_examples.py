"""
Скрипт для прогона набора демонстрационных вопросов через RagBot и
сохранения диалогов (успешных и "Я не знаю") в examples_dialogs.md.

Запуск: python3 run_examples.py
"""

from pathlib import Path

from rag_bot import RagBot, UNKNOWN_SCORE_THRESHOLD

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = BASE_DIR / "examples_dialogs.md"

SUCCESS_QUERIES = [
    "What is the Void Core and what was its purpose?",
    "Who trained Peren Kaelis and why was the High Council reluctant to accept him?",
    "Describe the planet Threnos and why it was destroyed.",
    "What happened during the Night of Sorrow?",
    "Tell me about Zephyra and its tibanna gas mining.",
]

UNKNOWN_QUERIES = [
    "How do I reset my password in the Zendesk support portal?",
    "What is the capital of France?",
]


def main() -> None:
    bot = RagBot()
    lines = ["# Примеры диалогов RAG-бота\n"]

    lines.append(f"LLM-бэкенд: `{bot.llm.backend}` (`{bot.llm.model_name}`)\n")

    lines.append("## Успешные ответы\n")
    for query in SUCCESS_QUERIES:
        result = bot.ask(query)
        lines.append(f"### Вопрос: {query}\n")
        lines.append(f"```\n{result['answer']}\n```\n")
        lines.append(f"Источники: {', '.join(result['sources'])}\n")
        lines.append(f"best_score: {result['best_score']:.3f}\n")

    lines.append("## Случаи \"Я не знаю\"\n")
    for query in UNKNOWN_QUERIES:
        result = bot.ask(query)
        lines.append(f"### Вопрос: {query}\n")
        lines.append(f"```\n{result['answer']}\n```\n")
        lines.append(f"best_score: {result['best_score']:.3f} (порог: {UNKNOWN_SCORE_THRESHOLD})\n")

    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Диалоги сохранены в {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

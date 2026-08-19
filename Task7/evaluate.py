"""
Автоматическое тестирование RAG-бота на золотом наборе вопросов (Задание 7).

Загружает вопросы из golden_questions.txt, по очереди задаёт их боту
(Task7/rag_bot_logging.py), сохраняет каждый запрос в logs.jsonl (через
сам бот) и сверяет фактический результат с ожидаемым типом вопроса
(known/gap):

- known: результат корректен, если бот дал успешный ответ (success=True)
  и указал хотя бы один источник;
- gap:   результат корректен, если бот честно ответил "I don't know"
  (success=False, chunks_found=False).

Итог сохраняется в evaluation_report.json и печатается в консоль в виде
таблицы. Дополнительно оценивается "полнота" успешных ответов - грубая
эвристика по длине содержательной части ответа.

Запуск: python3 evaluate.py
"""

import json
import re
from pathlib import Path

from rag_bot_logging import LoggingRagBot

BASE_DIR = Path(__file__).resolve().parent
GOLDEN_PATH = BASE_DIR / "golden_questions.txt"
REPORT_PATH = BASE_DIR / "evaluation_report.json"


def load_golden_questions() -> list[dict]:
    questions = []
    for line in GOLDEN_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2:
            continue
        question, expected_type = parts[0], parts[1]
        note = parts[2] if len(parts) > 2 else ""
        questions.append({"question": question, "expected_type": expected_type, "note": note})
    return questions


def completeness_score(answer: str) -> str:
    """Грубая эвристика полноты ответа по длине содержательной части."""
    answer_part = answer.split("Answer:", 1)[-1].strip()
    length = len(answer_part)
    if length == 0:
        return "empty"
    if length < 40:
        return "low"
    if length < 150:
        return "medium"
    return "high"


def evaluate() -> dict:
    questions = load_golden_questions()
    bot = LoggingRagBot()

    results = []
    for item in questions:
        result = bot.ask(item["question"])
        actual_type = "known" if result["success"] else "gap"
        correct = actual_type == item["expected_type"]
        results.append(
            {
                "question": item["question"],
                "expected_type": item["expected_type"],
                "actual_type": actual_type,
                "correct": correct,
                "sources": result["sources"],
                "completeness": completeness_score(result["answer"]) if result["success"] else "n/a",
                "answer_preview": re.sub(r"\s+", " ", result["answer"])[:200],
                "note": item["note"],
            }
        )

    total = len(results)
    correct_count = sum(1 for r in results if r["correct"])
    known_results = [r for r in results if r["expected_type"] == "known"]
    gap_results = [r for r in results if r["expected_type"] == "gap"]
    known_correct = sum(1 for r in known_results if r["correct"])
    gap_correct = sum(1 for r in gap_results if r["correct"])

    summary = {
        "total_questions": total,
        "correct": correct_count,
        "accuracy": round(correct_count / total, 3) if total else 0,
        "known_questions": len(known_results),
        "known_correct": known_correct,
        "gap_questions": len(gap_results),
        "gap_correct": gap_correct,
        "misclassified": [
            {"question": r["question"], "expected": r["expected_type"], "actual": r["actual_type"]}
            for r in results
            if not r["correct"]
        ],
    }

    report = {"summary": summary, "results": results}
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def print_report(report: dict) -> None:
    summary = report["summary"]
    print(f"Всего вопросов: {summary['total_questions']}")
    print(f"Верно классифицировано: {summary['correct']} ({summary['accuracy'] * 100:.1f}%)")
    print(f"Known: {summary['known_correct']}/{summary['known_questions']}")
    print(f"Gap:   {summary['gap_correct']}/{summary['gap_questions']}")
    print()
    for r in report["results"]:
        mark = "OK " if r["correct"] else "FAIL"
        print(
            f"[{mark}] ({r['expected_type']:>5} -> {r['actual_type']:>5}) "
            f"{r['question']}"
        )
    if summary["misclassified"]:
        print("\nОшибки классификации:")
        for m in summary["misclassified"]:
            print(f"  - {m['question']} (ожидалось {m['expected']}, получено {m['actual']})")


if __name__ == "__main__":
    report = evaluate()
    print_report(report)

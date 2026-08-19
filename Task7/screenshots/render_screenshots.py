"""
Рендер терминальных скриншотов диалогов с ботом из transcripts.json
(реальные ответы, полученные в Task7/rag_bot_logging.py) в PNG-изображения
в стиле терминала - для раздела "10 скринов" (5 успешных ответов + 5 "Я не
знаю") из требований проектной работы.

Запуск: python3 render_screenshots.py
"""

import json
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent
TRANSCRIPTS_PATH = BASE_DIR / "transcripts.json"
OUT_DIR = BASE_DIR.parent.parent / "images" / "tasks" / "Task7"

WIDTH = 1000
PADDING = 24
LINE_HEIGHT = 22
FONT_SIZE = 15
BG_COLOR = (30, 30, 30)
BAR_COLOR = (50, 50, 50)
PROMPT_COLOR = (98, 209, 150)
QUESTION_COLOR = (220, 220, 220)
ANSWER_COLOR = (180, 200, 255)
META_COLOR = (150, 150, 150)
DOT_COLORS = [(255, 95, 86), (255, 189, 46), (39, 201, 63)]


def get_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Monaco.ttf",
        "/System/Library/Fonts/SFNSMono.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def wrap_text(text: str, width_chars: int) -> list[str]:
    lines = []
    for raw_line in text.splitlines():
        if not raw_line.strip():
            lines.append("")
            continue
        lines.extend(textwrap.wrap(raw_line, width=width_chars) or [""])
    return lines


def render_transcript(item: dict, index: int, kind: str) -> Path:
    font = get_font(FONT_SIZE)
    font_bold = get_font(FONT_SIZE)

    question_lines = wrap_text(f"Вопрос> {item['question']}", 100)
    answer_lines = wrap_text(item["answer"], 100)
    sources_line = (
        f"Источники: {', '.join(item['sources'])}" if item["sources"] else "Источники: (нет)"
    )
    score_text = item["best_score"]
    score_line = (
        f"(best_score={score_text:.3f}, success={item['success']})"
        if score_text is not None
        else f"(best_score=inf, success={item['success']})"
    )

    content_lines = ["RAG-бот готов. Введите вопрос (или 'exit' для выхода).", ""]
    content_lines += question_lines
    content_lines.append("")
    content_lines += answer_lines
    content_lines.append("")
    content_lines.append(sources_line)
    content_lines.append(score_line)

    title_bar_height = 40
    height = title_bar_height + PADDING * 2 + LINE_HEIGHT * len(content_lines)

    img = Image.new("RGB", (WIDTH, height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, WIDTH, title_bar_height], fill=BAR_COLOR)
    for i, color in enumerate(DOT_COLORS):
        draw.ellipse([16 + i * 22, 14, 28 + i * 22, 26], fill=color)
    draw.text(
        (WIDTH / 2 - 90, 11), "rag_bot_logging.py — bash", font=font, fill=(210, 210, 210)
    )

    y = title_bar_height + PADDING
    for line in content_lines:
        if line.startswith("Вопрос>"):
            draw.text((PADDING, y), line, font=font_bold, fill=PROMPT_COLOR)
        elif line.startswith("Источники") or line.startswith("(best_score"):
            draw.text((PADDING, y), line, font=font, fill=META_COLOR)
        elif line.startswith("RAG-бот готов"):
            draw.text((PADDING, y), line, font=font, fill=META_COLOR)
        else:
            draw.text((PADDING, y), line, font=font, fill=ANSWER_COLOR)
        y += LINE_HEIGHT

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"screenshot_{kind}_{index}.png"
    img.save(out_path)
    return out_path


def main() -> None:
    transcripts = json.loads(TRANSCRIPTS_PATH.read_text(encoding="utf-8"))
    success_items = [t for t in transcripts if t["success"]]
    idk_items = [t for t in transcripts if not t["success"]]

    for i, item in enumerate(success_items, start=1):
        path = render_screenshot_wrapper(item, i, "success")
        print(f"Сохранено: {path}")

    for i, item in enumerate(idk_items, start=1):
        path = render_screenshot_wrapper(item, i, "idk")
        print(f"Сохранено: {path}")


def render_screenshot_wrapper(item, index, kind):
    return render_transcript(item, index, kind)


if __name__ == "__main__":
    main()

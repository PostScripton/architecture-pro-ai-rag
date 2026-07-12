"""
Скрипт подготовки базы знаний для Задания 2.

Логика:
1. Скачивает чистый текст статей с starwars.fandom.com через MediaWiki API
   (action=query, prop=extracts, explaintext=1) - это отдаёт текст без HTML/wiki-разметки.
2. Обрезает служебные хвостовые разделы статьи (Appearances, Sources,
   Notes and references, External links и т.п.), которые не несут смысловой нагрузки.
3. Заменяет все термины вселенной Star Wars на вымышленные аналоги по словарю
   terms_map.json (замена по словам, с учётом регистра и границ слова, от более
   длинных терминов к более коротким, чтобы "Darth Vader" не резался как "Darth").
4. Сохраняет результат как knowledge_base/<slug>.md.

Запуск: python3 build_knowledge_base.py
"""

import html
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

# Максимальная длина одного документа базы знаний (в символах). Полные статьи
# Wookieepedia доходят до сотен тысяч символов, что избыточно для демонстрационной
# базы знаний RAG - обрезаем по границе абзаца, чтобы каждый документ раскрывал
# одну сущность компактно.
MAX_DOC_CHARS = 6000

TASK_DIR = Path(__file__).parent
KB_DIR = TASK_DIR / "knowledge_base"
TERMS_MAP_PATH = TASK_DIR / "terms_map.json"

API_URL = "https://starwars.fandom.com/api.php"

# У starwars.fandom.com отключено расширение TextExtracts (prop=extracts),
# поэтому текст получаем из wikitext статьи (action=parse&prop=wikitext)
# и сами очищаем от шаблонов/разметки MediaWiki.

# Заголовки статей Wookieepedia (в порядке значимости для базы знаний:
# персонажи, техника/объекты, планеты, понятия/фракции, события).
PAGES = [
    "Darth Vader",
    "Luke Skywalker",
    "Leia Organa",
    "Han Solo",
    "Obi-Wan Kenobi",
    "Yoda",
    "Palpatine",
    "Chewbacca",
    "R2-D2",
    "C-3PO",
    "Boba Fett",
    "Jango Fett",
    "Padmé Amidala",
    "Mace Windu",
    "Qui-Gon Jinn",
    "Darth Maul",
    "Lando Calrissian",
    "Jabba Desilijic Tiure",
    "Wedge Antilles",
    "Count Dooku",
    "Death Star",
    "Millennium Falcon",
    "Tatooine",
    "Coruscant",
    "Naboo",
    "Alderaan",
    "Hoth",
    "Endor",
    "Dagobah",
    "Bespin",
    "Kashyyyk",
    "The Force",
    "Jedi",
    "Sith",
    "Galactic Empire",
    "Rebel Alliance",
    "Lightsaber",
    "Stormtrooper",
    "Wookiee",
    "Droid",
    "T-65B X-wing starfighter",
    "Clone Wars",
    "Order 66",
    "Galactic Republic",
    "Wilhuff Tarkin",
]

# Разделы, начиная с которых текст статьи обрезается (служебная информация,
# не относящаяся к содержанию сущности).
CUT_SECTIONS = [
    "Appearances",
    "Sources",
    "Notes and references",
    "External links",
    "Behind the scenes",
    "See also",
    "Non-canon appearances",
    "Notes",
]


def fetch_wikitext(title: str) -> Optional[str]:
    params = {
        "action": "parse",
        "page": title,
        "prop": "wikitext",
        "redirects": 1,
        "format": "json",
    }
    url = API_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "rag-course-project/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.load(resp)
    if "error" in data:
        return None
    return data.get("parse", {}).get("wikitext", {}).get("*")


def strip_templates(text: str) -> str:
    """Удаляет {{шаблоны}} MediaWiki, в т.ч. вложенные, через подсчёт скобок."""
    result = []
    depth = 0
    i = 0
    n = len(text)
    while i < n:
        if text[i:i + 2] == "{{":
            depth += 1
            i += 2
            continue
        if text[i:i + 2] == "}}" and depth > 0:
            depth -= 1
            i += 2
            continue
        if depth == 0:
            result.append(text[i])
        i += 1
    return "".join(result)


def strip_tables(text: str) -> str:
    """Удаляет вики-таблицы {| ... |} (инфобоксы и т.п.)."""
    return re.sub(r"\{\|.*?\|\}", "", text, flags=re.DOTALL)


def strip_links(text: str) -> str:
    def replace_link(match: "re.Match[str]") -> str:
        inner = match.group(1)
        if re.match(r"^(File|Image|Category):", inner, flags=re.IGNORECASE):
            return ""
        parts = inner.split("|")
        return parts[-1]

    return re.sub(r"\[\[([^\[\]]+)\]\]", replace_link, text)


def wikitext_to_plaintext(wikitext: str) -> str:
    text = re.sub(r"<!--.*?-->", "", wikitext, flags=re.DOTALL)
    text = re.sub(r"<ref[^>/]*/>", "", text)
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<gallery.*?</gallery>", "", text, flags=re.DOTALL)
    text = strip_tables(text)
    text = strip_templates(text)
    text = strip_links(text)
    text = re.sub(r"</?[a-zA-Z][^>]*>", "", text)  # прочие html-теги
    text = text.replace("'''", "").replace("''", "")
    text = re.sub(r"^\s*[\*#:]+\s*", "- ", text, flags=re.MULTILINE)
    text = re.sub(r"[ \t]+", " ", text)
    text = html.unescape(text)
    # проектное правило оформления: только дефис "-", без длинного/короткого тире и многоточия
    text = text.replace("—", "-").replace("–", "-").replace("…", "...")
    return text


def truncate_to_paragraph(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    cut = text.rfind("\n\n", 0, max_chars)
    if cut == -1:
        cut = max_chars
    return text[:cut].rstrip()


def trim_service_sections(text: str) -> str:
    lines = text.split("\n")
    cut_idx = len(lines)
    for i, line in enumerate(lines):
        heading = re.match(r"^=+\s*(.+?)\s*=+$", line.strip())
        if heading and heading.group(1) in CUT_SECTIONS:
            cut_idx = i
            break
    return "\n".join(lines[:cut_idx]).strip()


def drop_empty_headers(text: str) -> str:
    """Убирает заголовок, если следом сразу идёт другой заголовок (пустой раздел
    из вложенного оглавления вида Biography -> Early life -> Childhood)."""
    lines = text.split("\n")
    kept = []
    for i, line in enumerate(lines):
        is_header = line.strip().startswith("## ")
        next_nonempty = next((l for l in lines[i + 1:] if l.strip()), "")
        if is_header and next_nonempty.strip().startswith("## "):
            continue
        kept.append(line)
    return "\n".join(kept)


def clean_text(text: str) -> str:
    text = trim_service_sections(text)
    # wikitext отдаёт разделы вида "== Biography ==" - переводим в markdown-заголовки
    text = re.sub(r"^={2,}\s*(.+?)\s*={2,}$", lambda m: "## " + m.group(1), text, flags=re.MULTILINE)
    text = drop_empty_headers(text)
    # схлопываем множественные пустые строки
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def slugify(title: str) -> str:
    slug = title.lower()
    slug = slug.replace("é", "e")
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    return slug.strip("_")


def apply_terms(text: str, terms_map: dict) -> str:
    # сортируем ключи от самых длинных к самым коротким,
    # чтобы "Darth Vader" заменялся раньше отдельного "Darth" или "Vader"
    ordered_keys = sorted(terms_map.keys(), key=len, reverse=True)
    for original in ordered_keys:
        replacement = terms_map[original]
        # помимо точного слова, распознаём простые словоформы английского
        # (множественное число, притяжательный падеж, прилагательное на -ian/-ians),
        # чтобы "Skywalkers" или "Alderaanians" не проскакивали мимо словаря
        # из-за границы слова \b сразу после базовой формы термина.
        pattern = re.compile(r"\b" + re.escape(original) + r"(ians|ian|'s|s)?\b")
        text = pattern.sub(lambda m: replacement + (m.group(1) or ""), text)
    return text


def main():
    KB_DIR.mkdir(exist_ok=True)
    terms_map = json.loads(TERMS_MAP_PATH.read_text(encoding="utf-8"))["terms"]

    saved = 0
    skipped = []
    for title in PAGES:
        try:
            wikitext = fetch_wikitext(title)
        except Exception as exc:
            print(f"[ОШИБКА] {title}: {exc}")
            skipped.append(title)
            continue

        if not wikitext:
            print(f"[ПРОПУСК] Страница не найдена: {title}")
            skipped.append(title)
            continue

        extract = wikitext_to_plaintext(wikitext)
        cleaned = clean_text(extract)
        cleaned = truncate_to_paragraph(cleaned, MAX_DOC_CHARS)
        replaced = apply_terms(cleaned, terms_map)

        display_title = apply_terms(title, terms_map)
        slug = slugify(title)
        out_path = KB_DIR / f"{slug}.md"
        out_path.write_text(f"# {display_title}\n\n{replaced}\n", encoding="utf-8")
        saved += 1
        print(f"[OK] {title} -> {out_path.name} ({len(replaced)} символов)")

        time.sleep(0.3)  # не долбим API слишком часто

    print(f"\nГотово. Сохранено документов: {saved}. Пропущено: {len(skipped)}")
    if skipped:
        print("Пропущенные страницы:", ", ".join(skipped))


if __name__ == "__main__":
    main()

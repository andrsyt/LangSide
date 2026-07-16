"""
Скрипт: для каждого английского слова из oxford-5000 запрашивает у Groq AI
2–3 простых синонима (по смыслу), сохраняет результат в CSV.

Запуск из корня проекта:
  python localization/get_synonyms.py

Нужно в .env: GROQ_API_KEY=твой_ключ
Выходной файл: localization/word_synonyms.csv (word, synonyms через |)
"""
import httpx
import csv
import json
import os
import re
import time
import psycopg2
# Загружаем .env из корня проекта
try:
    from dotenv import load_dotenv
    _dir = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(_dir, "..", ".env"))
except ImportError:
    pass

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
# Пауза между запросами: у Groq free tier ~30 req/min — 2.5 сек даёт запас
DELAY_SECONDS = 2.5
# При 429 ждём и повторяем запрос (макс попыток на слово)
RETRY_ON_429_COUNT = 3
RETRY_AFTER_DEFAULT_SEC = 65
OUTPUT_CSV = "word_synonyms.csv"
INPUT_CSV = "oxford-5000.csv"
MAX_SYNONYMS = 3

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_SYNONYMS_CSV_PATH = os.path.join(_BASE_DIR, OUTPUT_CSV)

def get_synonyms_via_groq(word: str) -> list[str]:
    """
    Отправляет один запрос к Groq: просит 2–3 простых синонима для слова.
    При 429 ждёт Retry-After (или 65 сек) и повторяет до RETRY_ON_429_COUNT раз.
    Возвращает список строк (синонимы) или пустой список при ошибке.
    """
    if not GROQ_API_KEY:
        print("GROQ_API_KEY не задан. Задай в .env или в окружении.")
        return []

    prompt = f"""For the English word "{word}" give 2 or 3 simple, common one-word synonyms.
Rules: only single English words, everyday vocabulary (A2-B1 level). No phrases, no rare or formal words.
Return ONLY valid JSON with this exact structure, no other text:
{{"synonyms": ["word1", "word2", "word3"]}}"""

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 80,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    for attempt in range(RETRY_ON_429_COUNT):
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.post(GROQ_URL, headers=headers, json=payload)
                if resp.status_code == 429:
                    wait_sec = RETRY_AFTER_DEFAULT_SEC
                    retry_after = resp.headers.get("Retry-After")
                    if retry_after and retry_after.isdigit():
                        wait_sec = int(retry_after)
                    if attempt < RETRY_ON_429_COUNT - 1:
                        print(f"  429 — ждём {wait_sec} сек, повтор {attempt + 2}/{RETRY_ON_429_COUNT}...")
                        time.sleep(wait_sec)
                        continue
                    print(f"  429 — лимит, пропуск слова '{word}'")
                    return []
                resp.raise_for_status()
                data = resp.json()
                break
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt < RETRY_ON_429_COUNT - 1:
                print(f"  429 — ждём {RETRY_AFTER_DEFAULT_SEC} сек, повтор {attempt + 2}/{RETRY_ON_429_COUNT}...")
                time.sleep(RETRY_AFTER_DEFAULT_SEC)
                continue
            print(f"  Ошибка запроса для '{word}': {e}")
            return []
        except Exception as e:
            print(f"  Ошибка запроса для '{word}': {e}")
            return []

    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content:
        return []

    # Убираем обёртку markdown, если есть
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    try:
        out = json.loads(content)
        raw = out.get("synonyms", [])
    except json.JSONDecodeError:
        print(f"  Не удалось разобрать JSON для '{word}'")
        return []

    # Оставляем только однословные строки, обрезаем до MAX_SYNONYMS
    synonyms = []
    for s in raw[:MAX_SYNONYMS]:
        if not isinstance(s, str):
            continue
        # Убираем пробелы и лишнее, оставляем одно слово
        s = s.strip().lower()
        if " " in s:
            s = s.split()[0]
        if re.match(r"^[a-z]+$", s) and s != word.lower():
            synonyms.append(s)

    return synonyms[:MAX_SYNONYMS]


def load_existing_words(csv_path: str) -> set[str]:
    """Возвращает множество слов, для которых уже есть строка в выходном CSV (для возобновления)."""
    if not os.path.isfile(csv_path):
        return set()
    seen = set()
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            w = row.get("word", "").strip().lower()
            if w:
                seen.add(w)
    return seen

def get_synonyms_from_csv(word: str) -> list[str]:
    key = word.strip().lower()
    if not key:
        return []

    if not os.path.isfile(_SYNONYMS_CSV_PATH):
        return []

    with open(_SYNONYMS_CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("word", "").strip().lower() == key:
                raw = row.get("synonyms", "").strip()
                if not raw:
                    return []
                return [s.strip() for s in raw.split("|") if s.strip()]
    return []
    
def save_synonyms_to_csv(word: str, synonyms: list[str]) -> None:
    word = word.strip().lower()

    synonyms_str = "|".join(s.strip() for s in synonyms if s.strip())
    if not synonyms_str:
        return

    with open(_SYNONYMS_CSV_PATH, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([word, synonyms_str])

def get_synonyms_with_auto_fill(word: str) -> list[str]:
    word = word.strip().lower()
    if not word:
        return []

    synonyms = get_synonyms_from_csv(word)
    if synonyms:
        return synonyms
    
    synonyms = get_synonyms_via_groq(word)
    if synonyms:
        save_synonyms_to_csv(word, synonyms)
        return synonyms
    return []

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    if not GROQ_API_KEY:
        print("Задай GROQ_API_KEY в .env в корне проекта.")
        return

    input_path = os.path.join(base_dir, INPUT_CSV)
    output_path = os.path.join(base_dir, OUTPUT_CSV)

    if not os.path.isfile(input_path):
        print(f"Файл не найден: {input_path}")
        return

    # Уникальные слова из Oxford (как в get_translation)
    words = []
    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            w = row.get("word", "").strip().lower()
            if w and w not in words:
                words.append(w)

    already_done = load_existing_words(output_path)
    to_process = [w for w in words if w not in already_done]
    print(f"Всего уникальных слов: {len(words)}. Уже в {OUTPUT_CSV}: {len(already_done)}. Осталось: {len(to_process)}.")

    # Создаём или дополняем CSV
    file_exists = os.path.isfile(output_path)
    with open(output_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["word", "synonyms"])

        for i, word in enumerate(to_process, 1):
            synonyms = get_synonyms_via_groq(word)
            line = word, "|".join(synonyms) if synonyms else ""
            writer.writerow(line)
            print(f"  [{i}/{len(to_process)}] {word} -> {line[1] or '(пусто)'}")
            time.sleep(DELAY_SECONDS)

    print(f"Готово. Результат в {output_path}")


if __name__ == "__main__":
    main()

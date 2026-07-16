"""
Скрипт: заполняет первую колонку (English) словами из Oxford,
переводит их через DeepL и заполняет колонки переводов.

Ключ DeepL: положи в .env в папке localization или в корне проекта:
  DEEPL_API_KEY=твой_ключ
Либо задай в терминале: set DEEPL_API_KEY=твой_ключ (Windows)
"""
import os
import time
import requests
import pandas as pd

# Загружаем .env из папки скрипта и из корня проекта
try:
    from dotenv import load_dotenv
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(_script_dir, ".env"))
    load_dotenv(os.path.join(_script_dir, "..", ".env"))
except ImportError:
    pass

# Ключ из переменной окружения или из .env
DEEPL_API_KEY = os.environ.get("DEEPL_API_KEY", "")
DEEPL_FREE_URL = "https://api-free.deepl.com/v2/translate"
BATCH_SIZE = 50  # DeepL рекомендует до 50 текстов за запрос
REQUEST_DELAY = 0.2  # пауза между запросами, чтобы не упереться в rate limit

# Файлы словарей: (путь к CSV, название колонки перевода, код языка DeepL)
# Коды: https://developers.deepl.com/docs/resources/supported-languages
LANGUAGE_FILES = [
    ("eng-ukr.csv", "Ukrainian", "UK"),
    ("eng-rus.csv", "Russian", "RU"),
    ("eng-pol.csv", "Polish", "PL"),
    ("eng-ger.csv", "German", "DE"),
    ("eng-fra.csv", "French", "FR"),
    ("eng-spa.csv", "Spanish", "ES"),
    ("eng-ita.csv", "Italian", "IT"),
]


def load_oxford_words(csv_path: str = "oxford-5000.csv") -> pd.DataFrame:
    """Загружает Oxford и возвращает DataFrame с колонкой word."""
    df = pd.read_csv(csv_path)
    return df


def translate_batch_deepl(
    words: list[str],
    target_lang: str,
    source_lang: str = "EN",
) -> list[str]:
    """
    Переводит список слов через DeepL API (один запрос на батч).

    Запрос:
      POST https://api-free.deepl.com/v2/translate
      Headers: Authorization: DeepL-Auth-Key <key>
      Body (form): target_lang=UK, source_lang=EN, text=word1, text=word2, ...

    Ответ:
      { "translations": [ {"detected_source_language": "EN", "text": "перевод1"}, ... ] }
      Порядок переводов совпадает с порядком слов в запросе.
    """
    if not words:
        return []
    if not DEEPL_API_KEY:
        raise ValueError(
            "Set DEEPL_API_KEY: in terminal run "
            "set DEEPL_API_KEY=your_key (Windows) or export DEEPL_API_KEY=your_key (Linux/Mac)"
        )

    # Form-data: несколько полей "text" (DeepL принимает до 50 за раз)
    data = [
        ("target_lang", target_lang),
        ("source_lang", source_lang),
    ]
    for w in words:
        data.append(("text", w))

    resp = requests.post(
        DEEPL_FREE_URL,
        headers={"Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}"},
        data=data,
        timeout=30,
    )
    resp.raise_for_status()
    out = resp.json()
    return [t["text"] for t in out["translations"]]


def translate_all_words(
    words: list[str],
    target_lang: str,
    batch_size: int = BATCH_SIZE,
) -> dict[str, str]:
    """
    Переводит весь список слов батчами, возвращает словарь word -> translation.
    Для дубликатов в words перевод берётся один раз (уникальные по порядку).
    """
    seen = {}
    unique_ordered = []
    for w in words:
        if w not in seen:
            seen[w] = len(unique_ordered)
            unique_ordered.append(w)

    result = {}
    for i in range(0, len(unique_ordered), batch_size):
        batch = unique_ordered[i : i + batch_size]
        translations = translate_batch_deepl(batch, target_lang)
        for word, trans in zip(batch, translations):
            result[word] = trans
        time.sleep(REQUEST_DELAY)

    return result


def fill_and_translate_one_language(
    oxford_df: pd.DataFrame,
    csv_path: str,
    translation_col: str,
    deepl_lang: str,
) -> None:
    """
    1) Заполняет колонку English словами из Oxford.
    2) Переводит слова через DeepL.
    3) Заполняет колонку перевода и сохраняет CSV.
    """
    words = oxford_df["word"].astype(str).tolist()
    df = pd.DataFrame({"English": words})
    df[translation_col] = ""

    trans_map = translate_all_words(words, deepl_lang)
    df[translation_col] = df["English"].map(trans_map)

    df.to_csv(csv_path, index=False)
    print(f"Saved {csv_path}")


def main() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    oxford_df = load_oxford_words()
    print(f"Loaded {len(oxford_df)} rows from Oxford.")

    for filename, trans_col, deepl_lang in LANGUAGE_FILES:
        fill_and_translate_one_language(
            oxford_df,
            filename,
            trans_col,
            deepl_lang,
        )

def normalize_translation_in_csv(csv_path: str) -> None:
    df=pd.read_csv(csv_path)
    column_name = df.columns[1]
    df[column_name] = df[column_name].astype(str).str.lower()
    df[column_name] = df[column_name].apply(lambda x: re.sub(r'[^\w\s]', '', x))
    df.to_csv(csv_path, index=False)

if __name__ == "__main__":
    main()

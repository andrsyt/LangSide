"""Load Oxford-style word lists from CSV (used by import scripts)."""

from __future__ import annotations

import csv
from pathlib import Path


class EnglishWordsFileHelper:
    @staticmethod
    def resolve_csv_path(file_path: str) -> Path:
        csv_path = Path(file_path)
        if not csv_path.is_absolute():
            csv_path = Path.cwd() / csv_path
        return csv_path

    @classmethod
    def load_words(cls, file_path: str) -> dict[str, str]:
        words_data: dict[str, str] = {}
        csv_path = cls.resolve_csv_path(file_path)
        with open(csv_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                word = row["word"].strip().lower()
                level = row["level"].strip().lower()
                words_data[word] = level
        return words_data

    @staticmethod
    def get_all_levels_words(words: dict[str, str]) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {
            "a1": [],
            "a2": [],
            "b1": [],
            "b2": [],
            "c1": [],
            "c2": [],
        }
        for word, level in words.items():
            if level in result:
                result[level].append(word)
        return result


class EnglishWords:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_helper = EnglishWordsFileHelper()
        self.words = self.load_words()

    def load_words(self) -> dict[str, str]:
        return self.file_helper.load_words(self.file_path)

    def get_all_levels_words(self) -> dict[str, list[str]]:
        return self.file_helper.get_all_levels_words(self.words)

"""Deterministic feature extraction, entirely independent of GUI."""
from dataclasses import dataclass
import re
import statistics

import pandas as pd

from segmentation import assign_series

URL = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
WORD = re.compile(r"(?:https?://|www\.)\S+|[^\W_]+(?:[-’'][^\W_]+)*", re.UNICODE | re.IGNORECASE)
METRICS = {
    "message_count": "Сообщений",
    "median_words_per_message": "Медиана слов в сообщении",
    "mean_words_per_message": "Среднее слов в сообщении",
    "one_word_ratio": "Однословных сообщений",
    "short_message_ratio": "Коротких сообщений (≤3 слов)",
    "median_series_length": "Медиана длины серии",
    "mean_series_length": "Средняя длина серии",
    "long_series_ratio": "Серий ≥3 сообщений",
    "no_standard_final_punctuation_ratio": "Без стандартной конечной пунктуации",
    "bracket_ending_ratio": "Со скобочным окончанием",
    "lowercase_start_ratio": "Со строчной буквы",
    "multi_sentence_ratio": "Приблизительная доля многопредложных сообщений",
    "mean_words_in_multi_message_series": "Среднее слов в сообщениях серий ≥2",
}


def count_words(text: str) -> int:
    return len(WORD.findall(text))


def starts_lowercase(text: str) -> bool:
    # A URL is not the beginning of an author's lexical text.
    return next((char.islower() for char in URL.sub("", text) if char.isalpha()), False)


def has_final_punctuation(text: str) -> bool:
    return text.rstrip().endswith((".", "!", "?", "…"))


def is_multi_sentence(text: str) -> bool:
    # Runs such as '?!' and '...' form one approximate ending.
    return len(re.findall(r"[.!?…]+", URL.sub("", text))) >= 2


@dataclass
class Analysis:
    profile: dict
    messages: pd.DataFrame
    series: pd.DataFrame
    message_word_lengths: list[int]
    series_lengths: list[int]


def analyze_author(chat: pd.DataFrame, author: str) -> Analysis:
    selected = assign_series(chat)
    selected = selected.loc[selected["author"].eq(author)].copy()
    if selected.empty:
        raise ValueError(f"Нет текстовых сообщений автора: {author}")
    selected["word_count"] = selected["text"].map(count_words)
    selected["lowercase_start"] = selected["text"].map(starts_lowercase)
    selected["no_standard_final_punctuation"] = ~selected["text"].map(has_final_punctuation)
    selected["bracket_ending"] = selected["text"].map(lambda s: bool(re.search(r"\)+$", s.rstrip())))
    selected["multi_sentence"] = selected["text"].map(is_multi_sentence)
    series = selected.groupby("series_id", sort=False).agg(
        author=("author", "first"), start=("datetime", "first"), end=("datetime", "last"),
        series_length=("message_id", "size"), total_words=("word_count", "sum"),
    ).reset_index()
    lengths = selected["word_count"].tolist()
    series_lengths = series["series_length"].tolist()
    multi_words = selected.loc[selected["series_length"].ge(2), "word_count"].tolist()
    profile = {
        "source_file": selected["source_file"].iloc[0], "author": author,
        "message_count": len(selected),
        "median_words_per_message": statistics.median(lengths),
        "mean_words_per_message": statistics.mean(lengths),
        "one_word_ratio": sum(n == 1 for n in lengths) / len(lengths),
        "short_message_ratio": sum(n <= 3 for n in lengths) / len(lengths),
        "median_series_length": statistics.median(series_lengths),
        "mean_series_length": statistics.mean(series_lengths),
        "long_series_ratio": sum(n >= 3 for n in series_lengths) / len(series_lengths),
        "no_standard_final_punctuation_ratio": float(selected["no_standard_final_punctuation"].mean()),
        "bracket_ending_ratio": float(selected["bracket_ending"].mean()),
        "lowercase_start_ratio": float(selected["lowercase_start"].mean()),
        "multi_sentence_ratio": float(selected["multi_sentence"].mean()),
        "mean_words_in_multi_message_series": statistics.mean(multi_words) if multi_words else None,
    }
    return Analysis(profile, selected, series, lengths, series_lengths)

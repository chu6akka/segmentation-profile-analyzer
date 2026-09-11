"""Deterministic feature extraction, entirely independent of GUI."""
from dataclasses import dataclass
import re
import statistics

import pandas as pd

from segmentation import assign_series

URL = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
WORD = re.compile(r"(?:https?://|www\.)\S+|[^\W_]+(?:[-’'][^\W_]+)*", re.UNICODE | re.IGNORECASE)
SEGMENTATION_METRICS = {
    "message_count": "Сообщений",
    "median_words_per_message": "Медиана слов в сообщении",
    "mean_words_per_message": "Среднее слов в сообщении",
    "q1_words_per_message": "Q1 длины сообщения",
    "q3_words_per_message": "Q3 длины сообщения",
    "iqr_words_per_message": "IQR длины сообщения",
    "one_word_ratio": "Однословных сообщений",
    "short_message_ratio": "Коротких сообщений (≤3 слов)",
    "series_count": "Количество серий",
    "median_series_length": "Медиана длины серии",
    "mean_messages_per_series": "Среднее число сообщений в серии",
    "single_message_series_ratio": "Одиночные серии, %",
    "long_series_ratio": "Серий ≥3 сообщений",
}
BOUNDARY_METRICS = {
    "no_standard_final_punctuation_ratio": "Без стандартной конечной пунктуации",
    "lowercase_start_ratio": "Со строчной буквы",
    "bracket_ending_ratio": "Со скобочным окончанием",
}
METRICS = {**SEGMENTATION_METRICS, **BOUNDARY_METRICS}
RATIO_METRICS = {key for key in METRICS if key.endswith("_ratio")}


def count_words(text: str) -> int:
    return len(WORD.findall(text))


def starts_lowercase(text: str) -> bool:
    # A URL is not the beginning of an author's lexical text.
    return next((char.islower() for char in URL.sub("", text) if char.isalpha()), False)


def has_letter(text: str) -> bool:
    return any(char.isalpha() for char in URL.sub("", text))


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


def analyze_author(chat: pd.DataFrame, author: str, threshold_minutes: int = 10) -> Analysis:
    selected = assign_series(chat, threshold_minutes)
    selected = selected.loc[selected["author"].eq(author)].copy()
    if selected.empty:
        raise ValueError(f"Нет текстовых сообщений автора: {author}")
    selected["word_count"] = selected["text"].map(count_words)
    selected["lowercase_start"] = selected["text"].map(starts_lowercase)
    selected["no_standard_final_punctuation"] = ~selected["text"].map(has_final_punctuation)
    selected["bracket_ending"] = selected["text"].map(lambda s: bool(re.search(r"\)+$", s.rstrip())))
    selected["has_letter"] = selected["text"].map(has_letter)
    series = selected.groupby("series_id", sort=False).agg(
        author=("author", "first"), start_datetime=("datetime", "first"), end_datetime=("datetime", "last"),
        message_count=("message_id", "size"), total_words=("word_count", "sum"),
    ).reset_index()
    series["mean_words_per_message"] = series["total_words"] / series["message_count"]
    series["duration_seconds"] = (series["end_datetime"] - series["start_datetime"]).dt.total_seconds()
    series["threshold_minutes"] = threshold_minutes
    lengths = selected["word_count"].tolist()
    series_lengths = series["message_count"].tolist()
    q1, q3 = selected["word_count"].quantile([.25, .75]).tolist()
    letter_rows = selected.loc[selected["has_letter"], "lowercase_start"]
    profile = {
        "source_file": selected["source_file"].iloc[0], "author": author,
        "message_count": len(selected),
        "median_words_per_message": statistics.median(lengths),
        "mean_words_per_message": statistics.mean(lengths),
        "q1_words_per_message": q1,
        "q3_words_per_message": q3,
        "iqr_words_per_message": q3 - q1,
        "one_word_ratio": sum(n == 1 for n in lengths) / len(lengths),
        "short_message_ratio": sum(n <= 3 for n in lengths) / len(lengths),
        "series_count": len(series_lengths),
        "median_series_length": statistics.median(series_lengths),
        "mean_messages_per_series": statistics.mean(series_lengths),
        "single_message_series_ratio": sum(n == 1 for n in series_lengths) / len(series_lengths),
        "long_series_ratio": sum(n >= 3 for n in series_lengths) / len(series_lengths),
        "no_standard_final_punctuation_ratio": float(selected["no_standard_final_punctuation"].mean()),
        "bracket_ending_ratio": float(selected["bracket_ending"].mean()),
        "lowercase_start_ratio": float(letter_rows.mean()) if len(letter_rows) else None,
        "threshold_minutes": threshold_minutes,
    }
    return Analysis(profile, selected, series, lengths, series_lengths)


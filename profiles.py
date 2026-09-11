"""Descriptive statistics across profiles; no authorship inference."""
import statistics
import pandas as pd

from features import METRICS


def aggregate_profiles(analyses) -> pd.DataFrame:
    rows = []
    for key in METRICS:
        values = [a.profile[key] for a in analyses if a.profile.get(key) is not None]
        if not values:
            continue
        rows.append({"parameter": key, "mean_across_profiles": statistics.mean(values),
                     "median_across_profiles": statistics.median(values), "minimum": min(values),
                     "maximum": max(values), "range": max(values) - min(values)})
    return pd.DataFrame(rows)


def within_author_comparison(analyses) -> pd.DataFrame:
    if len(analyses) not in (2, 3):
        raise ValueError("Для внутриавторского сравнения нужны 2 или 3 профиля")
    rows = []
    for key in METRICS:
        values = [a.profile.get(key) for a in analyses]
        valid = [v for v in values if v is not None]
        row = {"parameter": key, **{f"profile_{i + 1}": v for i, v in enumerate(values)}}
        row.update({"minimum": min(valid) if valid else None, "maximum": max(valid) if valid else None,
                    "range": max(valid) - min(valid) if valid else None})
        rows.append(row)
    return pd.DataFrame(rows)


def threshold_sensitivity(chat, author):
    from features import analyze_author
    keys = ("series_count", "median_series_length", "mean_messages_per_series",
            "single_message_series_ratio", "long_series_ratio")
    analyses = {n: analyze_author(chat, author, n) for n in (5, 10, 30)}
    table = pd.DataFrame([{"parameter": key, **{f"threshold_{n}": a.profile[key]
                          for n, a in analyses.items()}} for key in keys])
    return analyses, table


def variability_comparison(author_a, author_b) -> pd.DataFrame:
    if len(author_a) < 2 or len(author_b) < 2:
        raise ValueError("Нужно минимум по два профиля каждого автора")
    a, b = aggregate_profiles(author_a).set_index("parameter"), aggregate_profiles(author_b).set_index("parameter")
    return pd.DataFrame([{"parameter": key, "within_author_a_range": a.at[key, "range"],
                          "within_author_b_range": b.at[key, "range"],
                          "difference_between_means": abs(a.at[key, "mean_across_profiles"] - b.at[key, "mean_across_profiles"])}
                         for key in METRICS if key in a.index and key in b.index])


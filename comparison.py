import pandas as pd

from features import Analysis, METRICS


def compare_profiles(a: Analysis, b: Analysis) -> pd.DataFrame:
    rows = []
    for key in METRICS:
        left, right = a.profile[key], b.profile[key]
        difference = abs(left - right) if left is not None and right is not None else None
        rows.append({"parameter": key, "author_a": left, "author_b": right,
                     "absolute_difference": difference})
    return pd.DataFrame(rows)


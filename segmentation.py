"""Segment the complete conversation BEFORE selecting the target author."""
import pandas as pd


def assign_series(messages: pd.DataFrame, threshold_minutes: int = 10) -> pd.DataFrame:
    if threshold_minutes <= 0:
        raise ValueError("Порог серии должен быть больше нуля")
    result = messages.copy()
    if result.empty:
        for column in ("series_id", "position_in_series", "series_length"):
            result[column] = pd.Series(dtype="int64")
        result["time_gap_from_previous_same_author"] = pd.Series(dtype="float64")
        return result
    if "datetime" in result:
        previous_same = result.groupby("author", sort=False)["datetime"].shift()
        result["time_gap_from_previous_same_author"] = (
            pd.to_datetime(result["datetime"]) - pd.to_datetime(previous_same)
        ).dt.total_seconds()
        adjacent_gap = pd.to_datetime(result["datetime"]).diff().dt.total_seconds()
    else:
        result["time_gap_from_previous_same_author"] = float("nan")
        adjacent_gap = pd.Series(float("nan"), index=result.index)
    boundary = result["author"].ne(result["author"].shift())
    if "_turn_id" in result:
        boundary |= result["_turn_id"].ne(result["_turn_id"].shift())
    boundary |= adjacent_gap.gt(threshold_minutes * 60)
    result["series_id"] = boundary.cumsum().astype(int)
    groups = result.groupby("series_id", sort=False)
    result["position_in_series"] = groups.cumcount() + 1
    result["series_length"] = groups["message_id"].transform("size")
    return result


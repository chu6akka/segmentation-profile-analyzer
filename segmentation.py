"""Segment the complete conversation BEFORE selecting the target author."""
import pandas as pd


def assign_series(messages: pd.DataFrame) -> pd.DataFrame:
    result = messages.copy()
    if result.empty:
        for column in ("series_id", "position_in_series", "series_length"):
            result[column] = pd.Series(dtype="int64")
        return result
    boundary = result["author"].ne(result["author"].shift())
    if "_turn_id" in result:
        boundary |= result["_turn_id"].ne(result["_turn_id"].shift())
    result["series_id"] = boundary.cumsum().astype(int)
    groups = result.groupby("series_id", sort=False)
    result["position_in_series"] = groups.cumcount() + 1
    result["series_length"] = groups["message_id"].transform("size")
    return result

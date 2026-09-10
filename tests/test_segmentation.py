import pandas as pd

from parser import parse_chat
from segmentation import assign_series


def test_series_and_positions():
    frame = pd.DataFrame({"author": ["A", "A", "A", "B", "A", "A"], "message_id": range(6)})
    result = assign_series(frame)
    assert result.series_id.tolist() == [1, 1, 1, 2, 3, 3]
    assert result.position_in_series.tolist() == [1, 2, 3, 1, 1, 2]
    assert result.series_length.tolist() == [3, 3, 3, 1, 2, 2]


def test_excluded_other_participant_still_breaks_series(tmp_path):
    path = tmp_path / "chat.txt"
    path.write_text("[11.06.2026 14:12] A: привет\n[11.06.2026 14:13] B: [стикер]\n[11.06.2026 14:14] A: ау", encoding="utf-8")
    assert assign_series(parse_chat(str(path))).series_length.tolist() == [1, 1]


def test_empty():
    result = assign_series(pd.DataFrame(columns=["author", "message_id"]))
    assert result.empty and "series_length" in result

from parser import parse_chat


def test_single_digit_hour_and_file_order(tmp_path):
    path = tmp_path / "chat.txt"
    path.write_text("[10.09.2026 9:33] Участник: Привет\n[30.06.2026 9:47] Участник: Пока", encoding="utf-8")
    df = parse_chat(str(path))
    assert len(df) == 2
    assert df.iloc[0].datetime.hour == 9
    assert df.attrs["diagnostics"]["chronology_inversions"] == 1

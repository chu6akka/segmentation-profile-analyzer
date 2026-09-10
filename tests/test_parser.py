import pytest

from parser import parse_chat


def parse(tmp_path, text):
    path = tmp_path / "chat.txt"
    path.write_text(text, encoding="utf-8")
    return parse_chat(str(path))


def test_ordinary_author_time_and_original_text(tmp_path):
    df = parse(tmp_path, "[11.06.2026 14:12] Автор А: ну че завтра 😁 https://x.ru")
    assert len(df) == 1
    row = df.iloc[0]
    assert row.author == "Автор А"
    assert row.text == "ну че завтра 😁 https://x.ru"
    assert row.datetime.isoformat() == "2026-06-11T14:12:00"
    assert not row.is_reply


def test_reply_and_quoted_text(tmp_path):
    df = parse(tmp_path, "[11.06.2026 14:18] Автор А в ответ Автор Б:\n> цитируемое сообщение\n  > ещё цитата\nлюбой хука плейс")
    row = df.iloc[0]
    assert row.author == "Автор А"
    assert row.is_reply and row.reply_to_author == "Автор Б"
    assert row.text == "любой хука плейс"
    assert "цитируемое" in row.quoted_text


def test_multiline_and_blanks(tmp_path):
    df = parse(tmp_path, "[11.06.2026 14:12] A: Строка 1\n\nСтрока 2\n[11.06.2026 14:13] B: да")
    assert df.iloc[0].text == "Строка 1\n\nСтрока 2"
    assert len(df) == 2


def test_exclusions_and_caption(tmp_path):
    df = parse(tmp_path, "служебный заголовок\n[11.06.2026 14:12] A:\n[11.06.2026 14:13] A: > цитата\n[11.06.2026 14:14] A: [стикер]\n[11.06.2026 14:15] A: [изображение]\nподпись\n[11.06.2026 14:16] участник вышел\n--- конец экспорта ---")
    assert df.text.tolist() == ["подпись"]
    assert df.attrs["diagnostics"]["excluded_messages"] == 3


def test_invalid_date(tmp_path):
    with pytest.raises(ValueError, match="Некорректная дата"):
        parse(tmp_path, "[31.02.2026 14:12] A: привет")


def test_cp1251_and_empty(tmp_path):
    path = tmp_path / "old.txt"
    path.write_bytes("[11.06.2026 14:12] Участник: привет".encode("cp1251"))
    assert parse_chat(str(path)).iloc[0].author == "Участник"
    assert parse(tmp_path, "").empty

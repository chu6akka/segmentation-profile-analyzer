import pytest

from features import analyze_author, count_words, has_final_punctuation, is_multi_sentence, starts_lowercase
from parser import parse_chat


@pytest.mark.parametrize("text,expected", [("ну че завтра", 3), ("😀 ))", 0), ("кто-то 123", 2), ("https://x.ru/a?q=2 привет", 2), ("don't ну_да", 3)])
def test_words(text, expected):
    assert count_words(text) == expected


@pytest.mark.parametrize("text,expected", [("😁 123 привет", True), ("https://x.ru Привет", False), ("123 😀", False), ("…Я", False), ("www.x.ru ну", True)])
def test_lowercase(text, expected):
    assert starts_lowercase(text) is expected


@pytest.mark.parametrize("text,expected", [("да.", True), ("да… ", True), ("да?!", True), ("да))", False), ("да!😀", False), ("", False)])
def test_final(text, expected):
    assert has_final_punctuation(text) is expected


@pytest.mark.parametrize("text,expected", [("Да?!", False), ("Да...", False), ("Да. Нет!", True), ("https://a.ru/x.y да!", False)])
def test_sentences(text, expected):
    assert is_multi_sentence(text) is expected


def test_exact_profile(tmp_path):
    path = tmp_path / "chat.txt"
    path.write_text("\n".join([
        "[11.06.2026 14:12] A: привет",
        "[11.06.2026 14:12] A: ты где",
        "[11.06.2026 14:12] A: Ау!",
        "[11.06.2026 14:13] B: иду",
        "[11.06.2026 14:14] A: Да. Хорошо!",
        "[11.06.2026 14:14] A: ну ок))",
        "[11.06.2026 14:15] B: пока",
        "[11.06.2026 14:16] A: это ровно четыре слова",
    ]), encoding="utf-8")
    result = analyze_author(parse_chat(str(path)), "A")
    p = result.profile
    assert result.message_word_lengths == [1, 2, 1, 2, 2, 4]
    assert result.series_lengths == [3, 2, 1]
    expected = {"message_count": 6, "median_words_per_message": 2,
                "mean_words_per_message": 2, "one_word_ratio": 2/6,
                "short_message_ratio": 5/6, "median_series_length": 2,
                "mean_series_length": 2, "long_series_ratio": 1/3,
                "no_standard_final_punctuation_ratio": 4/6,
                "bracket_ending_ratio": 1/6, "lowercase_start_ratio": 4/6,
                "multi_sentence_ratio": 1/6, "mean_words_in_multi_message_series": 8/5}
    for key, value in expected.items():
        assert p[key] == pytest.approx(value), key


def test_no_multi_message_series(tmp_path):
    path = tmp_path / "chat.txt"
    path.write_text("[11.06.2026 14:12] A: 😀", encoding="utf-8")
    df = parse_chat(str(path))
    result = analyze_author(df, "A")
    assert result.profile["mean_words_in_multi_message_series"] is None
    assert result.profile["short_message_ratio"] == 1
    with pytest.raises(ValueError):
        analyze_author(df, "missing")

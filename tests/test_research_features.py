import pytest

from comparison import compare_profiles
from features import analyze_author
from parser import parse_chat
from profiles import aggregate_profiles, threshold_sensitivity, within_author_comparison


def make_chat(tmp_path, name="chat.txt"):
    path = tmp_path / name
    path.write_text("\n".join([
        "[11.06.2026 12:00] A: один",
        "[11.06.2026 12:01] A: два слова",
        "[11.06.2026 12:25] A: три слова здесь",
        "[11.06.2026 12:26] B: ответ",
        "[11.06.2026 12:27] A: четыре слова теперь здесь",
    ]), encoding="utf-8")
    return parse_chat(path)


def test_time_and_participant_boundaries(tmp_path):
    result = analyze_author(make_chat(tmp_path), "A", 10)
    assert result.series_lengths == [2, 1, 1]
    assert result.profile["series_count"] == 3
    assert result.profile["median_series_length"] == 1
    assert result.profile["mean_messages_per_series"] == pytest.approx(4 / 3)
    assert result.profile["single_message_series_ratio"] == pytest.approx(2 / 3)
    assert result.profile["long_series_ratio"] == 0
    assert result.messages.time_gap_from_previous_same_author.tolist()[1:] == [60, 1440, 120]


def test_quartiles_ranges_and_differences(tmp_path):
    chat = make_chat(tmp_path)
    a = analyze_author(chat, "A")
    b = analyze_author(chat, "B")
    assert (a.profile["q1_words_per_message"], a.profile["q3_words_per_message"], a.profile["iqr_words_per_message"]) == (1.75, 3.25, 1.5)
    within = within_author_comparison([a, a])
    assert within["range"].dropna().eq(0).all()
    assert aggregate_profiles([a, a])["range"].eq(0).all()
    assert compare_profiles(a, b).absolute_difference.notna().all()
    analyses, table = threshold_sensitivity(chat, "A")
    assert set(analyses) == {5, 10, 30}
    assert table.shape == (5, 4)


def test_bilingual_replies_media_quotes_and_boundaries(tmp_path):
    path = tmp_path / "formats.txt"
    path.write_text("\n".join([
        "[11.06.2026 12:00] A in reply to B:", "> quote", "😁ну да))",
        "[11.06.2026 12:01] B в ответ A: Да.",
        "[11.06.2026 12:02] A: [ Голосовое сообщение ]",
        "[11.06.2026 12:03] A: [ Photo ]",
        "[11.06.2026 12:04] A: ???",
    ]), encoding="utf-8")
    chat = parse_chat(path)
    assert chat.iloc[0].is_reply and chat.iloc[0].reply_to_author == "B"
    assert chat.iloc[1].is_reply and chat.iloc[1].reply_to_author == "A"
    assert "quote" in chat.iloc[0].quoted_text and "quote" not in chat.iloc[0].text
    assert chat.text.tolist() == ["😁ну да))", "Да.", "???"]
    result = analyze_author(chat, "A")
    assert result.profile["lowercase_start_ratio"] == 1
    assert result.profile["bracket_ending_ratio"] == .5
    assert result.profile["no_standard_final_punctuation_ratio"] == .5


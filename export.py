"""CSV and literal-string Excel exports; no formula interpretation of chat text."""
from pathlib import Path
import os
import tempfile

import pandas as pd

from comparison import compare_profiles
from profiles import aggregate_profiles, threshold_sensitivity, within_author_comparison, variability_comparison
from features import Analysis


def export_csv(analysis: Analysis, path: str | Path) -> None:
    pd.DataFrame([analysis.profile]).to_csv(path, index=False, encoding="utf-8-sig")


def _write_sheets(sheets: dict, path: str | Path) -> None:
    target = Path(path)
    descriptor, temporary = tempfile.mkstemp(suffix=".xlsx", dir=target.parent)
    os.close(descriptor)
    try:
        _write_workbook(sheets, temporary)
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _write_workbook(sheets: dict, path: str | Path) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, frame in sheets.items():
            # Excel otherwise silently truncates cells longer than 32767 chars.
            if any(isinstance(value, str) and len(value) > 32767
                   for value in frame.to_numpy().ravel()):
                raise ValueError("Текст превышает предел Excel (32767 символов в ячейке).")
            frame.to_excel(writer, sheet_name=name, index=False)
            sheet = writer.sheets[name]
            for row in sheet.iter_rows():
                for cell in row:
                    if isinstance(cell.value, str):
                        cell.data_type = "s"
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions


def export_xlsx(analysis: Analysis, path: str | Path) -> None:
    _write_sheets({"Profile": pd.DataFrame([analysis.profile]),
                   "Messages": analysis.messages.drop(columns=["_turn_id"], errors="ignore"),
                   "Series": analysis.series}, path)


def export_comparison_xlsx(a: Analysis, b: Analysis, path: str | Path) -> None:
    _write_sheets({"Author_A": pd.DataFrame([a.profile]),
                   "Author_B": pd.DataFrame([b.profile]),
                   "Between_Author_Comparison": compare_profiles(a, b)}, path)


def export_within_author_xlsx(analyses, path: str | Path) -> None:
    sheets = {f"Profile_{i + 1}": pd.DataFrame([a.profile]) for i, a in enumerate(analyses)}
    sheets["Within_Author_Comparison"] = within_author_comparison(analyses)
    sheets["Aggregated_Profile"] = aggregate_profiles(analyses)
    _write_sheets(sheets, path)


def export_threshold_xlsx(chat, author, path: str | Path) -> None:
    analyses, comparison = threshold_sensitivity(chat, author)
    sheets = {f"Threshold_{n}": pd.DataFrame([a.profile]) for n, a in analyses.items()}
    sheets["Threshold_Comparison"] = comparison
    _write_sheets(sheets, path)


def export_variability_xlsx(author_a, author_b, path: str | Path) -> None:
    _write_sheets({"Author_A_Aggregated": aggregate_profiles(author_a),
                   "Author_B_Aggregated": aggregate_profiles(author_b),
                   "Variability_Comparison": variability_comparison(author_a, author_b)}, path)


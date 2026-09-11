import pandas as pd
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableView, QLabel, QFileDialog, QMessageBox, QComboBox

from comparison import compare_profiles
from export import export_comparison_xlsx, export_within_author_xlsx
from features import analyze_author, METRICS
from profiles import within_author_comparison
from ui.common import FilePicker, set_table


class ComparisonTab(QWidget):
    def __init__(self):
        super().__init__()
        self.results = None
        layout = QVBoxLayout(self)
        self.mode = QComboBox()
        self.mode.addItems(["Межавторское сравнение", "Внутриавторское сравнение"])
        self.mode.currentTextChanged.connect(self._mode_changed)
        layout.addWidget(self.mode)
        self.a, self.b, self.c = FilePicker("профиль 1"), FilePicker("профиль 2"), FilePicker("профиль 3 (необязательно)")
        for picker in (self.a, self.b, self.c):
            layout.addWidget(picker)
            picker.changed.connect(self.invalidate)
        row = QHBoxLayout()
        self.analyze_button = QPushButton("Сравнить параметры")
        self.analyze_button.clicked.connect(self.analyze)
        self.csv_button = QPushButton("Экспорт CSV")
        self.csv_button.clicked.connect(lambda: self.save(False))
        self.xlsx_button = QPushButton("Экспорт XLSX")
        self.xlsx_button.clicked.connect(lambda: self.save(True))
        for button in (self.analyze_button, self.csv_button, self.xlsx_button):
            row.addWidget(button)
        row.addStretch()
        layout.addLayout(row)
        self.status = QLabel("Долевые различия интерпретируются в процентных пунктах. Вывод об авторстве и общий показатель сходства не рассчитываются.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.table = QTableView()
        layout.addWidget(self.table)
        self._mode_changed()

    def _mode_changed(self):
        self.c.setVisible(self.mode.currentText().startswith("Внутри"))
        self.invalidate()

    def invalidate(self):
        self.results = None
        self.analyze_button.setEnabled(self.a.chat is not None and self.b.chat is not None)
        self.csv_button.setEnabled(False)
        self.xlsx_button.setEnabled(False)
        set_table(self.table, pd.DataFrame())

    def analyze(self):
        try:
            analyses = [analyze_author(p.chat, p.author) for p in (self.a, self.b) if p.chat is not None]
            if self.mode.currentText().startswith("Внутри"):
                if self.c.chat is not None:
                    analyses.append(analyze_author(self.c.chat, self.c.author))
                comparison = within_author_comparison(analyses)
            else:
                comparison = compare_profiles(*analyses[:2])
            shown = comparison.copy()
            shown["parameter"] = shown["parameter"].map(METRICS)
            shown = shown.rename(columns={"parameter": "Параметр", "author_a": "Автор A", "author_b": "Автор B", "absolute_difference": "Абсолютная разница", "minimum": "Минимум", "maximum": "Максимум", "range": "Размах"})
            set_table(self.table, shown)
            self.results = analyses
            self.csv_button.setEnabled(True)
            self.xlsx_button.setEnabled(True)
        except Exception as exc:
            QMessageBox.warning(self, "Ошибка сравнения", str(exc))

    def save(self, xlsx):
        if not self.results:
            return
        suffix = "xlsx" if xlsx else "csv"
        path, _ = QFileDialog.getSaveFileName(self, "Экспорт сравнения", f"comparison.{suffix}", f"{suffix.upper()} (*.{suffix})")
        if not path:
            return
        if not path.lower().endswith(f".{suffix}"):
            path += f".{suffix}"
        try:
            within = self.mode.currentText().startswith("Внутри")
            if xlsx:
                if within:
                    export_within_author_xlsx(self.results, path)
                else:
                    export_comparison_xlsx(*self.results[:2], path)
            else:
                frame = within_author_comparison(self.results) if within else compare_profiles(*self.results[:2])
                frame.to_csv(path, index=False, encoding="utf-8-sig")
        except Exception as exc:
            QMessageBox.warning(self, "Ошибка экспорта", str(exc))


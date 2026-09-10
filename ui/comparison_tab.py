import pandas as pd
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableView, QLabel, QFileDialog, QMessageBox

from comparison import compare_profiles
from export import export_comparison_xlsx
from features import analyze_author, METRICS
from ui.common import FilePicker, set_table


class ComparisonTab(QWidget):
    def __init__(self):
        super().__init__()
        self.results = None
        layout = QVBoxLayout(self)
        self.a, self.b = FilePicker("файл A"), FilePicker("файл B")
        for picker in (self.a, self.b):
            layout.addWidget(picker)
            picker.changed.connect(self.invalidate)
        row = QHBoxLayout()
        self.analyze_button = QPushButton("Сравнить параметры")
        self.analyze_button.clicked.connect(self.analyze)
        self.csv_button = QPushButton("Экспорт сравнения CSV")
        self.csv_button.clicked.connect(lambda: self.save(False))
        self.xlsx_button = QPushButton("Экспорт сравнения XLSX")
        self.xlsx_button.clicked.connect(lambda: self.save(True))
        for button in (self.analyze_button, self.csv_button, self.xlsx_button):
            row.addWidget(button)
        row.addStretch()
        layout.addLayout(row)
        self.status = QLabel("Доли представлены от 0 до 1; абсолютная разница — в тех же единицах. Общий показатель совпадения не рассчитывается.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.table = QTableView()
        layout.addWidget(self.table)
        self.invalidate()

    def invalidate(self):
        self.results = None
        self.analyze_button.setEnabled(self.a.chat is not None and self.b.chat is not None)
        self.csv_button.setEnabled(False)
        self.xlsx_button.setEnabled(False)
        set_table(self.table, pd.DataFrame(columns=["Параметр", "Профиль A", "Профиль B", "Абсолютная разница"]))

    def analyze(self):
        try:
            left = analyze_author(self.a.chat, self.a.author)
            right = analyze_author(self.b.chat, self.b.author)
            comparison = compare_profiles(left, right)
            comparison["parameter"] = comparison["parameter"].map(METRICS)
            self.results = left, right
            shown = comparison.rename(columns={"parameter": "Параметр", "profile_a": "Профиль A", "profile_b": "Профиль B", "absolute_difference": "Абсолютная разница"})
            set_table(self.table, shown)
            self.table.setColumnWidth(0, 620)
            self.csv_button.setEnabled(True)
            self.xlsx_button.setEnabled(True)
        except Exception as exc:
            QMessageBox.warning(self, "Ошибка сравнения", str(exc))

    def save(self, xlsx):
        if self.results is None:
            return
        suffix = "xlsx" if xlsx else "csv"
        path, _ = QFileDialog.getSaveFileName(self, "Экспорт сравнения", f"comparison.{suffix}", f"{suffix.upper()} (*.{suffix})")
        if not path:
            return
        try:
            if not path.lower().endswith(f".{suffix}"):
                path += f".{suffix}"
            if xlsx:
                export_comparison_xlsx(*self.results, path)
            else:
                compare_profiles(*self.results).to_csv(path, index=False, encoding="utf-8-sig")
            QMessageBox.information(self, "Экспорт завершён", path)
        except Exception as exc:
            QMessageBox.warning(self, "Ошибка экспорта", str(exc))

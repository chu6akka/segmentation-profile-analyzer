import pandas as pd
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableView, QFileDialog, QMessageBox

from export import export_threshold_xlsx
from features import METRICS
from profiles import threshold_sensitivity
from ui.common import FilePicker, set_table


class ThresholdTab(QWidget):
    def __init__(self):
        super().__init__()
        self.result = None
        layout = QVBoxLayout(self)
        self.picker = FilePicker()
        layout.addWidget(self.picker)
        row = QHBoxLayout()
        run = QPushButton("Рассчитать для 5, 10 и 30 минут")
        run.clicked.connect(self.analyze)
        save = QPushButton("Экспорт XLSX")
        save.clicked.connect(self.export)
        row.addWidget(run); row.addWidget(save); row.addStretch()
        layout.addLayout(row)
        self.table = QTableView(); layout.addWidget(self.table)

    def analyze(self):
        if self.picker.chat is None:
            return
        try:
            self.result = threshold_sensitivity(self.picker.chat, self.picker.author)
            shown = self.result[1].copy()
            shown["parameter"] = shown["parameter"].map(METRICS)
            set_table(self.table, shown.rename(columns={"parameter": "Параметр", "threshold_5": "5 мин", "threshold_10": "10 мин", "threshold_30": "30 мин"}))
        except Exception as exc:
            QMessageBox.warning(self, "Ошибка", str(exc))

    def export(self):
        if self.result is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Экспорт", "thresholds.xlsx", "XLSX (*.xlsx)")
        if path:
            export_threshold_xlsx(self.picker.chat, self.picker.author, path if path.endswith(".xlsx") else path + ".xlsx")


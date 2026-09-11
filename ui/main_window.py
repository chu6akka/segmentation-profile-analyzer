import pandas as pd
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget, QTableView, QLabel, QFileDialog, QMessageBox, QComboBox

from export import export_csv, export_xlsx
from features import analyze_author
from ui.charts import Charts
from ui.common import FilePicker, set_table
from ui.comparison_tab import ComparisonTab
from ui.profile_tab import ProfileTab
from ui.threshold_tab import ThresholdTab
from ui.corpus_tab import CorpusTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Анализатор сегментации переписки")
        self.resize(1180, 850)
        self.analysis = None
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        title = QLabel("Профиль сегментации письменной речи")
        title.setStyleSheet("font-size: 22px; font-weight: 600; padding: 8px;")
        layout.addWidget(title)
        self.picker = FilePicker()
        layout.addWidget(self.picker)
        row = QHBoxLayout()
        row.addWidget(QLabel("Порог серии:"))
        self.threshold = QComboBox()
        self.threshold.addItems(["5 мин", "10 мин", "30 мин"])
        self.threshold.setCurrentText("10 мин")
        self.threshold.currentTextChanged.connect(self.invalidate)
        row.addWidget(self.threshold)
        self.analyze_button = QPushButton("Анализировать")
        self.analyze_button.clicked.connect(self.analyze)
        self.csv_button = QPushButton("Экспорт CSV")
        self.csv_button.clicked.connect(lambda: self.save(False))
        self.xlsx_button = QPushButton("Экспорт XLSX")
        self.xlsx_button.clicked.connect(lambda: self.save(True))
        for button in (self.analyze_button, self.csv_button, self.xlsx_button):
            row.addWidget(button)
        row.addStretch()
        layout.addLayout(row)
        self.tabs = QTabWidget()
        self.profile = ProfileTab()
        self.messages = QTableView()
        self.charts = Charts()
        self.comparison = ComparisonTab()
        self.threshold_tab = ThresholdTab()
        self.corpus = CorpusTab()
        for widget, label in [(self.profile, "Профиль"), (self.messages, "Сообщения"), (self.charts, "Графики"), (self.comparison, "Сравнение профилей"), (self.threshold_tab, "Проверка порога серии"), (self.corpus, "Корпус")]:
            self.tabs.addTab(widget, label)
        layout.addWidget(self.tabs, 1)
        note = QLabel("Приложение не осуществляет автоматическую идентификацию автора. Получаемые показатели предназначены для исследовательского и экспертно-аналитического использования и требуют интерпретации специалистом.")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.picker.changed.connect(self.invalidate)
        self.invalidate()

    def invalidate(self):
        self.analysis = None
        self.analyze_button.setEnabled(self.picker.chat is not None)
        self.csv_button.setEnabled(False)
        self.xlsx_button.setEnabled(False)
        self.profile.clear()
        set_table(self.messages, pd.DataFrame())
        self.charts.clear()
        self.statusBar().showMessage("Выберите файл и автора для анализа")

    def analyze(self):
        try:
            result = analyze_author(self.picker.chat, self.picker.author, int(self.threshold.currentText().split()[0]))
            self.profile.display(result)
            columns = {"message_id": "message_id", "datetime": "datetime", "author": "author", "text": "text", "word_count": "word_count", "series_id": "series_id", "position_in_series": "position_in_series", "series_length": "series_length", "time_gap_from_previous_same_author": "time_gap_from_previous_same_author", "is_reply": "is_reply", "reply_to_author": "reply_to_author"}
            set_table(self.messages, result.messages[list(columns)].rename(columns=columns))
            self.charts.display(result)
            self.analysis = result
            self.csv_button.setEnabled(True)
            self.xlsx_button.setEnabled(True)
            self.statusBar().showMessage(f"Рассчитано: {result.profile['message_count']} сообщений, {len(result.series)} серий")
        except Exception as exc:
            QMessageBox.warning(self, "Ошибка анализа", str(exc))

    def save(self, xlsx):
        if self.analysis is None:
            return
        suffix = "xlsx" if xlsx else "csv"
        path, _ = QFileDialog.getSaveFileName(self, "Экспорт профиля", f"profile.{suffix}", f"{suffix.upper()} (*.{suffix})")
        if not path:
            return
        try:
            if not path.lower().endswith(f".{suffix}"):
                path += f".{suffix}"
            (export_xlsx if xlsx else export_csv)(self.analysis, path)
            self.statusBar().showMessage(f"Сохранено: {path}")
        except Exception as exc:
            QMessageBox.warning(self, "Ошибка экспорта", str(exc))


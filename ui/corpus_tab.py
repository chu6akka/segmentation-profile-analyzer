from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox

from parser import parse_chat


class CorpusTab(QWidget):
    COLUMNS = ["corpus_id", "author", "interlocutor", "source_file", "message_count", "date_start", "date_end", "notes"]

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        button = QPushButton("Добавить файлы TXT")
        button.clicked.connect(self.add_files)
        layout.addWidget(button)
        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        layout.addWidget(self.table)

    def add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Добавить файлы корпуса", "", "Переписка (*.txt)")
        for path in paths:
            try:
                chat = parse_chat(path)
                authors = list(chat.author.unique())
                row = self.table.rowCount(); self.table.insertRow(row)
                values = [f"C{row + 1:02d}", authors[0] if authors else "", authors[1] if len(authors) > 1 else "",
                          Path(path).name, str(len(chat)), str(chat.datetime.min()), str(chat.datetime.max()), ""]
                for column, value in enumerate(values):
                    self.table.setItem(row, column, QTableWidgetItem(value))
            except Exception as exc:
                QMessageBox.warning(self, "Ошибка корпуса", f"{Path(path).name}: {exc}")


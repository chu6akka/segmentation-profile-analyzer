from pathlib import Path

import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, QSortFilterProxyModel, Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                               QComboBox, QFileDialog, QMessageBox, QTableView, QHeaderView)

from parser import parse_chat


class FrameModel(QAbstractTableModel):
    def __init__(self, frame, parent=None):
        super().__init__(parent)
        self.frame = frame

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.frame)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.frame.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        value = self.frame.iat[index.row(), index.column()]
        if role == Qt.ItemDataRole.UserRole:
            if pd.isna(value):
                return ""
            if isinstance(value, (pd.Timestamp,)):
                return value.isoformat()
            return value.item() if hasattr(value, "item") else value
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole):
            if pd.isna(value):
                return "—"
            if isinstance(value, pd.Timestamp):
                return value.strftime("%d.%m.%Y %H:%M:%S")
            if isinstance(value, float):
                return f"{value:.4f}".rstrip("0").rstrip(".")
            return str(value)
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return str(self.frame.columns[section]) if orientation == Qt.Orientation.Horizontal else str(section + 1)
        return None


def set_table(table: QTableView, frame: pd.DataFrame):
    old_proxy = table.model()
    proxy = QSortFilterProxyModel(table)
    proxy.setSourceModel(FrameModel(frame, proxy))
    proxy.setSortRole(Qt.ItemDataRole.UserRole)
    table.setModel(proxy)
    table.setSortingEnabled(True)
    table.sortByColumn(-1, Qt.SortOrder.AscendingOrder)
    table.setWordWrap(False)
    table.resizeColumnsToContents()
    table.horizontalHeader().setStretchLastSection(True)
    for index, column in enumerate(frame.columns):
        if column == "Текст":
            table.setColumnWidth(index, 500)
    if old_proxy is not None:
        old_proxy.deleteLater()


class FilePicker(QWidget):
    changed = Signal()

    def __init__(self, title="Переписка", parent=None):
        super().__init__(parent)
        self.chat = None
        self.path = None
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        button = QPushButton("Загрузить TXT" if title == "Переписка" else f"Загрузить {title}")
        button.clicked.connect(self.choose_file)
        self.file_label = QLabel("Файл не загружен")
        self.file_label.setWordWrap(True)
        row.addWidget(button)
        row.addWidget(self.file_label, 1)
        row.addWidget(QLabel("Целевой автор:"))
        self.authors = QComboBox()
        self.authors.setMinimumWidth(190)
        self.authors.currentTextChanged.connect(lambda _: self.changed.emit())
        row.addWidget(self.authors)
        layout.addLayout(row)
        self.info = QLabel("TXT • UTF-8 / Windows-1251 • обработка на этом компьютере")
        self.info.setWordWrap(True)
        layout.addWidget(self.info)

    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите переписку", "", "Переписка (*.txt)")
        if path:
            try:
                self.load_path(path)
            except Exception as exc:
                QMessageBox.warning(self, "Не удалось загрузить файл", str(exc))

    def load_path(self, path):
        chat = parse_chat(path)
        if chat.empty:
            raise ValueError("Не найдено текстовых сообщений. Проверьте формат: [11.06.2026 9:33] Автор: текст")
        self.chat, self.path = chat, Path(path)
        self.authors.blockSignals(True)
        self.authors.clear()
        self.authors.addItems(list(chat.author.unique()))
        self.authors.blockSignals(False)
        self.file_label.setText(self.path.name)
        self.file_label.setToolTip(str(self.path))
        d = chat.attrs["diagnostics"]
        details = f"Сообщений: {len(chat)} • Авторов: {chat.author.nunique()} • Исключено сообщений: {d['excluded_messages']} • Пропущено строк: {d['ignored_lines']}"
        if chat.author.nunique() == 1:
            details += "\nВ файле указан один автор: проверьте разметку участников перед интерпретацией серий."
        if d["chronology_inversions"]:
            details += "\nДаты идут не по порядку. Анализ сохраняет исходную последовательность файла."
        self.info.setText(details)
        self.changed.emit()

    @property
    def author(self):
        return self.authors.currentText()

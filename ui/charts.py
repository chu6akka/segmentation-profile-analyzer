from collections import Counter
import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "segmentation-profile-analyzer-mpl"))

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFileDialog, QMessageBox


class RussianToolbar(NavigationToolbar2QT):
    toolitems = [
        ("Исходный вид", "Восстановить исходный вид", "home", "home"),
        ("Назад", "Вернуться к предыдущему виду", "back", "back"),
        ("Вперёд", "Перейти к следующему виду", "forward", "forward"),
        (None, None, None, None),
        ("Перемещение", "Левая кнопка — перемещение; правая — масштаб", "move", "pan"),
        ("Масштаб", "Выделите прямоугольную область для увеличения", "zoom_to_rect", "zoom"),
        (None, None, None, None),
        ("Сохранить", "Сохранить графики в файл", "filesave", "save_figure"),
    ]

    def set_message(self, message):
        super().set_message(str(message).replace("pan/zoom", "перемещение / масштаб").replace("zoom rect", "увеличение области"))

    def save_figure(self, *args):
        path, selected = QFileDialog.getSaveFileName(
            self, "Сохранить графики", "графики.png",
            "Изображение PNG (*.png);;Документ PDF (*.pdf);;Векторное изображение SVG (*.svg)")
        if not path:
            return
        if not Path(path).suffix:
            path += ".pdf" if "*.pdf" in selected else ".svg" if "*.svg" in selected else ".png"
        try:
            self.canvas.figure.savefig(path)
        except Exception as exc:
            QMessageBox.warning(self, "Ошибка сохранения графиков", str(exc))


class Charts(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.figure = Figure(figsize=(10, 10), layout="constrained")
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setMinimumHeight(900)
        layout.addWidget(RussianToolbar(self.canvas, self))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.canvas)
        layout.addWidget(scroll)

    def clear(self):
        self.figure.clear()
        self.canvas.draw_idle()

    def display(self, analysis):
        self.figure.clear()
        axes = self.figure.subplots(3, 1)
        for ax, values, title, label in [
            (axes[0], analysis.message_word_lengths, "Распределение длины сообщений", "Слов в сообщении"),
            (axes[1], analysis.series_lengths, "Распределение длины серий", "Сообщений в серии"),
        ]:
            counts = Counter(values)
            ax.bar(list(counts), list(counts.values()), color="#367a9e")
            ax.set_title(title)
            ax.set_xlabel(label)
            ax.set_ylabel("Частота")
            ax.grid(axis="y", alpha=.2)
        keys = ["one_word_ratio", "short_message_ratio", "single_message_series_ratio",
                "long_series_ratio", "no_standard_final_punctuation_ratio", "lowercase_start_ratio", "bracket_ending_ratio"]
        labels = ["Однословные", "Короткие ≤3", "Одиночные серии", "Серии ≥3",
                  "Без конечной пунктуации", "Со строчной буквы", "Скобочное окончание"]
        values = [(analysis.profile[key] or 0) * 100 for key in keys]
        axes[2].barh(labels, values, color="#3a8b78")
        axes[2].set_xlim(0, 110)
        axes[2].set_xlabel("Доля, %")
        axes[2].set_title("Основные доли")
        for y, value in enumerate(values):
            axes[2].text(value + 1, y, f"{value:.1f}%", va="center")
        self.canvas.draw_idle()


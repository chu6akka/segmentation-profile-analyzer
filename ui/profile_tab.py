import pandas as pd
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableView

from features import SEGMENTATION_METRICS, BOUNDARY_METRICS
from ui.common import set_table


class ProfileTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.heading = QLabel("Загрузите TXT, выберите автора и нажмите «Анализировать».")
        self.heading.setWordWrap(True)
        layout.addWidget(self.heading)
        self.table = QTableView()
        self.table.verticalHeader().hide()
        layout.addWidget(self.table)
        note = QLabel("Доли рассчитаны по сообщениям, кроме доли серий ≥3. «—» означает отсутствие подходящих наблюдений.")
        note.setWordWrap(True)
        layout.addWidget(note)

    def clear(self):
        self.heading.setText("Нажмите «Анализировать» для выбранного файла и автора.")
        set_table(self.table, pd.DataFrame(columns=["Параметр", "Значение"]))

    def display(self, analysis):
        p = analysis.profile
        self.heading.setText(f"{p['author']}  •  {p['source_file']}  •  {len(analysis.series)} серий")
        rows = []
        for block, metrics in (("A. Параметры сегментации", SEGMENTATION_METRICS),
                               ("B. Оформление границ сообщений", BOUNDARY_METRICS)):
            for key, label in metrics.items():
                value = p[key]
                shown = "—" if value is None else (f"{value:.2%}" if key.endswith("ratio") else f"{value:.3f}".rstrip("0").rstrip("."))
                rows.append({"Блок": block, "Параметр": label, "Значение": shown})
        set_table(self.table, pd.DataFrame(rows))
        self.table.setSortingEnabled(False)
        self.table.setColumnWidth(1, 560)


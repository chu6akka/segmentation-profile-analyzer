from pathlib import Path

from matplotlib import get_data_path
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtCore import QTranslator, QLibraryInfo, QLocale


def configure_app(app):
    """Use a Cyrillic-capable font available with the required matplotlib package."""
    QLocale.setDefault(QLocale("ru_RU"))
    translator = QTranslator(app)
    if translator.load("qtbase_ru", QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
        app.installTranslator(translator)
        app._russian_translator = translator
    path = Path(get_data_path()) / "fonts" / "ttf" / "DejaVuSans.ttf"
    font_id = QFontDatabase.addApplicationFont(str(path))
    families = QFontDatabase.applicationFontFamilies(font_id)
    if families:
        app.setFont(QFont(families[0], 10))
    app.setStyle("Fusion")

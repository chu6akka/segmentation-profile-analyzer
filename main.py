"""Start the desktop UI, or analyze a file using the local CLI."""
import argparse
import sys
from pathlib import Path


def main():
    argparser = argparse.ArgumentParser(description="Segmentation Profile Analyzer")
    argparser.add_argument("--file", help="TXT file (CLI mode)")
    argparser.add_argument("--author", help="Exact author name")
    argparser.add_argument("--output", default="profile.csv", help="CSV or XLSX output")
    args = argparser.parse_args()
    if args.file:
        from parser import parse_chat
        from features import analyze_author
        from export import export_csv, export_xlsx
        try:
            frame = parse_chat(args.file)
            if not args.author:
                print("\n".join(frame.author.unique()))
                return 0
            result = analyze_author(frame, args.author)
            suffix = Path(args.output).suffix.lower()
            if suffix not in (".csv", ".xlsx"):
                raise ValueError("Выберите расширение .csv или .xlsx")
            (export_xlsx if suffix == ".xlsx" else export_csv)(result, args.output)
            print(f"Сохранено: {args.output}")
            return 0
        except Exception as exc:
            print(str(exc), file=sys.stderr)
            return 1
    from PySide6.QtWidgets import QApplication
    from ui.main_window import MainWindow
    from ui.theme import configure_app
    app = QApplication(sys.argv[:1])
    configure_app(app)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

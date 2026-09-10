"""Launch with `python -m palvault` or `python -m palvault --sqlserver`."""
import argparse
import os
from pathlib import Path
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from .repository import Repository
from .theme import STYLE
from .ui import MainWindow


def main():
    parser = argparse.ArgumentParser(description="Palvault — Palworld TCG collection manager")
    parser.add_argument("--sqlserver", action="store_true", help="Use the original SQL Server database")
    parser.add_argument("--demo-db", type=Path, help="Override the SQLite demo database location")
    args = parser.parse_args()
    app = QApplication(sys.argv[:1])
    app.setApplicationName("Palvault")
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    try:
        if args.sqlserver:
            repo = Repository.sqlserver()
            mode = "SQL Server · PalworldTCG"
        else:
            default = Path(os.getenv("LOCALAPPDATA", str(Path.home() / ".local" / "share"))) / "Palvault" / "demo.sqlite3"
            repo = Repository.demo(args.demo_db or default)
            mode = "Demo · saved on this device"
    except Exception:
        QMessageBox.critical(None, "Unable to open database", "Could not open the selected database. For SQL Server, check the service, ODBC Driver 18, and run sql/01 through sql/05 in order. To try the portable demo, start without --sqlserver.")
        return 1
    window = MainWindow(repo, mode)
    window.show()
    try:
        return app.exec()
    finally:
        repo.close()


if __name__ == "__main__":
    raise SystemExit(main())

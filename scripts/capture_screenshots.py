"""Render reproducible documentation images using a disposable demo database."""
import os
from pathlib import Path
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase
from PySide6.QtCore import QCoreApplication, QEvent
from palvault.repository import Repository
from palvault.theme import STYLE
from palvault.ui import MainWindow


def main():
    output = Path(__file__).resolve().parents[1] / "docs"
    output.mkdir(exist_ok=True)
    app = QApplication([])
    # Windows' offscreen Qt platform does not discover installed fonts itself.
    if sys.platform == "win32":
        for name in ("segoeui.ttf", "segoeuib.ttf", "seguisb.ttf", "consola.ttf"):
            QFontDatabase.addApplicationFont(str(Path(os.environ["WINDIR"]) / "Fonts" / name))
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    with tempfile.TemporaryDirectory() as directory:
        repo = Repository.demo(Path(directory) / "preview.sqlite3")
        repo.save_entry(repo.cards()[0]["CardID"], {
            "Quantity": 2, "CardCondition": "Near Mint", "PurchasePricePerCard": "3.50",
            "DateAcquired": "2026-09-10", "StorageLocation": "Red binder · page 01", "IsForTrade": False,
        })
        window = MainWindow(repo, "Demo · example collection")
        window.show()
        app.processEvents()
        window.grab().save(str(output / "catalogue.png"))
        window.switch_view("collection")
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        app.processEvents()
        window.grab().save(str(output / "collection.png"))
        window.close()
        repo.close()


if __name__ == "__main__":
    main()

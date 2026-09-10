import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox
import pytest
from palvault.repository import Repository
from palvault.theme import STYLE
from palvault.ui import CardEditor, EntryEditor, MainWindow


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance() or QApplication([])
    instance.setStyleSheet(STYLE)
    yield instance


def test_forms_search_and_collection_refresh(app, tmp_path):
    repo = Repository.demo(tmp_path / "ui.sqlite3")
    window = MainWindow(repo, "Test demo")
    window.show()
    app.processEvents()
    window.search.setText("Suzaku")
    assert len(window.filtered_cards()) == 1
    window.search.clear()
    editor = CardEditor(repo, window)
    editor.fields["CardNumber"].setText("CUSTOM-010")
    editor.fields["CardName"].setText("Test custom card")
    editor.save()
    assert editor.result() == QDialog.DialogCode.Accepted
    window.refresh()
    card = next(c for c in repo.cards() if c["CardNumber"] == "CUSTOM-010")
    entry = EntryEditor(repo, window, card)
    entry.quantity.setValue(4)
    entry.price.setText("2.50")
    entry.save()
    assert entry.result() == QDialog.DialogCode.Accepted
    window.refresh()
    window.switch_view("collection")
    assert repo.stats()["copies"] == 4
    assert "1 collection entries" in window.result_label.text()
    window.close()
    repo.close()


def test_delete_cancel_preserves_record(app, tmp_path, monkeypatch):
    repo = Repository.demo(tmp_path / "cancel.sqlite3")
    window = MainWindow(repo, "Test demo")
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Cancel)
    window.remove_card(repo.cards()[0])
    assert len(repo.cards()) == 3
    window.close()
    repo.close()


def test_start_menu_navigation_preserves_collection(app, tmp_path):
    repo = Repository.demo(tmp_path / "welcome.sqlite3")
    window = MainWindow(repo, "Test demo")
    assert window.pages.currentIndex() == 1
    window.start_catalogue.click()
    assert window.pages.currentIndex() == 0
    assert window.view == "catalogue"
    window.show_start_menu()
    window.start_collection.click()
    assert window.pages.currentIndex() == 0
    assert window.view == "collection"
    window.show_start_menu()
    assert window.pages.currentIndex() == 1
    assert len(repo.cards()) == 3
    assert repo.entries() == []
    window.close()
    repo.close()

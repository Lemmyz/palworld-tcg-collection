from collections import Counter
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from palvault.catalogue import snapshot
from palvault.card_reference import artwork_for, reference_for
from palvault.repository import Repository
from palvault.ui import MainWindow


def test_snapshot_complete_with_decodable_artwork(tmp_path):
    data = snapshot()
    repo = Repository.demo(tmp_path / "full.sqlite3")
    cards = repo.cards()
    assert len(cards) == data["total"] == 256
    assert Counter(c["SetCode"] for c in cards) == {s["code"]: s["count"] for s in data["sets"]}
    assert Counter(c["Rarity"] for c in cards) == data["rarities"]
    assert len({c["id"] for c in data["cards"]}) == 256
    assert sum(c["parallel"] for c in data["cards"]) == data["parallel_total"] == 89
    for card in cards:
        assert reference_for(card) is not None
        picture = QImage(str(artwork_for(card)))
        assert not picture.isNull(), card["CardNumber"]
        assert picture.width() > 100 and picture.height() > 100
    repo.close()


def test_import_preserves_owned_ids_and_user_edits(tmp_path):
    path = tmp_path / "upgrade.sqlite3"
    repo = Repository.demo(path, seed_catalogue=False)
    original = repo.cards()[0]
    repo.save_card(dict(original, CardName="My edited card name"), original["CardID"])
    repo.save_entry(original["CardID"], {"Quantity": 5, "CardCondition": "Mint"})
    before = repo.entries()
    result = repo.import_catalogue()
    assert result["cards_added"] == 253 and result["sets_added"] == 3
    assert repo.entries() == before
    assert next(c for c in repo.cards() if c["CardID"] == original["CardID"])["CardName"] == "My edited card name"
    assert repo.import_catalogue()["cards_added"] == 0
    other = next(c for c in repo.cards() if c["CardNumber"] == "EBP01-001OSR")
    repo.delete_card(other["CardID"])
    repo.close()
    repo = Repository.demo(path)
    assert len(repo.cards()) == 255
    assert repo.import_catalogue(force=True)["cards_added"] == 1
    assert repo.entries() == before
    repo.close()


def test_same_number_in_different_sets_and_soul_null_stats(tmp_path):
    repo = Repository.demo(tmp_path / "souls.sqlite3")
    souls = [c for c in repo.cards() if c["CardNumber"] == "ESOUL-001"]
    assert {c["SetCode"] for c in souls} == {"ETD01", "ETD02"}
    assert artwork_for(souls[0]) != artwork_for(souls[1])
    assert reference_for(souls[0])["cost"] is None
    repo.save_card(souls[0], souls[0]["CardID"])
    assert next(c for c in repo.cards() if c["CardID"] == souls[0]["CardID"])["CardColour"] is None
    repo.close()


def test_set_rarity_variant_filters_and_pagination(tmp_path):
    app = QApplication.instance() or QApplication([])
    repo = Repository.demo(tmp_path / "filters.sqlite3")
    window = MainWindow(repo, "Test demo")
    window.switch_view("catalogue")
    assert len(window.visible_cards) == 12
    first_ids = {c["CardID"] for c in window.visible_cards}
    window.change_page(1)
    assert not first_ids & {c["CardID"] for c in window.visible_cards}
    window.set_filter.setCurrentIndex(window.set_filter.findData("ETD01"))
    assert window.page_index == 0
    assert len(window.filtered_cards()) == 39
    window.rarity_filter.setCurrentIndex(window.rarity_filter.findData("TSP"))
    assert len(window.filtered_cards()) == 2
    window.variant_filter.setCurrentIndex(window.variant_filter.findData("Parallel (TSP)"))
    assert len(window.filtered_cards()) == 2
    window.rarity_filter.setCurrentIndex(window.rarity_filter.findData("SSS"))
    assert window.visible_cards == []
    assert not window.next_page.isEnabled()
    window.clear_filters()
    assert len(window.filtered_cards()) == 256
    window.close()
    app.processEvents()
    repo.close()

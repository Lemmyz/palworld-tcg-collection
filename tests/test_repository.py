from decimal import Decimal
import pytest
from palvault.repository import Repository, ValidationError


@pytest.fixture
def repo(tmp_path):
    instance = Repository.demo(tmp_path / "collection.sqlite3")
    yield instance
    instance.close()


def entry(**overrides):
    return {"Quantity": 2, "CardCondition": "Near Mint", "PurchasePricePerCard": "1.25",
            "DateAcquired": "2026-09-10", "StorageLocation": "Binder A", "IsForTrade": True, **overrides}


def test_collection_lifecycle_and_exact_spend(repo):
    card = repo.cards()[0]
    repo.save_entry(card["CardID"], entry())
    record = repo.entries()[0]
    assert repo.cards()[0]["Owned"] == 2
    assert repo.stats()["spent"] == Decimal("2.50")
    repo.save_entry(card["CardID"], entry(Quantity=3, PurchasePricePerCard="0.10"), record["CollectionEntryID"])
    assert repo.stats()["spent"] == Decimal("0.30")
    assert repo.entries()[0]["StorageLocation"] == "Binder A"
    repo.delete_entry(record["CollectionEntryID"])
    assert repo.stats()["copies"] == 0


def test_delete_owned_card_is_blocked(repo):
    card = repo.cards()[0]
    repo.save_entry(card["CardID"], entry())
    with pytest.raises(ValidationError):
        repo.delete_card(card["CardID"])
    assert len(repo.cards()) == 3
    assert len(repo.entries()) == 1


def test_catalogue_crud_duplicate_and_parameterized_text(repo):
    card = dict(repo.cards()[0])
    card.update(CardNumber="CUSTOM-001", CardName="Collector's card; DROP TABLE Cards; --")
    repo.save_card(card)
    saved = next(c for c in repo.cards() if c["CardNumber"] == "CUSTOM-001")
    assert saved["CardName"] == card["CardName"]
    with pytest.raises(ValidationError):
        repo.save_card(card)
    saved["CardName"] = "Renamed card"
    repo.save_card(saved, saved["CardID"])
    assert any(c["CardName"] == "Renamed card" for c in repo.cards())
    repo.delete_card(saved["CardID"])
    assert len(repo.cards()) == 3


@pytest.mark.parametrize("changes", [
    {"Quantity": 0}, {"Quantity": 1.5}, {"Quantity": True}, {"Quantity": 1000000},
    {"PurchasePricePerCard": "-1"}, {"PurchasePricePerCard": "NaN"},
    {"PurchasePricePerCard": "1.001"}, {"PurchasePricePerCard": "Infinity"},
    {"DateAcquired": "2026-02-30"}, {"CardCondition": "Unknown"}, {"StorageLocation": "x" * 101},
])
def test_invalid_entries_do_not_write(repo, changes):
    with pytest.raises(ValidationError):
        repo.save_entry(repo.cards()[0]["CardID"], entry(**changes))
    assert repo.entries() == []


def test_blank_price_is_distinct_from_free(repo):
    card_id = repo.cards()[0]["CardID"]
    repo.save_entry(card_id, entry(PurchasePricePerCard=""))
    repo.save_entry(card_id, entry(PurchasePricePerCard="0.00"))
    assert repo.entries()[0]["PurchasePricePerCard"] == 0
    assert repo.entries()[1]["PurchasePricePerCard"] is None


def test_persistence_and_no_reseeding_deleted_cards(tmp_path):
    path = tmp_path / "persist.sqlite3"
    repo = Repository.demo(path)
    repo.delete_card(repo.cards()[0]["CardID"])
    repo.save_entry(repo.cards()[0]["CardID"], entry())
    repo.close()
    reopened = Repository.demo(path)
    assert len(reopened.cards()) == 2
    assert reopened.stats()["copies"] == 2
    reopened.close()


def test_transaction_rolls_back(repo):
    with pytest.raises(RuntimeError):
        with repo.transaction():
            repo.connection.execute("DELETE FROM Cards")
            raise RuntimeError("simulate a failure before commit")
    assert len(repo.cards()) == 3

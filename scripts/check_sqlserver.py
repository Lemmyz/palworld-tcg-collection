"""Integration check in an isolated, disposable SQL Server database.

Requires permission to create/drop a test database. Never writes to PalworldTCG.
"""
from pathlib import Path
import re
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pyodbc
from database import CONNECTION_STRING
from palvault.repository import Repository, ValidationError


def main():
    name = "PalvaultTest_" + uuid.uuid4().hex
    admin = pyodbc.connect(CONNECTION_STRING, autocommit=True, timeout=5)
    repo = None
    created = False
    try:
        admin.execute(f"CREATE DATABASE [{name}]")
        created = True
        connection_string = re.sub(r"DATABASE=[^;]+", f"DATABASE={name}", CONNECTION_STRING, flags=re.I)
        connection = pyodbc.connect(connection_string, autocommit=True, timeout=5)
        repo = Repository(connection, "sqlserver")
        root = Path(__file__).resolve().parents[1]
        scripts = sorted((root / "sql").glob("*.sql"))[1:]
        # Rerun every setup/seed script to prove idempotency as well as a clean setup.
        for _ in range(2):
            for path in scripts:
                source = path.read_text(encoding="utf-8-sig").replace("USE PalworldTCG;", f"USE [{name}];")
                for batch in re.split(r"^GO\s*$", source, flags=re.M | re.I):
                    if batch.strip():
                        cursor = connection.execute(batch)
                        while cursor.nextset():
                            pass
                        cursor.close()
        connection.autocommit = False
        card = repo.cards()[0]
        assert len(repo.cards()) == 3
        repo.save_entry(card["CardID"], {"Quantity": 2, "CardCondition": "Near Mint", "PurchasePricePerCard": "0.10"})
        assert str(repo.stats()["spent"]) == "0.20"
        try:
            repo.delete_card(card["CardID"])
            raise AssertionError("Owned-card deletion should be blocked")
        except ValidationError:
            pass
        record = repo.entries()[0]
        repo.save_entry(card["CardID"], {"Quantity": 3, "CardCondition": "Mint", "PurchasePricePerCard": "2.50"}, record["CollectionEntryID"])
        assert repo.stats()["copies"] == 3
        repo.delete_entry(record["CollectionEntryID"])
        custom = dict(card, CardNumber="TEST-001", CardName="Integration card")
        repo.save_card(custom)
        saved = next(c for c in repo.cards() if c["CardNumber"] == "TEST-001")
        repo.save_card(dict(saved, CardName="Edited integration card"), saved["CardID"])
        repo.delete_card(saved["CardID"])
        assert len(repo.cards()) == 3 and repo.stats()["copies"] == 0
        print("SQL Server integration passed: repeatable setup, card CRUD, collection CRUD, joins, totals, deletion protection.")
    finally:
        if repo:
            repo.close()
        if created:
            # Name is generated internally, never read from user input or a file.
            admin.execute(f"ALTER DATABASE [{name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
            admin.execute(f"DROP DATABASE [{name}]")
        admin.close()


if __name__ == "__main__":
    main()

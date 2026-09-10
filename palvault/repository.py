"""Parameterized persistence shared by SQLite demo and SQL Server modes.

Connections belong to one Repository and are closed explicitly. Each mutation
is a transaction; the UI never constructs SQL or owns database rules.
"""
from contextlib import contextmanager
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
import os
import sqlite3

CONDITIONS = ("Mint", "Near Mint", "Lightly Played", "Moderately Played", "Heavily Played", "Damaged")
COLOURS = ("Red", "Blue", "Green", "Yellow", "Purple", "Black", "White", "Colourless")
TYPES = ("Pal", "Structure", "Gear", "Event")


class ValidationError(ValueError):
    """A user-correctable validation or relationship error."""


def required(value, label, limit):
    value = str(value or "").strip()
    if not value or len(value) > limit:
        raise ValidationError(f"{label} must contain 1–{limit} characters.")
    return value


class Repository:
    def __init__(self, connection, backend="sqlite"):
        self.connection = connection
        self.backend = backend

    @classmethod
    def demo(cls, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path)
        connection.execute("PRAGMA foreign_keys = ON")
        repo = cls(connection)
        connection.executescript('''
            CREATE TABLE IF NOT EXISTS CardSets (
                SetID INTEGER PRIMARY KEY, SetCode TEXT NOT NULL UNIQUE,
                SetName TEXT NOT NULL, ReleaseDate TEXT);
            CREATE TABLE IF NOT EXISTS Cards (
                CardID INTEGER PRIMARY KEY, SetID INTEGER NOT NULL REFERENCES CardSets(SetID),
                CardNumber TEXT NOT NULL, CardName TEXT NOT NULL, CardType TEXT NOT NULL,
                CardColour TEXT, Rarity TEXT NOT NULL, Variant TEXT NOT NULL DEFAULT 'Standard',
                UNIQUE(SetID, CardNumber, Variant));
            CREATE TABLE IF NOT EXISTS CollectionEntries (
                CollectionEntryID INTEGER PRIMARY KEY,
                CardID INTEGER NOT NULL REFERENCES Cards(CardID),
                Quantity INTEGER NOT NULL DEFAULT 1 CHECK(Quantity > 0),
                CardCondition TEXT NOT NULL DEFAULT 'Near Mint',
                PurchasePricePerCard NUMERIC CHECK(PurchasePricePerCard IS NULL OR PurchasePricePerCard >= 0),
                DateAcquired TEXT, StorageLocation TEXT, IsForTrade INTEGER NOT NULL DEFAULT 0);
            CREATE INDEX IF NOT EXISTS IX_CollectionEntries_CardID ON CollectionEntries(CardID);
            CREATE TABLE IF NOT EXISTS AppMetadata (Key TEXT PRIMARY KEY, Value TEXT NOT NULL);
        ''')
        # A separate marker prevents deleted demo cards reappearing at startup.
        if not repo.query("SELECT Value FROM AppMetadata WHERE Key = ?", ("seed_version",)):
            with repo.transaction():
                connection.execute("INSERT INTO CardSets VALUES (1, 'EBP01', 'Dawn of Palpagos', '2026-07-30')")
                for number, name, rarity in (
                    ("EBP01-001", "Jormuntide Ignis - Savage Lava Dragon", "RR"),
                    ("EBP01-002", "Suzaku - Hellfire Wings", "RR"),
                    ("EBP01-003", "Gobfin Ignis - Blazing Hothead", "R"),
                ):
                    connection.execute("INSERT INTO Cards (SetID,CardNumber,CardName,CardType,CardColour,Rarity,Variant) VALUES (1,?,?, 'Pal','Red',?,'Standard')", (number, name, rarity))
                connection.execute("INSERT INTO AppMetadata VALUES ('seed_version', '1')")
        return repo

    @classmethod
    def sqlserver(cls):
        import pyodbc
        from database import CONNECTION_STRING
        connection = pyodbc.connect(os.getenv("PALVAULT_CONNECTION_STRING", CONNECTION_STRING), timeout=5)
        repo = cls(connection, "sqlserver")
        # Startup is read-only: setup and migrations are an explicit command.
        repo.query("SELECT TOP 0 CollectionEntryID FROM dbo.CollectionEntries")
        return repo

    def close(self):
        self.connection.close()

    @contextmanager
    def transaction(self):
        try:
            yield
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def query(self, sql, parameters=()):
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql, parameters)
            names = [column[0] for column in cursor.description]
            return [dict(zip(names, row)) for row in cursor.fetchall()]
        finally:
            cursor.close()

    def sets(self):
        return self.query("SELECT * FROM CardSets ORDER BY SetCode")

    def cards(self):
        return self.query('''SELECT c.*, s.SetCode, s.SetName, s.ReleaseDate,
            COALESCE(e.Owned, 0) AS Owned FROM Cards c
            JOIN CardSets s ON s.SetID = c.SetID
            LEFT JOIN (SELECT CardID, SUM(Quantity) AS Owned FROM CollectionEntries GROUP BY CardID) e
            ON e.CardID = c.CardID ORDER BY c.CardNumber, c.Variant''')

    def entries(self, card_id=None):
        sql = '''SELECT e.*, c.CardNumber, c.CardName, c.Variant FROM CollectionEntries e
                 JOIN Cards c ON c.CardID = e.CardID'''
        return self.query(sql + (" WHERE e.CardID = ?" if card_id is not None else "") + " ORDER BY e.CollectionEntryID DESC", (card_id,) if card_id is not None else ())

    def save_card(self, values, card_id=None):
        data = {key: required(values.get(key), label, limit) for key, label, limit in (
            ("CardNumber", "Card number", 20), ("CardName", "Card name", 100),
            ("CardType", "Card type", 30), ("Rarity", "Rarity", 20),
            ("Variant", "Variant", 50))}
        data["CardColour"] = required(values.get("CardColour"), "Colour", 30)
        data["SetID"] = values.get("SetID")
        if not self.query("SELECT SetID FROM CardSets WHERE SetID = ?", (data["SetID"],)):
            raise ValidationError("Choose an existing card set.")
        duplicates = self.query("SELECT CardID FROM Cards WHERE SetID = ? AND CardNumber = ? AND Variant = ?", (data["SetID"], data["CardNumber"], data["Variant"]))
        if any(row["CardID"] != card_id for row in duplicates):
            raise ValidationError("This card number and variant already exist in that set.")
        if card_id is not None and not self.query("SELECT CardID FROM Cards WHERE CardID = ?", (card_id,)):
            raise ValidationError("This card no longer exists. Refresh the catalogue.")
        fields = list(data)
        with self.transaction():
            cursor = self.connection.cursor()
            try:
                if card_id is None:
                    cursor.execute(f"INSERT INTO Cards ({','.join(fields)}) VALUES ({','.join('?' for _ in fields)})", tuple(data.values()))
                else:
                    cursor.execute(f"UPDATE Cards SET {','.join(f'{field} = ?' for field in fields)} WHERE CardID = ?", (*data.values(), card_id))
            finally:
                cursor.close()

    def delete_card(self, card_id):
        if self.entries(card_id):
            raise ValidationError("Remove this card's collection entries before deleting its catalogue record.")
        with self.transaction():
            self.connection.execute("DELETE FROM Cards WHERE CardID = ?", (card_id,))

    def save_entry(self, card_id, values, entry_id=None):
        quantity = values.get("Quantity")
        if isinstance(quantity, bool) or not isinstance(quantity, int) or not 1 <= quantity <= 999999:
            raise ValidationError("Quantity must be a whole number between 1 and 999,999.")
        condition = values.get("CardCondition")
        if condition not in CONDITIONS:
            raise ValidationError("Choose a supported card condition.")
        raw_price = values.get("PurchasePricePerCard")
        price = None
        if raw_price not in (None, ""):
            try:
                price = Decimal(str(raw_price))
                if not price.is_finite() or price < 0 or price > Decimal("99999999.99") or price != price.quantize(Decimal("0.01")):
                    raise InvalidOperation
            except (InvalidOperation, ValueError):
                raise ValidationError("Price must be a non-negative amount with at most two decimal places.") from None
        acquired = values.get("DateAcquired") or None
        if acquired:
            try:
                acquired = date.fromisoformat(str(acquired)).isoformat()
            except ValueError:
                raise ValidationError("Use a valid acquisition date in YYYY-MM-DD format.") from None
        location = str(values.get("StorageLocation") or "").strip()
        if len(location) > 100:
            raise ValidationError("Storage location must be 100 characters or fewer.")
        if not self.query("SELECT CardID FROM Cards WHERE CardID = ?", (card_id,)):
            raise ValidationError("This card no longer exists.")
        if entry_id is not None and not self.query("SELECT CollectionEntryID FROM CollectionEntries WHERE CollectionEntryID = ? AND CardID = ?", (entry_id, card_id)):
            raise ValidationError("This collection entry no longer exists.")
        data = (quantity, condition, str(price) if price is not None else None, acquired, location or None, int(bool(values.get("IsForTrade"))))
        with self.transaction():
            if entry_id is None:
                self.connection.execute("INSERT INTO CollectionEntries (Quantity,CardCondition,PurchasePricePerCard,DateAcquired,StorageLocation,IsForTrade,CardID) VALUES (?,?,?,?,?,?,?)", (*data, card_id))
            else:
                self.connection.execute("UPDATE CollectionEntries SET Quantity=?,CardCondition=?,PurchasePricePerCard=?,DateAcquired=?,StorageLocation=?,IsForTrade=? WHERE CollectionEntryID=?", (*data, entry_id))

    def delete_entry(self, entry_id):
        with self.transaction():
            self.connection.execute("DELETE FROM CollectionEntries WHERE CollectionEntryID = ?", (entry_id,))

    def stats(self):
        cards = self.cards()
        entries = self.entries()
        return {"catalogue": len(cards), "unique": sum(c["Owned"] > 0 for c in cards),
                "copies": sum(e["Quantity"] for e in entries),
                "spent": sum((Decimal(str(e["PurchasePricePerCard"])) * e["Quantity"] for e in entries if e["PurchasePricePerCard"] is not None), Decimal(0))}

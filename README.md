# Palvault · Palworld TCG Collection Manager

[![Application tests](https://github.com/Lemmyz/palworld-tcg-collection/actions/workflows/tests.yml/badge.svg)](https://github.com/Lemmyz/palworld-tcg-collection/actions/workflows/tests.yml)

A Python desktop application for browsing Palworld cards and managing a personal
collection. Built with **PySide6, SQL Server, T-SQL, and pyodbc**, with a portable
SQLite demo so employers can evaluate the application without a database server.

![Palvault start menu](docs/start-menu.png)

The app opens with a start menu explaining what Palvault does and how to use it.
Choose **Open card catalogue** or **Open my collection** to begin. Return to the
guide at any time using **Start menu** in the sidebar.

![Palvault card catalogue](docs/catalogue.png)

## Try it

**Windows:** download the ZIP from [Releases](https://github.com/Lemmyz/palworld-tcg-collection/releases),
extract the entire folder, then open **Palvault.exe**. The default demo stores
changes locally and needs neither Python nor SQL Server. This is an unsigned
portfolio build, not a Microsoft Store application.

**From source** (Python 3.13 recommended):

```powershell
git clone https://github.com/Lemmyz/palworld-tcg-collection.git
cd palworld-tcg-collection
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m palvault
```

On macOS/Linux, activate with `source .venv/bin/activate`. The tested desktop
platform is Windows 11; the portable data layer is cross-platform.

## Features

- Browse cards with artwork, rarity, colour, type, variant, and set information.
- Search by name or card number; filter by set, rarity, variant, colour, and ownership.
- Browse 256 official English printings across four sets/promo groups, with
  89 parallel printings, all 13 published rarity labels, and offline artwork.
- Page through the catalogue in groups of 12 for responsive browsing.
- Add, edit, and delete catalogue records, with duplicate protection.
- Track multiple collection entries per card: quantity, condition, price per
  copy, acquisition date, storage location, and availability for trade.
- Edit or remove owned copies without deleting the catalogue card.
- View total copies, unique cards collected, and recorded purchase spend.
- View published cost, power, strike, element, subtype, and work suitability;
  open the exact official printing for card text and current rulings. Fields
  that do not apply to a card, such as Soul-card combat stats, stay absent.
- Persist changes across restarts. Cancelled dialogs make no changes.
- Keyboard shortcuts: **Ctrl+F** search, **Ctrl+N** new card, **F5** refresh.

![Palvault collection ledger](docs/collection.png)

### Evaluation walkthrough

1. Open the demo, choose **Open card catalogue**, and select **Jormuntide Ignis**.
2. Choose **Add to collection**, enter a quantity and optional purchase details,
   then save. The owned count and totals update immediately.
3. Open **My collection**, select the entry, and edit its quantity or condition.
4. Close and reopen the app to verify persistence.
5. Remove the entry. The catalogue record remains available to collect again.
6. Add your own catalogue card with **New card** and edit its details.

## SQL Server setup

The app connects directly to the original `CardSets`, `Cards`, and
`CollectionEntries` tables.

1. Install SQL Server Express and **Microsoft ODBC Driver 18 for SQL Server**.
2. In SQL Server Management Studio, connect using Windows Authentication and run
   the scripts in `sql/` in numerical order, **01 through 05**.
3. Import the bundled catalogue, then start the desktop app:

```powershell
python -m palvault --sqlserver --import-catalogue
```

For the packaged app, run `Palvault.exe --sqlserver --import-catalogue` once,
then use `Palvault.exe --sqlserver` for subsequent launches. The default
server is `localhost\SQLEXPRESS`, database `PalworldTCG`, with Windows
Authentication. To use another server, set `PALVAULT_CONNECTION_STRING` in the
environment before starting the app. Never commit credentials.

Setup scripts are additive and safe to rerun. Script 05 fills the gap in the
original repository's collection-table setup. Startup does not run SQL Server
migrations or seed data. A failed connection is reported; the app never silently
switches databases. The explicit `--import-catalogue` option adds missing sets
and printings without replacing existing card IDs, edits, or owned copies.
The original CLI reader remains available as `python main.py`.

## Architecture

```mermaid
flowchart LR
    UI[PySide6 desktop interface] --> R[Repository and validation]
    R --> SQL[SQL Server via pyodbc]
    R --> Demo[SQLite portable demo]
    UI --> Ref[Verified official catalogue snapshot]
```

```mermaid
erDiagram
    CardSets ||--o{ Cards : contains
    Cards ||--o{ CollectionEntries : collected_as
    CardSets {
        int SetID PK
        string SetCode UK
        string SetName
        date ReleaseDate
    }
    Cards {
        int CardID PK
        int SetID FK
        string CardNumber
        string CardName
        string CardType
        string CardColour
        string Rarity
        string Variant
    }
    CollectionEntries {
        int CollectionEntryID PK
        int CardID FK
        int Quantity
        string CardCondition
        decimal PurchasePricePerCard
        date DateAcquired
        string StorageLocation
        bool IsForTrade
    }
```

Two purchases of the same card can have different conditions, prices, and
locations, so catalogue cards and owned copies are separate entities. A
composite unique constraint on set, card number, and variant prevents duplicate
catalogue records. Foreign keys prevent orphaned collection entries. A card
with owned copies cannot be deleted until those entries are removed.

The UI delegates persistence to `palvault/repository.py`. Values use bound query
parameters. Transactions commit complete changes or roll back failures. SQL
joins aggregate owned quantities. Money is validated to two decimal places and
totals use Python `Decimal`; SQL Server stores prices as `DECIMAL(10,2)`.

## Tests and builds

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests cover catalogue and collection CRUD, duplicates, invalid input, SQL-like
text values, deletion protection, rollback, persistence, search, form saves,
and cancellation. GitHub Actions runs these tests on Windows.

```powershell
python scripts/check_sqlserver.py
```

The integration check requires permission to create/drop a database. It creates
a uniquely named disposable test database, runs setup twice, checks both CRUD
workflows, then drops that database. It does not change `PalworldTCG`.

Build a Windows executable folder:

```powershell
python -m pip install pyinstaller==6.16.0
./build-windows.ps1
```

The result is `dist/Palvault/`; keep the entire folder together. The manual
**Build Windows app** GitHub Actions workflow produces the same type of build.
Regenerate documentation screenshots with `python scripts/capture_screenshots.py`.
Screenshots use disposable example data, not a private collection.

## Data and current scope

- The bundled snapshot contains **all 256 printings in the official English
  catalogue retrieved on 10 September 2026**. See [catalogue coverage](docs/CATALOGUE.md)
  for set totals, rarity counts, verification, and update instructions. This
  is a dated English snapshot, not a claim to include unrevealed or Japanese-only cards.
- All official sets are imported. Add custom cards through the app. Custom set
  creation still uses SQL rather than a set editor.
- Demo and SQL Server collections are separate and do not synchronise. On
  Windows, demo data lives at `%LOCALAPPDATA%\Palvault\demo.sqlite3`. Copy it
  while the app is closed to back it up. Override its location using
  `python -m palvault --demo-db path/to/collection.sqlite3`.
- Artwork and published reference stats are bundled for every official printing.
  Custom cards show their entered catalogue details. Full official numbers,
  including rarity suffixes, are retained; parallel status comes from the
  official filter rather than an inference from rarity.
- The demo imports missing official printings once per snapshot version, keeping
  existing records and owned copies. A deleted card stays deleted on later
  launches of the same version. An explicit `--import-catalogue` restores missing
  official catalogue records. SQLite also stores a snapshot marker in `AppMetadata`;
  the SQL Server importer creates the same table when first used.
- Spend means recorded purchase costs in GBP, not market value. The collected
  fraction is relative to the local catalogue, not full-set completion.
- This is a single-user desktop app, with no hosted browser demo or cloud sync.

See [asset provenance and attribution](docs/ASSETS.md). Palvault is an unofficial
fan portfolio project and is not affiliated with Pocketpair or Bushiroad.

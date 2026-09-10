"""Import the bundled catalogue into the original SQL Server database.

python scripts/import_catalogue.py [--force]
All changes are additive; existing catalogue IDs and collection rows survive.
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from palvault.repository import Repository


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Restore missing official cards even if this snapshot was imported before")
    args = parser.parse_args()
    repo = Repository.sqlserver()
    try:
        print(json.dumps(repo.import_catalogue(force=args.force)))
    finally:
        repo.close()


if __name__ == "__main__":
    main()

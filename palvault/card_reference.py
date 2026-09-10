"""Small verified reference snapshot; unknown cards never receive invented stats.

Source: official English EBP01 card catalogue, retrieved 2026-09-10.
See docs/ASSETS.md for provenance and artwork ownership.
"""
from pathlib import Path

REFERENCE = {
    "EBP01-001": {"cost": 8, "power": 1700, "strike": 4, "element": "Dragon / Fire", "subtype": "Lucky Pal"},
    "EBP01-002": {"cost": 7, "power": 1200, "strike": 3, "element": "Fire", "subtype": "Lucky Pal"},
    "EBP01-003": {"cost": 4, "power": 400, "strike": 2, "element": "Fire", "subtype": "Normal Pal"},
}


def reference_for(card):
    if card["SetCode"] == "EBP01" and card["Variant"] == "Standard":
        return REFERENCE.get(card["CardNumber"])
    return None


def artwork_for(card):
    if reference_for(card):
        return Path(__file__).parent / "assets" / f"{card['CardNumber']}.png"
    return None

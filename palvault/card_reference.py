"""Resolve exact printings, including identical numbers in different sets."""
from pathlib import Path
from .catalogue import references


def reference_for(card):
    return references().get((card["SetCode"], card["CardNumber"], card["Variant"]))


def artwork_for(card):
    reference = reference_for(card)
    if reference:
        return Path(__file__).parent / "assets" / reference["artwork"]
    return None

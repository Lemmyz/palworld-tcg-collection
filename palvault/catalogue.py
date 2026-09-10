"""The reproducible, offline official English card catalogue snapshot."""
from functools import lru_cache
import json
from pathlib import Path


@lru_cache(maxsize=1)
def snapshot():
    path = Path(__file__).parent / "assets" / "catalogue.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if len(data["cards"]) != data["total"]:
        raise ValueError("The bundled catalogue is incomplete")
    return data


@lru_cache(maxsize=1)
def references():
    return {(c["set"], c["number"], c["variant"]): c for c in snapshot()["cards"]}

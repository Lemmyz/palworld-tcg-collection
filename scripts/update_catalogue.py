"""Refresh the bundled English catalogue from the official public card API.

Validates pagination, set totals, parallel coverage, unique IDs and artwork
before replacing the snapshot. Does not connect to a collection database.
"""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
API = "https://en.palworld-official-cardgame.com/manage/card-list-user/"
IMAGES = "https://en.palworld-official-cardgame.com/wordpress/wp-content/images/cardlist/"


def fetch(url):
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={"User-Agent": "Palvault-Catalogue/1.2"}), timeout=30) as response:
                return response.read()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def listing(**filters):
    rows, total, page = [], None, 1
    while True:
        payload = json.loads(fetch(API + "list?" + urlencode(dict(filters, page=page, per_page=100, sort="no"))))
        if total is None:
            total = payload["total"]
        if payload["total"] != total or payload["page"] != page:
            raise ValueError("Official catalogue changed during pagination; rerun the refresh.")
        batch = payload["items"]
        rows.extend(batch)
        if len(rows) == total:
            break
        if not batch or len(rows) > total:
            raise ValueError("Incomplete or inconsistent official pagination")
        page += 1
    if len({r["id"] for r in rows}) != total:
        raise ValueError("Duplicate official IDs in pagination")
    return rows


def main():
    products = json.loads(fetch(API + "products"))
    sets = []
    for group in products["products"]:
        for item in group["items"]:
            sets.append({"code": item["code"], "name": item["name"], "kind": item["type"],
                         "release_date": item["date"].replace(".", "-") or None})
    rows = listing()
    parallel = {r["id"] for r in listing(parallel="only")}
    standard = {r["id"] for r in listing(parallel="exclude")}
    if parallel & standard or parallel | standard != {r["id"] for r in rows}:
        raise ValueError("Official parallel and standard filters do not partition the catalogue")
    counts = Counter(r["expansion"] for r in rows)
    if set(counts) != {s["code"] for s in sets}:
        raise ValueError("Unmapped card set or empty listed product")
    for item in sets:
        expected_ids = {r["id"] for r in rows if r["expansion"] == item["code"]}
        if {r["id"] for r in listing(title=item["code"])} != expected_ids:
            raise ValueError("Set query disagrees with full catalogue")
        item["count"] = counts[item["code"]]
    cards = []
    for row in rows:
        variant = f"Parallel ({row['rare']})" if row["id"] in parallel else ("Promo" if row["rare"] == "PR" else "Standard")
        cards.append({"id": row["id"], "set": row["expansion"], "number": row["card_number"],
                      "name": row["card_name"], "type": row["card_kind"], "colour": row["color"] or None,
                      "rarity": row["rare"], "variant": variant, "parallel": row["id"] in parallel,
                      "cost": int(row["cost"]) if row["cost"] else None,
                      "power": int(row["power"]) if row["power"] else None,
                      "strike": int(row["attack"]) if row["attack"] else None,
                      "element": row["type"].replace("|", " / "), "subtype": row["card_kind_sub"],
                      "work_suitability": row["aptitude"].replace("|", " / "),
                      "artwork": f"official/{row['id']}.png", "image_source": IMAGES + quote(row["picture"], safe="/"),
                      "source": f"https://en.palworld-official-cardgame.com/cardlist/detail/?id={row['id']}"})
    keys = {(c["set"], c["number"], c["variant"]) for c in cards}
    if len(keys) != len(cards):
        raise ValueError("Two official printings would collide in the local schema")
    assets = ROOT / "palvault" / "assets"
    (assets / "official").mkdir(exist_ok=True)

    def download(card):
        target = assets / card["artwork"]
        data = fetch(card["image_source"])
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError(f"Invalid PNG for official card {card['id']}")
        temporary = target.with_suffix(".tmp")
        temporary.write_bytes(data)
        temporary.replace(target)

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(download, cards))
    snapshot = {"language": "en", "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "source": "https://en.palworld-official-cardgame.com/cardlist/", "sets": sets, "cards": cards,
                "total": len(cards), "parallel_total": len(parallel), "rarities": dict(sorted(Counter(c["rarity"] for c in cards).items()))}
    snapshot["version"] = hashlib.sha256(json.dumps(cards, sort_keys=True).encode()).hexdigest()[:16]
    target = assets / "catalogue.json"
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
    print(json.dumps({"total": len(cards), "sets": dict(counts), "parallel_total": len(parallel), "rarities": snapshot["rarities"]}))


if __name__ == "__main__":
    main()

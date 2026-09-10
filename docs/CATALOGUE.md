# Official English catalogue coverage

Snapshot retrieved **10 September 2026** from the
[official English Palworld card catalogue](https://en.palworld-official-cardgame.com/cardlist/).
The public catalogue lists **256 printings**, with **89 marked parallel**.

| Set/group | Code | Printings | Product release date |
| --- | --- | ---: | --- |
| Booster Pack: Dawn of Palpagos | EBP01 | 162 | 2026-07-30 |
| Trial Deck: Dawn of Palpagos Red / Blue | ETD01 | 39 | 2026-07-30 |
| Trial Deck: Dawn of Palpagos Green / Purple | ETD02 | 39 | 2026-07-30 |
| PR Cards (2026) | PR2026 | 16 | Not supplied for the group |
| **Total** | | **256** | |

| Rarity | Printings |
| --- | ---: |
| C | 34 |
| U | 30 |
| R | 24 |
| RR | 12 |
| SR | 30 |
| OSR | 15 |
| SP | 12 |
| SSP | 4 |
| SSS | 1 |
| TD | 50 |
| TSR | 24 |
| TSP | 4 |
| PR | 16 |

## What counts as a printing

Every official catalogue ID is retained. Numbers such as `EBP01-001OSR` are
preserved exactly; the app also labels the variant `Parallel (OSR)` according
to the official parallel-only query. Promo records are labelled `Promo`.
Unflagged printings are `Standard`, regardless of rarity. In particular, the
SSS Soul printing is included even though the official filter does not mark it
parallel. This avoids guessing foil finishes or inventing missing varieties.

There are 10 Soul entries among the 256 printings. `ESOUL-001` appears in both
trial decks and remains two distinct catalogue records with different official
IDs, set identities, and artwork paths. Null stats on Soul and noncombat cards
are not converted to zero. The PR group has no single release date in the feed.

This covers the current **published English catalogue**, including promos and
all variants that it lists. It does not invent future unrevealed cards or claim
coverage of Japanese-only releases or unlisted event-specific printings.

## Verification and reproducibility

The importer checks that:

- all pages sum to the API's reported total, with unique official IDs;
- every listed product matches an independently fetched set query;
- the official parallel-only and parallel-excluded results form a complete,
  non-overlapping partition of the catalogue;
- set/number/variant keys do not collide;
- every downloaded artwork file is PNG; tests also decode every image.

The snapshot records a retrieval timestamp, content version, per-set counts,
rarity totals, exact source URLs, and factual reference fields. Card ability
text and rulings remain on the official site; the app links directly to each
printing's detail page.

To refresh the snapshot and artwork from the source:

```powershell
python scripts/update_catalogue.py
python -m pytest -q
```

The verification tests deliberately pin this release's counts. When the source
adds printings, review the new counts, update the coverage documentation and
corresponding assertions, then build and publish a new app version. There is no
background network update or runtime dependency on the source website.

To import the bundled snapshot into SQL Server:

```powershell
python scripts/import_catalogue.py
```

Or launch with `python -m palvault --sqlserver --import-catalogue` (packaged:
`Palvault.exe --sqlserver --import-catalogue`). All database changes are in one
transaction and additive. Existing IDs, user-edited records, and collection
entries are retained. The import marker makes repeated imports of the same
snapshot a no-op; the launch flag or script's `--force` option intentionally
restores any missing official catalogue rows. Rebuilding the app packages the
JSON snapshot and all artwork together.

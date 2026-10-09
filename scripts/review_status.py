"""List the rows of the review tables that still need a decision and check the confirmed ones.

Review tables (all in data/):
  seed_exchange_mapping.csv               usable when status is confirmed or no_exchange (F6)
  hm_crop_product_mapping.csv             usable when status is confirmed (F4b)
  hm_fertiliser_row_mapping.csv           usable when status is confirmed (F4c)
  hm_manure_class_mapping.csv             usable when status is confirmed (F4d)
  manure_nh3.csv                          usable when status is confirmed (F3)
  elementary_flow_alignment.csv           done when status is ok, renamed, confirmed or not_needed (F9)
  intermediate_exchange_alignment.csv     idem

A row counts as reviewed when its status is a final status AND the column reviewed_by holds the
reviewer's initials. Exceptions in the alignment tables: "ok" (exact Master Data name) and
"renamed" (Master Data spelling of the same flow; aligning the terminology with the Master Data
was decided by the user on 2026-10-09) need no signature.

With a configured Master Data (agritool.cfg or AGRITOOL_MASTER_DATA_PATH) the script also checks
that every exchange name of the seed mapping exists in the Master Data with the given unit.

Usage (repository root):  python scripts/review_status.py [--all]
    --all  print every open row instead of the first 15 per table
Exit code 0 when everything is reviewed and valid, 1 otherwise.
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "legacy_model"))

import config  # noqa: E402
import dataloader  # noqa: E402

TABLES = [
    # file, final statuses, columns shown for open rows
    ("seed_exchange_mapping.csv", ("confirmed", "no_exchange"), ("crop_key", "seed_exchange_name", "unit", "status", "note")),
    ("hm_crop_product_mapping.csv", ("confirmed",), ("legacy_crop_code", "plant_product_tab5", "status")),
    ("hm_fertiliser_row_mapping.csv", ("confirmed",), ("legacy_fertiliser_type", "tab6_row", "input_to_row_factor", "status", "note")),
    ("hm_manure_class_mapping.csv", ("confirmed",), ("legacy_manure_type", "tab7_manure_class", "share", "status", "note")),
    ("manure_nh3.csv", ("confirmed",), ("manure_type", "tan_kg_n_per_unit", "ef_nh3_n_fraction", "status")),
    ("elementary_flow_alignment.csv", ("renamed", "confirmed", "not_needed"), ("legacy_name", "subcompartment", "status", "md312_name", "candidates")),
    ("intermediate_exchange_alignment.csv", ("renamed", "confirmed", "not_needed"), ("legacy_name", "status", "md312_name", "candidates")),
]


def is_open(row, final_statuses):
    if row.get("status") in ("ok", "renamed"):
        return False
    return row.get("status") not in final_statuses or not row.get("reviewed_by", "").strip()


def main():
    show_all = "--all" in sys.argv
    problems = 0
    for filename, final, columns in TABLES:
        path = dataloader.DATA_DIR / filename
        if not path.is_file():
            print("\n%s: not generated yet (run scripts/check_master_data.py)" % filename)
            problems += 1
            continue
        with open(path, newline="", encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f) if any((v or "").strip() for v in r.values())]
        open_rows = [r for r in rows if is_open(r, final)]
        print("\n%s: %d rows, %d to review" % (filename, len(rows), len(open_rows)))
        for r in (open_rows if show_all else open_rows[:15]):
            print("   " + " | ".join("%s=%s" % (c, r.get(c, "")) for c in columns if r.get(c, "")))
        if len(open_rows) > 15 and not show_all:
            print("   ... %d more (use --all)" % (len(open_rows) - 15))
        problems += len(open_rows)

    path = config.master_data_path()
    if path is not None and path.is_file():
        import seedexchanges
        exchanges = seedexchanges.master_data_exchanges()
        mapping = seedexchanges.load_seed_mapping()
        missing = seedexchanges.validate_seed_mapping(mapping, exchanges)
        units = sorted(r["crop_key"] for r in dataloader.rows("seed_exchange_mapping.csv")
                       if r["seed_exchange_name"] in exchanges and exchanges[r["seed_exchange_name"]].unit != r["unit"])
        print("\nMaster Data %s: seed names not found %s, unit column differs from Master Data %s"
              % (path.name, missing or "none", units or "none"))
        problems += len(missing) + len(units)
    else:
        print("\nMaster Data not configured: names not checked")
    print("\n%s" % ("ALL REVIEWED" if not problems else "%d open item(s)" % problems))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())

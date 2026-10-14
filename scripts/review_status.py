"""List the rows of the review tables that still need a decision and check the confirmed ones.

Review tables (all in data/):
  seed_exchange_mapping.csv               usable when status is confirmed or no_exchange (F6)
  hm_crop_product_mapping_salca2023.csv   usable when status is confirmed (heavy metals, L10)
  hm_coproduct_mapping.csv                idem
  hm_organic_fertiliser_mapping.csv       idem
  hm_fertiliser_row_mapping.csv           usable when status is confirmed (F4c)
  hm_manure_class_mapping.csv             usable when status is confirmed (F4d)
  manure_type_composition.csv             usable when status is confirmed (F3, L12)
  manure_other_faostat_mapping.csv        idem (L13)
  pesticide_crop_archetype_mapping.csv    usable when status is confirmed (pesticide primary distribution)
  faostat_crop_item_mapping.csv           usable when status is confirmed (default yield, L23)
  faostat_country_mapping.csv             idem
  n_uptake_crop_parameters.csv            usable when status is confirmed (default N uptake, L28, L32)
  pk_crop_parameters.csv                  usable when status is confirmed (default mineral P and K, L31)
  ifa_fubc_country_mapping.csv            usable when status is confirmed (IFA fertiliser use by crop, L33)
  ifa_fubc_crop_mapping.csv               idem
  emep2023_fertiliser_type_mapping.csv    usable when status is confirmed (NH3 of mineral N fertilisers, L38)
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
    ("hm_crop_product_mapping_salca2023.csv", ("confirmed",), ("legacy_crop_code", "salca2023_main_product", "status", "note")),
    ("hm_coproduct_mapping.csv", ("confirmed",), ("by_product_label", "salca2023_product", "status")),
    ("hm_organic_fertiliser_mapping.csv", ("confirmed",), ("legacy_fertiliser_type", "salca2023_row", "status", "note")),
    ("hm_fertiliser_row_mapping.csv", ("confirmed",), ("legacy_fertiliser_type", "salca2023_row", "status", "note")),
    ("hm_manure_class_mapping.csv", ("confirmed",), ("legacy_manure_type", "salca2023_class", "share", "status", "note")),
    ("manure_type_composition.csv", ("confirmed",), ("manure_type", "grudaf_row_id", "emep_livestock", "emep_manure_type", "weight", "status")),
    ("manure_other_faostat_mapping.csv", ("confirmed",), ("form", "faostat_item", "manure_type", "status")),
    ("pesticide_crop_archetype_mapping.csv", ("confirmed",), ("crop", "olca_crop_archetype", "status", "note")),
    ("faostat_crop_item_mapping.csv", ("confirmed",), ("crop", "faostat_item_code", "faostat_item", "match", "status")),
    ("faostat_country_mapping.csv", ("confirmed",), ("country", "faostat_area_code", "faostat_area", "status")),
    ("n_uptake_crop_parameters.csv", ("confirmed",), ("crop", "wfldb_crop", "grudaf_crop", "residue_ratio", "tree_residues", "status")),
    ("pk_crop_parameters.csv", ("confirmed",), ("crop", "wfldb_crop", "status", "note")),
    ("ifa_fubc_country_mapping.csv", ("confirmed",), ("country", "fubc_country", "region_ifa", "status", "note")),
    ("ifa_fubc_crop_mapping.csv", ("confirmed",), ("fubc_crop", "crops", "match", "status")),
    ("emep2023_fertiliser_type_mapping.csv", ("confirmed",), ("legacy_fertiliser_type", "emep_fertiliser_type", "status", "note")),
    ("elementary_flow_alignment.csv", ("renamed", "confirmed", "not_needed"), ("legacy_name", "subcompartment", "status", "md312_name", "candidates")),
    ("intermediate_exchange_alignment.csv", ("renamed", "confirmed", "not_needed"), ("legacy_name", "status", "md312_name", "candidates")),
]


def is_open(row, final_statuses):
    if row.get("status") in ("ok", "renamed"):
        return False
    return row.get("status") not in final_statuses or not row.get("reviewed_by", "").strip()


LEGACY_TAG = "legacy, undocumented, provisional"


def print_legacy_tags():
    """List the places kept from the legacy tool without a documented source (decision O7)."""
    print()
    print("Parts marked '%s' (kept from the legacy tool, to be updated):" % LEGACY_TAG)
    for folder, pattern in (("data", "*.csv"), ("src", "*.py")):
        for path in sorted((ROOT / folder).rglob(pattern)):
            if dataloader.EXTERNAL_DATA_DIR in path.parents:
                continue
            text = path.read_text(encoding="utf-8")
            n = text.count(LEGACY_TAG)
            if n and path.name != "sources.csv":
                print("   %-55s %d" % (path.relative_to(ROOT).as_posix(), n))


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

    print_legacy_tags()

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

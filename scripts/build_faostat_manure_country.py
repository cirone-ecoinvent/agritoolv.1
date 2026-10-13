"""Build data/faostat_manure_n_applied_country.csv, the manure N applied to soils per country and livestock item.

Source (decision L29): FAOSTAT domain Emissions from Livestock (GLE), element 72381 "Manure applied to
soils (N content)", kg N, FAO TIER 1, download of 2026-10-10 (the file also used for the world mix of
L13). Countries of the tool are matched by M49 code (data/faostat_country_mapping.csv; CN = China;
mainland, M49 156). The value is the mean over the years of the download that have a value; all items
are kept, the model groups them with data/manure_other_faostat_mapping.csv.

Usage (repository root):
    python scripts/build_faostat_manure_country.py                                # FAOSTAT file in data/external_data/
    python scripts/build_faostat_manure_country.py --faostat <csv> --out <path>   # other download, write elsewhere
"""
import argparse
import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "legacy_model"))

import dataloader  # noqa: E402

FAOSTAT_FILE = "FAOSTAT_data_en_10-10-2026 (1).csv"
ELEMENT = "72381"
UNIT = "kg"
COLUMNS = ["country", "item", "item_code_cpc", "years", "n_years", "n_applied_mean_kg", "flags", "note"]


def read_faostat(path, m49_to_country):
    """{(country, item): {"code": item code, "values": {year: (kg N, flag)}}} for element 72381."""
    out = defaultdict(lambda: {"code": "", "values": {}})
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["Element Code"] != ELEMENT or not row["Value"].strip():
                continue
            country = m49_to_country.get(int(row["Area Code (M49)"]))
            if country is None:
                continue
            if row["Unit"] != UNIT:
                raise ValueError("FAOSTAT unit %r, expected %r" % (row["Unit"], UNIT))
            entry = out[(country, row["Item"])]
            entry["code"] = row["Item Code (CPC)"]
            entry["values"][int(row["Year"])] = (float(row["Value"]), row["Flag"])
    return out


def build(faostat_csv):
    m49_to_country = {int(r["m49_code"]): r["country"] for r in dataloader.rows("faostat_country_mapping.csv")
                      if r["country"] != "GLO"}
    data = read_faostat(faostat_csv, m49_to_country)
    years = sorted({year for entry in data.values() for year in entry["values"]})
    label = "%d-%d" % (years[0], years[-1])
    missing_countries = sorted(set(m49_to_country.values()) - {country for country, _ in data})
    if missing_countries:
        raise ValueError("No FAOSTAT value for %s" % ", ".join(missing_countries))
    rows = []
    for (country, item), entry in sorted(data.items()):
        values = entry["values"]
        flags = defaultdict(int)
        for _, flag in values.values():
            flags[flag] += 1
        missing = [str(y) for y in years if y not in values]
        rows.append({"country": country, "item": item, "item_code_cpc": entry["code"], "years": label,
                     "n_years": len(values), "n_applied_mean_kg": round(statistics.mean(v for v, _ in values.values()), 1),
                     "flags": " ".join("%s:%d" % kv for kv in sorted(flags.items()) if kv[0]),
                     "note": "no value for " + ", ".join(missing) if missing else ""})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--faostat", default=str(dataloader.EXTERNAL_DATA_DIR / FAOSTAT_FILE),
                        help="FAOSTAT GLE download (default: data/external_data/%s)" % FAOSTAT_FILE)
    parser.add_argument("--out", default=str(dataloader.DATA_DIR / "faostat_manure_n_applied_country.csv"))
    args = parser.parse_args()
    rows = build(args.faostat)
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print("%d rows written to %s" % (len(rows), args.out))


if __name__ == "__main__":
    main()

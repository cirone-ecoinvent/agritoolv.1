"""Build data/ecoinvent312_orchard_lifetime.csv, the plantation lifetime implied by the ecoinvent 3.12 datasets of the
perennial crops, decision L50.

Source: ecoinvent 3.12, release file 'exchanges (3.12, undef).xlsx' (sheet 'exchanges'), supplied by FC in
data/external_data/. The undefined release keeps the formulas and comments of the land use exchanges (e.g. cocoa
'10000/613/50', WFLDB 'life time of the perennial crop (20 years)').

For every dataset (activity and geography) of the activities with use 'ecoinvent' or 'proxy' in
data/orchard_lifetime_crop_mapping.csv:
  - occupation = sum of the elementary exchanges 'Occupation, ...' (m2*year per kg);
  - transformation = sum of the elementary exchanges 'Transformation, from ...' (m2 per kg; the land is transformed
    once per plantation);
  - lifetime_years = occupation / transformation;
  - made_with_this_tool = yes when a comment of these exchanges says the value was calculated with the ecoinvent LCI
    calculation tool for crop production (the legacy of this tool: such values are not used as a source).
Only these derived values are stored (no ecoinvent amounts).

Usage (repository root):
    python scripts/build_orchard_lifetime.py
    python scripts/build_orchard_lifetime.py --exchanges <xlsx> --out <path>
"""
import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "legacy_model"))

import dataloader  # noqa: E402

EXCHANGES_FILE = "exchanges (3.12, undef).xlsx"
SHEET = "exchanges"
TOOL_COMMENT = "lci calculation tool"
COLUMNS = ["activity_name", "geography", "lifetime_years", "made_with_this_tool"]


def mapped_activities():
    return {activity for row in dataloader.rows("orchard_lifetime_crop_mapping.csv")
            if row["use"] in ("ecoinvent", "proxy")
            for activity in row["ecoinvent_activities"].split("|") if activity}


def read_exchanges(path, activities):
    """{(activity, geography): dataset} with the land occupation and transformation of the given activities."""
    import openpyxl
    workbook = openpyxl.load_workbook(path, read_only=True)
    rows = workbook[SHEET].iter_rows(values_only=True)
    index = {name: i for i, name in enumerate(next(rows))}
    datasets = defaultdict(lambda: {"occupation": 0.0, "transformation": 0.0, "tool": False})
    for row in rows:
        activity = row[index["activityName"]]
        if activity not in activities or row[index["group"]] != "FromEnvironment":
            continue
        name, unit, amount = (row[index["exchange name"]], row[index["exchange unitName"]],
                              row[index["exchange amount"]])
        if name.startswith("Occupation, "):
            expected, key = "m2*year", "occupation"
        elif name.startswith("Transformation, from "):
            expected, key = "m2", "transformation"
        else:
            continue
        if unit != expected:
            raise ValueError("%s: %s in %r" % (activity, name, unit))
        dataset = datasets[(activity, row[index["geography"]])]
        dataset[key] += amount
        if TOOL_COMMENT in (row[index["exchange comment"]] or "").lower():
            dataset["tool"] = True
    return datasets


def build(path):
    activities = mapped_activities()
    datasets = read_exchanges(path, activities)
    missing = activities - {activity for activity, _ in datasets}
    if missing:
        raise ValueError("activities not found in %s: %s" % (path, sorted(missing)))
    out = []
    for (activity, geography), dataset in sorted(datasets.items()):
        if not dataset["transformation"]:
            raise ValueError("%s %s: no land transformation" % (activity, geography))
        out.append({"activity_name": activity, "geography": geography,
                    "lifetime_years": float("%.4g" % (dataset["occupation"] / dataset["transformation"])),
                    "made_with_this_tool": "yes" if dataset["tool"] else "no"})
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--exchanges", default=str(dataloader.EXTERNAL_DATA_DIR / EXCHANGES_FILE))
    parser.add_argument("--out", default=str(dataloader.DATA_DIR / "ecoinvent312_orchard_lifetime.csv"))
    args = parser.parse_args()
    rows = build(args.exchanges)
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print("%d rows written to %s" % (len(rows), args.out))


if __name__ == "__main__":
    main()

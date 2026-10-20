"""Build data/ecoinvent312_planting_rates.csv, the seedlings and trees planted per ha of the ecoinvent 3.12 crop
datasets, decision L47.

Source: ecoinvent 3.12, system model 'Allocation, cut-off by classification', release file 'exchanges (3.12, cut-off).xlsx'
(sheet 'exchanges'), copied by FC from the ecoinvent release folder to data/external_data/.

For every dataset (activity and geography) of the activities named in data/ecoinvent312_planting_crop_mapping.csv:
  - planting input = sum of the technosphere inputs whose name ends with ', for planting' (unit), per kg of the
    reference product (all reference products of these activities are 1 kg);
  - occupation = sum of the elementary exchanges 'Occupation, ...' (m2*year per kg);
  - transformation = sum of the elementary exchanges 'Transformation, from ...' (m2 per kg);
  - per_ha_and_year = planting input x 10000 / occupation (plants per ha and year of land occupation);
  - per_ha_and_crop_cycle = planting input x 10000 / transformation (plants per ha planted: the land is transformed
    once per planting);
  - lifetime_years = occupation / transformation.
Datasets without a planting input are listed on the screen and not written. Only these derived values per ha are
stored (no ecoinvent amounts per kg).

Usage (repository root):
    python scripts/build_ecoinvent_planting_rates.py
    python scripts/build_ecoinvent_planting_rates.py --exchanges <xlsx> --out <path>
"""
import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "legacy_model"))

import dataloader  # noqa: E402

EXCHANGES_FILE = "exchanges (3.12, cut-off).xlsx"
SHEET = "exchanges"
PLANTING_SUFFIX = ", for planting"
COLUMNS = ["activity_name", "geography", "reference_product", "planting_exchange", "per_ha_and_year",
           "per_ha_and_crop_cycle", "lifetime_years"]


def _round(value, digits=6):
    return float("%.*g" % (digits, value))


def mapped_activities():
    return {activity for row in dataloader.rows("ecoinvent312_planting_crop_mapping.csv")
            for activity in row["ecoinvent_activities"].split("|") if activity}


def read_exchanges(path, activities):
    """{activityId: dataset} with the planting inputs, land use and reference product of the given activities."""
    import openpyxl
    workbook = openpyxl.load_workbook(path, read_only=True)
    rows = workbook[SHEET].iter_rows(values_only=True)
    index = {name: i for i, name in enumerate(next(rows))}
    datasets = defaultdict(lambda: {"planting": defaultdict(float), "occupation": 0.0, "transformation": 0.0,
                                    "reference": []})
    for row in rows:
        activity = row[index["activityName"]]
        if activity not in activities:
            continue
        name, unit, amount = (row[index["exchange name"]], row[index["exchange unitName"]],
                              row[index["exchange amount"]])
        dataset = datasets[row[index["activityId"]]]
        dataset["activity_name"], dataset["geography"] = activity, row[index["geography"]]
        group = row[index["group"]]
        if group == "ReferenceProduct":
            dataset["reference"].append((name, unit, amount))
        elif group == "FromTechnosphere" and name.endswith(PLANTING_SUFFIX):
            if unit != "unit":
                raise ValueError("%s %s: planting input %r in %r" % (activity, dataset["geography"], name, unit))
            dataset["planting"][name] += amount
        elif group == "FromEnvironment" and name.startswith("Occupation, "):
            if unit != "m2*year":
                raise ValueError("%s: occupation in %r" % (activity, unit))
            dataset["occupation"] += amount
        elif group == "FromEnvironment" and name.startswith("Transformation, from "):
            if unit != "m2":
                raise ValueError("%s: transformation in %r" % (activity, unit))
            dataset["transformation"] += amount
    return datasets


def build(path):
    activities = mapped_activities()
    datasets = read_exchanges(path, activities)
    missing = activities - {d["activity_name"] for d in datasets.values()}
    if missing:
        raise ValueError("activities not found in %s: %s" % (path, sorted(missing)))
    out, skipped = [], []
    for dataset in datasets.values():
        if [(unit, amount) for _, unit, amount in dataset["reference"]] != [("kg", 1)]:
            raise ValueError("%s %s: reference product %r" % (dataset["activity_name"], dataset["geography"],
                                                              dataset["reference"]))
        if not dataset["planting"]:
            skipped.append("%s, %s" % (dataset["activity_name"], dataset["geography"]))
            continue
        plants = sum(dataset["planting"].values())
        out.append({"activity_name": dataset["activity_name"], "geography": dataset["geography"],
                    "reference_product": dataset["reference"][0][0],
                    "planting_exchange": "|".join(sorted(dataset["planting"])),
                    "per_ha_and_year": _round(plants * 10000.0 / dataset["occupation"]),
                    "per_ha_and_crop_cycle": _round(plants * 10000.0 / dataset["transformation"]),
                    "lifetime_years": _round(dataset["occupation"] / dataset["transformation"], 4)})
    out.sort(key=lambda row: (row["activity_name"], row["geography"]))
    return out, sorted(skipped)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--exchanges", default=str(dataloader.EXTERNAL_DATA_DIR / EXCHANGES_FILE))
    parser.add_argument("--out", default=str(dataloader.DATA_DIR / "ecoinvent312_planting_rates.csv"))
    args = parser.parse_args()
    rows, skipped = build(args.exchanges)
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print("%d rows written to %s" % (len(rows), args.out))
    print("datasets without a planting input (not written): %s" % ("; ".join(skipped) or "none"))


if __name__ == "__main__":
    main()

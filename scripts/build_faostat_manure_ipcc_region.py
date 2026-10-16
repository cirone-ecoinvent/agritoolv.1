"""Build the IPCC region of the FAOSTAT countries and the manure N applied to soils per IPCC region and in the world
(decision L42).

Sources:
  FAOSTAT domain Emissions from Livestock (GLE), element 72381 "Manure applied to soils (N content)", kg N, FAO
  TIER 1, download of 2026-10-10 (the file of decisions L13 and L29), all 198 areas of the download.
  UNSD, Standard country or area codes for statistical use (M49), overview table downloaded by FC on 2026-10-15
  (data/external_data/UNSD — Methodology.csv): sub-region of each country.
  data/ipcc2019_m49_region_mapping.csv: IPCC 2019 Refinement region (Vol. 4 Annex 10A.2, Tables 10A.6-10A.9) of
  each M49 sub-region, with country exceptions; a country row without region is left out (FAOSTAT 'China' = the
  sum of China, mainland, Taiwan, Hong Kong and Macao, which are in the download as well).

Outputs (data/):
  ipcc2019_country_region.csv                 IPCC region of the FAOSTAT areas
  faostat_manure_n_applied_ipcc_region.csv    N per IPCC region and item: sum of the countries per year, mean
  faostat_manure_n_applied_world.csv          N per item in the world: sum of the countries per year, mean

Usage (repository root):
    python scripts/build_faostat_manure_ipcc_region.py
    python scripts/build_faostat_manure_ipcc_region.py --faostat <csv> --m49 <csv> --out-dir <dir>
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
M49_FILE = "UNSD — Methodology.csv"
ELEMENT = "72381"
UNIT = "kg"
MAPPING = "ipcc2019_m49_region_mapping.csv"
COUNTRY_OUTPUT = "ipcc2019_country_region.csv"
REGION_OUTPUT = "faostat_manure_n_applied_ipcc_region.csv"
WORLD_OUTPUT = "faostat_manure_n_applied_world.csv"
COUNTRY_COLUMNS = ["m49_code", "faostat_area", "m49_subregion", "ipcc_region", "rule"]


def read_faostat(path):
    """({m49: area}, {(m49, item): {"code": item code, "values": {year: kg N}}}) for element 72381."""
    areas = {}
    data = defaultdict(lambda: {"code": "", "values": {}})
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["Element Code"] != ELEMENT:
                continue
            m49 = int(row["Area Code (M49)"])
            areas[m49] = row["Area"]
            if not row["Value"].strip():
                continue
            if row["Unit"] != UNIT:
                raise ValueError("FAOSTAT unit %r, expected %r" % (row["Unit"], UNIT))
            entry = data[(m49, row["Item"])]
            entry["code"] = row["Item Code (CPC)"]
            entry["values"][int(row["Year"])] = float(row["Value"])
    return areas, data


def read_m49(path):
    """{m49: (sub-region code, sub-region name)} from the UNSD overview table (semicolon separated)."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        return {int(row["M49 Code"]): (row["Sub-region Code"], row["Sub-region Name"])
                for row in csv.DictReader(f, delimiter=";")}


def country_regions(areas, m49):
    """One row per FAOSTAT area: IPCC region from the country row of the mapping, else from its M49 sub-region."""
    subregions, countries = {}, {}
    for row in dataloader.rows(MAPPING):
        (subregions if row["level"] == "subregion" else countries)[int(row["m49_code"])] = row["ipcc_region"]
    rows = []
    for code, area in sorted(areas.items()):
        subregion = m49.get(code, ("", ""))
        if code in countries:
            region, rule = countries[code], "country" if countries[code] else "excluded"
        elif subregion[0] and int(subregion[0]) in subregions:
            region, rule = subregions[int(subregion[0])], "subregion"
        else:
            raise ValueError("No IPCC region for FAOSTAT area %s (M49 %03d)" % (area, code))
        rows.append({"m49_code": "%03d" % code, "faostat_area": area, "m49_subregion": subregion[1],
                     "ipcc_region": region, "rule": rule})
    return rows


def sums(data, years, region_of, by_region):
    """Rows of N per item (and IPCC region): sum of the areas per year, mean over the years, number of areas with a
    value. Areas without region are left out."""
    groups = defaultdict(lambda: {"code": "", "years": defaultdict(float), "areas": 0})
    for (m49, item), entry in data.items():
        if not region_of[m49]:
            continue
        group = groups[(region_of[m49] if by_region else "", item)]
        group["code"] = entry["code"]
        group["areas"] += 1
        for year, value in entry["values"].items():
            group["years"][year] += value
    rows = []
    for (region, item), group in sorted(groups.items()):
        row = {"ipcc_region": region, "item": item} if by_region else {"item": item}
        row["item_code_cpc"] = group["code"]
        for year in years:
            row["n_applied_%d_kg" % year] = round(group["years"][year], 1)
        row["n_applied_mean_%d_%d_kg" % (years[0], years[-1])] = round(
            statistics.mean(group["years"][year] for year in years), 1)
        row["n_countries"] = group["areas"]
        rows.append(row)
    return rows


def build(faostat_csv, m49_csv):
    """(country rows, region rows, world rows)."""
    areas, data = read_faostat(faostat_csv)
    countries = country_regions(areas, read_m49(m49_csv))
    region_of = {int(row["m49_code"]): row["ipcc_region"] for row in countries}
    years = sorted({year for entry in data.values() for year in entry["values"]})
    return countries, sums(data, years, region_of, True), sums(data, years, region_of, False)


def write(rows, path):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--faostat", default=str(dataloader.EXTERNAL_DATA_DIR / FAOSTAT_FILE))
    parser.add_argument("--m49", default=str(dataloader.EXTERNAL_DATA_DIR / M49_FILE))
    parser.add_argument("--out-dir", type=Path, default=dataloader.DATA_DIR)
    args = parser.parse_args()
    countries, regions, world = build(args.faostat, args.m49)
    for rows, name in ((countries, COUNTRY_OUTPUT), (regions, REGION_OUTPUT), (world, WORLD_OUTPUT)):
        write(rows, args.out_dir / name)
        print("%d rows written to %s" % (len(rows), args.out_dir / name))


if __name__ == "__main__":
    main()

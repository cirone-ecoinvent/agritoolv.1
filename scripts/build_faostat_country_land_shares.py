"""Build data/faostat_country_land_shares.csv: shares of agricultural land, forest land and inland waters per country
and per M49 region, used to distribute the OLCA-Pest emissions to off-field surfaces (decision L65).

Source: FAOSTAT, Land Use (domain RL), bulk download Inputs_LandUse_E_All_Data_(Normalized).zip, accessed 2026-11-06,
element 5110 Area (1000 ha), items 6600 Country area, 6610 Agricultural land, 6646 Forest land, 6680 Inland waters.
One year only, never mixed: by default the most recent year with Country area, Agricultural land and Forest land for
the World (2024 in this download; 2025 has Forest land only).

Method of the OLCApest mapping tool (Land area countries.xlsx, sheet Full1; OLCA CALC rows 3-5):
    agri = Agricultural land / Country area, forest = Forest land / Country area, water = Inland waters / Country area
    (missing Inland waters = 0);
    delta = agri + forest + water - 1;
    agri_share = agri - delta x agri / (agri + forest); forest_share = forest - delta x forest / (agri + forest);
    water_share = water.
The three shares sum to 1. An area without Country area, Agricultural land or Forest land, or with agri + forest = 0,
gets no shares (empty cells; the model falls back to its sub-region, region, then World).

Rows:
- area_type country: FAOSTAT areas with an area code below 5000 whose M49 code is a country of the UNSD M49 file
  (data/external_data/UNSD — Methodology.csv), with its ISO alpha-2 code ("NA" = Namibia is a code, not a missing
  value). subregion_m49 = the UNSD intermediate region if FAOSTAT publishes it, else the UNSD sub-region if FAOSTAT
  publishes it; region_m49 = the UNSD region.
- area_type region / subregion / world: FAOSTAT aggregates (area code >= 5000) whose M49 code is a UNSD region,
  sub-region or intermediate region, and the World (M49 001). Other aggregates (European Union, LDCs, OECD...) are
  left out.
The FAOSTAT flags of the four values are kept.

Usage (repository root):
    .venv\\Scripts\\python scripts\\build_faostat_country_land_shares.py [--year 2024] [--faostat ZIP] [--m49 CSV]
                                                                       [--out CSV]
"""
import argparse
import csv
import io
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "legacy_model"))

import dataloader  # noqa: E402

FAOSTAT_ZIP = dataloader.EXTERNAL_DATA_DIR / "Inputs_LandUse_E_All_Data_(Normalized).zip"
M49_FILE = dataloader.EXTERNAL_DATA_DIR / "UNSD — Methodology.csv"
OUTPUT = dataloader.DATA_DIR / "faostat_country_land_shares.csv"
ELEMENT_AREA = "5110"
UNIT = "1000 ha"
ITEMS = {"6600": "country_area", "6610": "agricultural_land", "6646": "forest_land", "6680": "inland_waters"}
REQUIRED = ("country_area", "agricultural_land", "forest_land")
WORLD_M49 = 1
FIRST_AGGREGATE_CODE = 5000
COLUMNS = ["area_type", "iso2", "m49_code", "faostat_area_code", "area", "subregion_m49", "region_m49", "year"] \
    + [c for item in ITEMS.values() for c in ("%s_1000ha" % item, "%s_flag" % item)] \
    + ["agri_share", "forest_share", "water_share", "note"]


def read_m49(path):
    """UNSD M49 file: ({country M49: row}, set of region, sub-region and intermediate region M49 codes)."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    countries = {int(r["M49 Code"]): r for r in rows}
    groups = {int(r[c]) for r in rows for c in ("Region Code", "Sub-region Code", "Intermediate Region Code")
              if r[c].strip()}
    return countries, groups


def read_faostat(path):
    """{year: {(area code, M49, area): {item: (value 1000 ha, flag)}}} for element Area of the four items."""
    out = {}
    with zipfile.ZipFile(path) as z:
        name = next(n for n in z.namelist() if n.endswith("All_Data_(Normalized).csv"))
        with z.open(name) as raw:
            for row in csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8", newline="")):
                if row["Element Code"] != ELEMENT_AREA or row["Item Code"] not in ITEMS or not row["Value"].strip():
                    continue
                if row["Unit"] != UNIT:
                    raise ValueError("FAOSTAT unit %r, expected %r" % (row["Unit"], UNIT))
                area = (int(row["Area Code"]), int(row["Area Code (M49)"].lstrip("'")), row["Area"])
                out.setdefault(int(row["Year"]), {}).setdefault(area, {})[ITEMS[row["Item Code"]]] = \
                    (float(row["Value"]), row["Flag"])
    return out


def latest_complete_year(data):
    """Most recent year with Country area, Agricultural land and Forest land for the World."""
    years = [y for y, areas in data.items()
             for (code, m49, _), items in areas.items() if m49 == WORLD_M49 and all(i in items for i in REQUIRED)]
    return max(years)


def shares(agricultural_land, forest_land, inland_waters, country_area):
    """(agri_share, forest_share, water_share) of the OLCApest mapping tool; None if they cannot be computed."""
    agri, forest = agricultural_land / country_area, forest_land / country_area
    water = inland_waters / country_area
    if agri + forest <= 0.0:
        return None
    delta = agri + forest + water - 1.0
    return agri - delta * agri / (agri + forest), forest - delta * forest / (agri + forest), water


def build(year=None, faostat_zip=FAOSTAT_ZIP, m49_file=M49_FILE):
    countries, groups = read_m49(m49_file)
    data = read_faostat(faostat_zip)
    year = year or latest_complete_year(data)
    areas = data[year]
    published = {m49 for (code, m49, _) in areas if code >= FIRST_AGGREGATE_CODE}
    rows = []
    for (code, m49, name), items in sorted(areas.items(), key=lambda a: (a[0][0] < FIRST_AGGREGATE_CODE, a[0][2])):
        if code >= FIRST_AGGREGATE_CODE:
            if m49 != WORLD_M49 and m49 not in groups:
                continue
            area_type, iso2, subregion, region = _aggregate_type(m49, countries), "", "", ""
        else:
            if m49 not in countries:
                continue
            m = countries[m49]
            area_type, iso2 = "country", m["ISO-alpha2 Code"]
            subregion = next((m[c] for c in ("Intermediate Region Code", "Sub-region Code")
                              if m[c].strip() and int(m[c]) in published), "")
            region = m["Region Code"]
        row = {"area_type": area_type, "iso2": iso2, "m49_code": "%03d" % m49, "faostat_area_code": code,
               "area": name, "subregion_m49": subregion, "region_m49": region, "year": year, "note": ""}
        for item in ITEMS.values():
            value, flag = items.get(item, ("", ""))
            row["%s_1000ha" % item], row["%s_flag" % item] = value, flag
        missing = [item for item in REQUIRED if item not in items]
        result = None if missing else shares(items["agricultural_land"][0], items["forest_land"][0],
                                             items.get("inland_waters", (0.0, ""))[0], items["country_area"][0])
        if missing:
            row["note"] = "no %s in %d: no shares" % (" and ".join(m.replace("_", " ") for m in missing), year)
        elif result is None:
            row["note"] = "agricultural and forest land 0: no shares"
        else:
            row["agri_share"], row["forest_share"], row["water_share"] = ("%.9f" % s for s in result)
            if "inland_waters" not in items:
                row["note"] = "no inland waters value: 0"
        rows.append(row)
    return year, rows


def _aggregate_type(m49, countries):
    if m49 == WORLD_M49:
        return "world"
    if any(int(r["Region Code"]) == m49 for r in countries.values() if r["Region Code"].strip()):
        return "region"
    return "subregion"


def write(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, help="FAOSTAT year (default: most recent complete year)")
    parser.add_argument("--faostat", default=str(FAOSTAT_ZIP))
    parser.add_argument("--m49", default=str(M49_FILE))
    parser.add_argument("--out", default=str(OUTPUT))
    args = parser.parse_args()
    year, rows = build(args.year, args.faostat, args.m49)
    write(rows, args.out)
    print("written %s: year %d, %d rows (%d without shares)"
          % (args.out, year, len(rows), sum(1 for r in rows if not r.get("agri_share"))))


if __name__ == "__main__":
    main()

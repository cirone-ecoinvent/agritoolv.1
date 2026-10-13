"""Build data/default_yield.csv, the default yield per crop and country, from a FAOSTAT download.

Method (decision L23; WFLDB Guidelines v3.0, section 3.2.1): FAOSTAT yield (element 5412, kg/ha)
of the crop's item (data/faostat_crop_item_mapping.csv), mean of the latest 4 years of the
download, per country of the tool (data/faostat_country_mapping.csv); GLO = FAOSTAT World
(World production / area harvested when FAOSTAT reports no World yield for the item). When the
tool's product differs from the FAOSTAT item (tea: made tea vs green leaf), the yield is divided
by faostat_kg_per_kg_product of the mapping.
The mean is taken over the years that have a value; a country without any value gets no row
(the tool then uses GLO). Crops mapped to no item keep the legacy default 0 (no default yield).

Usage (repository root):
    python scripts/build_default_yield.py --faostat "C:/python/external_data/Production_Crops_Livestock_E_All_Data_(Normalized).csv"
    python scripts/build_default_yield.py --faostat <csv> --out <path>   # write elsewhere (review)
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

YIELD_ELEMENT = "5412"
YIELD_UNIT = "kg/ha"
PRODUCTION = ("5510", "t")
AREA_HARVESTED = ("5312", "ha")
N_YEARS = 4
LEGACY_TAG = "legacy, undocumented, provisional"
COLUMNS = ["crop", "country", "yield_kg_per_ha_year", "years", "n_years", "faostat_item_code", "flags", "note"]


def read_faostat(path, items, areas, world):
    """Yields {(item, area): {year: (kg/ha, flag)}} and, for the World, production and area harvested
    {(element, item): {year: value}} (used when FAOSTAT reports no World yield)."""
    yields = defaultdict(dict)
    world_totals = defaultdict(dict)
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["Item Code"] not in items or not row["Value"].strip():
                continue
            element = row["Element Code"]
            if element == YIELD_ELEMENT and row["Area Code"] in areas:
                if row["Unit"] != YIELD_UNIT:
                    raise ValueError("FAOSTAT yield unit %r, expected %r" % (row["Unit"], YIELD_UNIT))
                yields[(row["Item Code"], row["Area Code"])][int(row["Year"])] = (float(row["Value"]), row["Flag"])
            elif row["Area Code"] == world and (element, row["Unit"]) in (PRODUCTION, AREA_HARVESTED):
                world_totals[(element, row["Item Code"])][int(row["Year"])] = float(row["Value"])
    return yields, world_totals


def world_yield_from_totals(world_totals, item, years):
    """{year: (kg/ha, "")} = World production (t) x 1000 / World area harvested (ha)."""
    production = world_totals.get((PRODUCTION[0], item), {})
    area = world_totals.get((AREA_HARVESTED[0], item), {})
    return {y: (production[y] * 1000.0 / area[y], "") for y in years
            if production.get(y, 0) > 0 and area.get(y, 0) > 0}


def build(faostat_csv):
    crops = dataloader.rows("faostat_crop_item_mapping.csv")
    countries = dataloader.rows("faostat_country_mapping.csv")
    items = {r["faostat_item_code"] for r in crops if r["faostat_item_code"]}
    areas = {r["faostat_area_code"] for r in countries}
    world = next(r["faostat_area_code"] for r in countries if r["country"] == "GLO")
    yields, world_totals = read_faostat(faostat_csv, items, areas, world)
    last = max(year for series in yields.values() for year in series)
    years = list(range(last - N_YEARS + 1, last + 1))
    label = "%d-%d" % (years[0], years[-1])
    rows = []
    for crop in crops:
        if not crop["faostat_item_code"]:
            rows.append({"crop": crop["crop"], "country": "GLO", "yield_kg_per_ha_year": 0.0, "years": "",
                         "n_years": 0, "faostat_item_code": "", "flags": "",
                         "note": "no FAOSTAT item; 0 = no default yield, as in the legacy matrix; " + LEGACY_TAG})
            continue
        for country in countries:
            series = yields.get((crop["faostat_item_code"], country["faostat_area_code"]), {})
            source = ""
            if country["country"] == "GLO" and not any(y in series for y in years):
                series = world_yield_from_totals(world_totals, crop["faostat_item_code"], years)
                source = "no FAOSTAT World yield: World production / area harvested; "
            values = [series[y] for y in years if y in series and series[y][0] > 0]
            if not values:
                continue
            flags = defaultdict(int)
            for _, flag in values:
                flags[flag] += 1
            missing = [str(y) for y in years if y not in series or series[y][0] <= 0]
            factor = float(crop["faostat_kg_per_kg_product"] or 1.0)
            if factor != 1.0:
                source += "FAOSTAT yield / %s (faostat_kg_per_kg_product); " % crop["faostat_kg_per_kg_product"]
            rows.append({"crop": crop["crop"], "country": country["country"],
                         "yield_kg_per_ha_year": round(statistics.mean(v for v, _ in values) / factor, 3),
                         "years": label, "n_years": len(values), "faostat_item_code": crop["faostat_item_code"],
                         "flags": " ".join("%s:%d" % kv for kv in sorted(flags.items()) if kv[0]),
                         "note": (source + ("no value for " + ", ".join(missing) if missing else "")).rstrip("; ")})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--faostat", required=True, help="FAOSTAT Production_Crops_Livestock_E_All_Data_(Normalized).csv")
    parser.add_argument("--out", default=str(dataloader.DATA_DIR / "default_yield.csv"))
    args = parser.parse_args()
    rows = build(args.faostat)
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print("%d rows written to %s" % (len(rows), args.out))


if __name__ == "__main__":
    main()

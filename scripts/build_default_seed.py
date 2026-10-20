"""Build data/default_seed.csv, the default seed per crop and country (kg/ha and crop cycle), decision L46.

Sources:
  - FAOSTAT Supply Utilization Accounts (SUA), domain 'Supply Utilization Accounts' (crops and livestock), element
    5525 Seed (t), bulk download data/external_data/SUA_Crops_Livestock_E_All_Data_(Normalized).zip;
  - FAOSTAT QCL, element 5312 Area harvested (ha), data/external_data/Production_Crops_Livestock_E_All_Data_
    (Normalized).csv (the download of the default yield, L23);
  - FAO Technical Conversion Factors for Agricultural Commodities (seeding rates, kg/ha, national averages
    1992-1996), extracted into data/fao_tcf_seed_rates.csv.

Method, for the crops of data/seed_rate_crop_mapping.csv with use 'sua_tcf':
  1. SUA rate = mean over the years 2021-2023 of seed(t) x 1000 / area harvested(t + 1). FAO computes the SUA seed of
     year t as seeding rate x area sown in year t + 1 (FAOSTAT, New Food Balances, description of utilization
     variables, section V Seed); years with no seed or no area are skipped. GLO = FAOSTAT World.
  2. Country with a TCF rate: SUA rate when it lies within a factor seed_rate_max_ratio (model_parameters.csv) of the
     TCF rate, otherwise the TCF rate.
  3. Country without a TCF rate: SUA rate when it lies within that factor of the GLO rate, otherwise the GLO rate.
  4. Country without either: GLO rate.
Output: one row per crop and country of data/faostat_country_mapping.csv (GLO included), with the source of the
value (faostat_sua, fao_tcf, glo), the SUA and TCF rates and the SUA flags.

Usage (repository root):
    python scripts/build_default_seed.py
    python scripts/build_default_seed.py --sua <zip> --qcl <csv> --out <path>
"""
import argparse
import csv
import io
import statistics
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "legacy_model"))

import dataloader  # noqa: E402

SUA_FILE = "SUA_Crops_Livestock_E_All_Data_(Normalized).zip"
SUA_MEMBER = "SUA_Crops_Livestock_E_All_Data_(Normalized).csv"
QCL_FILE = "Production_Crops_Livestock_E_All_Data_(Normalized).csv"
SEED = ("5525", "t")
AREA_HARVESTED = ("5312", "ha")
SEED_YEARS = (2021, 2022, 2023)
COLUMNS = ["crop", "country", "seed_kg_per_ha", "source", "sua_kg_per_ha", "sua_n_years", "sua_flags", "tcf_kg_per_ha",
           "note"]


def read_sua(path, items, areas):
    """{(item, area): {year: (t, flag)}} of the SUA element Seed."""
    seed = defaultdict(dict)
    with zipfile.ZipFile(path) as z, z.open(SUA_MEMBER) as f:
        for row in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", errors="replace", newline="")):
            if (row["Element Code"] != SEED[0] or row["Item Code"] not in items or row["Area Code"] not in areas
                    or not row["Value"].strip()):
                continue
            if row["Unit"] != SEED[1]:
                raise ValueError("SUA seed unit %r, expected %r" % (row["Unit"], SEED[1]))
            seed[(row["Item Code"], row["Area Code"])][int(row["Year"])] = (float(row["Value"]), row["Flag"])
    return seed


def read_area(path, items, areas):
    """{(item, area): {year: ha}} of the QCL element Area harvested."""
    area = defaultdict(dict)
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if (row["Element Code"] != AREA_HARVESTED[0] or row["Item Code"] not in items
                    or row["Area Code"] not in areas or not row["Value"].strip()):
                continue
            if row["Unit"] != AREA_HARVESTED[1]:
                raise ValueError("QCL area unit %r, expected %r" % (row["Unit"], AREA_HARVESTED[1]))
            area[(row["Item Code"], row["Area Code"])][int(row["Year"])] = float(row["Value"])
    return area


def sua_rate(seed, area):
    """(kg/ha rounded to 3 decimals, number of years, flags) or (None, 0, "")."""
    values = [(seed[y][0] * 1000.0 / area[y + 1], seed[y][1]) for y in SEED_YEARS
              if seed.get(y, (0.0,))[0] > 0 and area.get(y + 1, 0.0) > 0]
    if not values:
        return None, 0, ""
    flags = defaultdict(int)
    for _, flag in values:
        flags[flag] += 1
    return (round(statistics.mean(v for v, _ in values), 3), len(values),
            " ".join("%s:%d" % kv for kv in sorted(flags.items()) if kv[0]))


def choose(sua, tcf, glo, factor):
    """(seed rate, source, note) by steps 2-4 of the method."""
    if tcf is not None:
        if sua is not None and 1.0 / factor <= sua / tcf <= factor:
            return sua, "faostat_sua", ""
        if sua is None:
            return tcf, "fao_tcf", "no SUA value"
        return tcf, "fao_tcf", "SUA rate not within x%g of the TCF rate" % factor
    if sua is not None:
        if 1.0 / factor <= sua / glo <= factor:
            return sua, "faostat_sua", "no TCF rate; SUA rate within x%g of GLO" % factor
        return glo, "glo", "no TCF rate; SUA rate not within x%g of GLO" % factor
    return glo, "glo", "no SUA value and no TCF rate"


def tcf_rates(crops):
    """{(crop, country): kg/ha} from fao_tcf_seed_rates.csv through the tcf_items of the mapping."""
    item_crop = {item: crop["crop"] for crop in crops for item in crop["tcf_items"].split("|") if item}
    rates = {}
    for row in dataloader.rows("fao_tcf_seed_rates.csv"):
        key = (item_crop[row["tcf_item"]], row["country"])
        if key in rates:
            raise ValueError("fao_tcf_seed_rates.csv: two rates for %s" % (key,))
        rates[key] = float(row["seed_rate_kg_per_ha"])
    return rates


def build(sua_zip, qcl_csv):
    crops = [row for row in dataloader.rows("seed_rate_crop_mapping.csv") if row["use"] == "sua_tcf"]
    countries = dataloader.rows("faostat_country_mapping.csv")
    areas = {row["faostat_area_code"] for row in countries}
    world = next(row["faostat_area_code"] for row in countries if row["country"] == "GLO")
    seed = read_sua(sua_zip, {row["faostat_seed_item_code"] for row in crops}, areas)
    area = read_area(qcl_csv, {row["faostat_area_item_code"] for row in crops}, areas)
    tcf = tcf_rates(crops)
    factor = dataloader.param("seed_rate_max_ratio")
    out = []
    for crop in crops:
        def rate(area_code):
            return sua_rate(seed.get((crop["faostat_seed_item_code"], area_code), {}),
                            area.get((crop["faostat_area_item_code"], area_code), {}))
        glo, glo_years, glo_flags = rate(world)
        if glo is None:
            raise ValueError("no FAOSTAT World seed rate for %s" % crop["crop"])
        for country in countries:
            if country["country"] == "GLO":
                value, source, note, (sua, n_years, flags), tcf_value = glo, "faostat_sua", "FAOSTAT World", \
                    (glo, glo_years, glo_flags), None
            else:
                sua, n_years, flags = rate(country["faostat_area_code"])
                tcf_value = tcf.get((crop["crop"], country["country"]))
                value, source, note = choose(sua, tcf_value, glo, factor)
            out.append({"crop": crop["crop"], "country": country["country"], "seed_kg_per_ha": value,
                        "source": source, "sua_kg_per_ha": "" if sua is None else sua, "sua_n_years": n_years,
                        "sua_flags": flags, "tcf_kg_per_ha": "" if tcf_value is None else tcf_value, "note": note})
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sua", default=str(dataloader.EXTERNAL_DATA_DIR / SUA_FILE))
    parser.add_argument("--qcl", default=str(dataloader.EXTERNAL_DATA_DIR / QCL_FILE))
    parser.add_argument("--out", default=str(dataloader.DATA_DIR / "default_seed.csv"))
    args = parser.parse_args()
    rows = build(args.sua, args.qcl)
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print("%d rows written to %s" % (len(rows), args.out))


if __name__ == "__main__":
    main()

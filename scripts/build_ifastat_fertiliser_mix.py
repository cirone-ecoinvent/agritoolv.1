"""Build data/ifastat_fertiliser_mix.csv, the mineral fertiliser mix per country (decision L45).

Source: International Fertilizer Association (IFA), IFASTAT, indicator 'Fertilizer consumption' by product and
nutrient ('000 t N, P2O5, K2O; consumption for plant nutrition), export of 2026-10-19 downloaded by FC with an IFASTAT
account (data/external_data/ifastat-data-2026-10-19.csv). The IFASTAT values are reserved for IFA members: only the
derived shares are stored in the repository (FC decision 2026-10-19), the export stays in data/external_data/.

For the countries of data/ifastat_country_mapping.csv: sum of the years 2021-2023 per product and nutrient, assigned to
the tool fertiliser types by data/ifastat_product_type_mapping.csv (fractions such as 1/3 allowed; products without a
type are left out), divided by the sum over the types of the nutrient. A country without consumption of the mapped
products of a nutrient (FI: potassium only in NPK) takes the world mix: the same sum over all countries and regions of
the export. Output: one row per country, nutrient (N, P2O5, K2O) and tool fertiliser type, share rounded to 6
significant digits, note.

Usage (repository root):
    python scripts/build_ifastat_fertiliser_mix.py
    python scripts/build_ifastat_fertiliser_mix.py --ifastat <csv> --out <path>
"""
import argparse
import csv
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "legacy_model"))

import dataloader  # noqa: E402
from models.fertilisermodel import NFertiliserType, PFertiliserType, KFertiliserType  # noqa: E402

IFASTAT_FILE = "ifastat-data-2026-10-19.csv"
INDICATOR = "Fertilizer consumption"
YEARS = (2021, 2022, 2023)
NUTRIENTS = {  # IFASTAT nutrient -> (basis of the tool, IFASTAT unit, tool fertiliser types)
    "Nitrogen": ("N", "'000 tonnes N", NFertiliserType),
    "Phosphorus": ("P2O5", "'000 tonnes P2O5", PFertiliserType),
    "Potassium": ("K2O", "'000 tonnes K2O", KFertiliserType),
}
COLUMNS = ["country", "nutrient", "fertiliser_type", "share", "note"]
WORLD = "world"
WORLD_NOTE = ("world mix (all countries and regions of the export): no consumption of the mapped products of the "
              "nutrient in the country")


def _sig(value, digits=6):
    return float("%.*g" % (digits, value))


def _mapping():
    mapping = {}
    for row in dataloader.rows("ifastat_product_type_mapping.csv"):
        types = mapping.setdefault((row["ifastat_nutrient"], row["ifastat_product"]), [])
        if row["fertiliser_type"]:
            fertiliser_type = NUTRIENTS[row["ifastat_nutrient"]][2](row["fertiliser_type"])
            types.append((fertiliser_type, Fraction(row["fraction"])))
    for key, types in mapping.items():
        if types and sum(fraction for _, fraction in types) != 1:
            raise ValueError("ifastat_product_type_mapping.csv: fractions of %s do not sum to 1" % (key,))
    return mapping


def read_ifastat(path, countries):
    """{(country or WORLD, IFASTAT nutrient, product): '000 t summed over YEARS}, checking units and years."""
    totals, years = {}, {}
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["Indicator"] != INDICATOR or int(row["Year"]) not in YEARS:
                continue
            if row["Unit"] != NUTRIENTS[row["Nutrient"]][1]:
                raise ValueError("%s: unit %r for %s" % (path, row["Unit"], row["Nutrient"]))
            for country in (countries.get(row["Country Alpha-3 code"]), WORLD):
                if country is not None:
                    key = (country, row["Nutrient"], row["Product"])
                    totals[key] = totals.get(key, 0.0) + float(row["Value"])
                    years.setdefault(country, set()).add(int(row["Year"]))
    missing = {country: sorted(set(YEARS) - years.get(country, set())) for country in countries.values()
               if set(YEARS) - years.get(country, set())}
    if missing:
        raise ValueError("%s: years missing %s" % (path, missing))
    return totals


def build(ifastat_csv):
    countries = {row["ifastat_alpha3"]: row["country"] for row in dataloader.rows("ifastat_country_mapping.csv")}
    mapping = _mapping()
    totals = read_ifastat(ifastat_csv, countries)
    unmapped = sorted({key[1:] for key in totals} - set(mapping))
    if unmapped:
        raise ValueError("products not in ifastat_product_type_mapping.csv: %s" % unmapped)
    out = []
    for country in sorted(countries.values()):
        for nutrient, (basis, _, fertiliser_types) in NUTRIENTS.items():
            amounts, note = _amounts(totals, mapping, country, nutrient, fertiliser_types), ""
            if sum(amounts.values()) <= 0:
                amounts, note = _amounts(totals, mapping, WORLD, nutrient, fertiliser_types), WORLD_NOTE
            total = sum(amounts.values())
            out.extend({"country": country, "nutrient": basis, "fertiliser_type": fertiliser_type.value,
                        "share": _sig(amount / total), "note": note} for fertiliser_type, amount in amounts.items())
    return out


def _amounts(totals, mapping, country, nutrient, fertiliser_types):
    amounts = {fertiliser_type: 0.0 for fertiliser_type in fertiliser_types}
    for (c, n, product), value in totals.items():
        if c == country and n == nutrient:
            for fertiliser_type, fraction in mapping[(n, product)]:
                amounts[fertiliser_type] += value * float(fraction)
    return amounts


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ifastat", default=str(dataloader.EXTERNAL_DATA_DIR / IFASTAT_FILE))
    parser.add_argument("--out", default=str(dataloader.DATA_DIR / "ifastat_fertiliser_mix.csv"))
    args = parser.parse_args()
    rows = build(args.ifastat)
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print("%d rows written to %s" % (len(rows), args.out))


if __name__ == "__main__":
    main()

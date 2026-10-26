"""Build data/ifastat_fertiliser_time_factor.csv, the factor that brings the IFA Fertilizer Use by Crop rates to
2021-2023 (decision L53; before: FAOSTAT RFN use per area of cropland, decisions L33, L35).

Source: International Fertilizer Association (IFA), IFASTAT, indicator 'Fertilizer consumption' by product and
nutrient ('000 t N, P2O5, K2O), export of 2026-10-19 downloaded by FC (data/external_data/ifastat-data-2026-10-19.csv).
The IFASTAT values are reserved for IFA members: only the derived ratios are stored in the repository (FC decision
2026-10-26, as for L45), the export stays in data/external_data/.

Factor = consumption of the country summed over the products, mean over 2021-2023 / mean over the base years.
Base years (decision L35): the FUBC 9 reference years of the country with the year before and after; the countries
without FUBC 9 data (earlier FUBC report only, or no FUBC data: GH, CS) take the most frequent FUBC 9 reference year
with the year before and after. Countries: all FUBC countries of data/ifa_fubc_rates.csv (IFASTAT country from
data/ifastat_fubc_country_mapping.csv; FUBC 9 countries outside the tool give the upper bound of the region rates,
decision L53) and the tool countries without FUBC data (data/ifastat_country_mapping.csv). A country missing in the
export, without a value in one of the years or without consumption in the base years gets no factor (note).

Usage (repository root):
    python scripts/build_ifastat_time_factor.py
    python scripts/build_ifastat_time_factor.py --ifastat <csv> --out <path>
"""
import argparse
import csv
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "legacy_model"))

import dataloader  # noqa: E402

IFASTAT_FILE = "ifastat-data-2026-10-19.csv"
INDICATOR = "Fertilizer consumption"
LATEST_REPORT = "9"
TARGET_YEARS = (2021, 2022, 2023)
BASE_WINDOW = (-1, 0, 1)  # years around the reference year of the FUBC data (decision L35)
NUTRIENTS = {"Nitrogen": ("N", "'000 tonnes N"), "Phosphorus": ("P2O5", "'000 tonnes P2O5"),
             "Potassium": ("K2O", "'000 tonnes K2O")}
COLUMNS = ["country", "fubc_country", "ifastat_alpha3", "nutrient", "base_years", "target_years", "factor", "note"]
REGION_ONLY_NOTE = "for the region rates only (decision L37)"


def read_ifastat(path):
    """{(alpha-3 code, nutrient of the tool, year): '000 t summed over the products}, checking the units."""
    totals = {}
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["Indicator"] != INDICATOR:
                continue
            nutrient, unit = NUTRIENTS[row["Nutrient"]]
            if row["Unit"] != unit:
                raise ValueError("%s: unit %r for %s" % (path, row["Unit"], row["Nutrient"]))
            key = (row["Country Alpha-3 code"], nutrient, int(row["Year"]))
            totals[key] = totals.get(key, 0.0) + float(row["Value"])
    return totals


def _countries():
    """[(tool country or '', FUBC country or '', alpha-3 code or '', base years, note)]"""
    rates = dataloader.rows("ifa_fubc_rates.csv")
    reference = {}
    for row in rates:
        if row["fubc_report"] == LATEST_REPORT:
            reference.setdefault(row["fubc_country"], set()).add(int(row["reference_years"]))
    fallback = int(Counter(row["reference_years"] for row in rates
                           if row["fubc_report"] == LATEST_REPORT).most_common(1)[0][0])
    tool_rows = dataloader.rows("ifa_fubc_country_mapping.csv")
    tool = {row["fubc_country"]: row["country"] for row in tool_rows if row["fubc_country"]}
    alpha3 = {row["fubc_country"]: (row["ifastat_alpha3"], row["note"])
              for row in dataloader.rows("ifastat_fubc_country_mapping.csv")}
    tool_alpha3 = {row["country"]: row["ifastat_alpha3"] for row in dataloader.rows("ifastat_country_mapping.csv")}
    countries = []
    for fubc_country in sorted({row["fubc_country"] for row in rates}):
        if fubc_country not in alpha3:
            raise ValueError("ifastat_fubc_country_mapping.csv: no row for %r" % fubc_country)
        code, note = alpha3[fubc_country]
        country = tool.get(fubc_country, "")
        if country and code != tool_alpha3[country]:
            raise ValueError("%s: IFASTAT code %r, ifastat_country_mapping.csv says %r"
                             % (fubc_country, code, tool_alpha3[country]))
        years = reference.get(fubc_country, {fallback})
        if country and fubc_country not in reference:
            note = REGION_ONLY_NOTE
        countries.append((country, fubc_country, code, years, note))
    for country in sorted(row["country"] for row in tool_rows if not row["fubc_country"]):
        countries.append((country, "", tool_alpha3[country], {fallback}, ""))
    return countries


def build(ifastat_path):
    totals = read_ifastat(ifastat_path)
    rows = []
    for country, fubc_country, code, reference, note in _countries():
        base_years = sorted({year + d for year in reference for d in BASE_WINDOW})
        for nutrient, _ in NUTRIENTS.values():
            factor, notes = "", [note] if note else []
            missing = [str(year) for year in base_years + list(TARGET_YEARS) if (code, nutrient, year) not in totals]
            if code and missing:
                notes.append("no IFASTAT value for " + " ".join(missing))
            elif code:
                base = statistics.mean(totals[(code, nutrient, year)] for year in base_years)
                target = statistics.mean(totals[(code, nutrient, year)] for year in TARGET_YEARS)
                if base > 0:
                    factor = round(target / base, 4)
                else:
                    notes.append("no consumption in the base years")
            rows.append({"country": country, "fubc_country": fubc_country, "ifastat_alpha3": code,
                         "nutrient": nutrient, "base_years": " ".join(str(y) for y in base_years),
                         "target_years": "%d-%d" % (TARGET_YEARS[0], TARGET_YEARS[-1]), "factor": factor,
                         "note": "; ".join(notes)})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--ifastat", default=str(dataloader.EXTERNAL_DATA_DIR / IFASTAT_FILE))
    parser.add_argument("--out", default=str(ROOT / "data" / "ifastat_fertiliser_time_factor.csv"))
    args = parser.parse_args()
    rows = build(args.ifastat)
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print("%s: %d rows" % (args.out, len(rows)))


if __name__ == "__main__":
    main()

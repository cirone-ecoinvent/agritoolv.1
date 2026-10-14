"""Build the mineral fertiliser-use tables of decision L33 (WFLDB level 2 nutrient inputs).

Sources (zip files supplied by FC in data/external_data/, read without unpacking):
- IFA Fertilizer Use by Crop (FUBC): Ludemann C., Gruere A., Heffer P., Dobermann A. (2022) Global data on
  fertilizer use by crop and by country, Dryad, doi:10.5061/dryad.2rbnzs7qh, version of February 2025, CC0.
- FAOSTAT domain Fertilizers by Nutrient (RFN), element 5159 "Use per area of cropland" (kg/ha), bulk download.

Outputs:
- data/ifa_fubc_rates.csv: mean rate of mineral N, P2O5 and K2O over the total crop area (fertilised or not) per
  FUBC country and crop name as reported. All countries of the 9th survey (FUBC 9, 2017-18, also needed for the
  region and world fallbacks): IFA_<nutrient>_t / crop area, with the FAO or the IFA area as chosen by the authors
  (FAO_area_used_Yes_No). Countries of the tool that are not in FUBC 9: their latest earlier report,
  Aver_<nutrient>_rate_kg_ha, else <nutrient>_rate_kg_ha x <nutrient>_pc_fert / 100 (rate on the fertilised area
  times the fertilised share).
- data/faostat_fertiliser_use_country.csv: use per area of cropland per country of the tool and nutrient, mean
  over the reference year of the FUBC 9 data of the country (Year_for_FAO_area) with the year before and after
  (decision L35) and over the target years 2021-2023; the model brings the FUBC 9 rates to 2021-2023 with the
  ratio. Countries without FUBC data (rates of their IFA region) and countries with an earlier report only: the
  most frequent Year_for_FAO_area of FUBC 9; for the latter the ratio is used for the region rates of the crops
  missing in their report (decision L37), their own rates are used without time scaling (decision L33).

Usage (repository root):
    python scripts/build_ifa_fertiliser_use.py
    python scripts/build_ifa_fertiliser_use.py --fubc-zip <zip> --rfn-zip <zip> --out-dir <dir>
"""
import argparse
import csv
import io
import re
import statistics
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "legacy_model"))

import dataloader  # noqa: E402

FUBC_ZIP = "IFA Fertilizer Use by Crop.zip"
FUBC_ALL = "FUBC_1_to_9_data.csv"
FUBC_9_RAW = "FUBC_9_raw_data.csv"
LATEST_REPORT = 9
RFN_ZIP = "Inputs_FertilizersNutrient_E_All_Data_(Normalized).zip"
RFN_CSV = "Inputs_FertilizersNutrient_E_All_Data_(Normalized).csv"
RFN_ELEMENT = "5159"
RFN_UNIT = "kg/ha"
RFN_ITEMS = {"3102": "N", "3103": "P2O5", "3104": "K2O"}
TARGET_YEARS = (2021, 2022, 2023)
BASE_WINDOW = (-1, 0, 1)  # years around the reference year of the FUBC data (decision L35)
NUTRIENTS = ("N", "P2O5", "K2O")
RATES_COLUMNS = ["fubc_country", "region_ifa", "fubc_report", "year", "reference_years", "fubc_crop", "area_ha",
                 "n_kg_per_ha", "p2o5_kg_per_ha", "k2o_kg_per_ha", "rate_basis", "note"]
USE_COLUMNS = ["country", "nutrient", "base_years", "base_kg_per_ha_cropland", "target_years",
               "target_kg_per_ha_cropland", "flags", "note"]


def read_zip_csv(zip_path, member, encoding="utf-8-sig"):
    with zipfile.ZipFile(zip_path) as archive, archive.open(member) as raw:
        yield from csv.DictReader(io.TextIOWrapper(raw, encoding=encoding, newline=""))


def _number(value):
    value = (value or "").strip()
    return None if value in ("", "NA") else float(value)


def calendar_years(label):
    """'1997' -> [1997], '1999/2000' -> [1999, 2000], '2017/18' -> [2017, 2018]."""
    parts = re.split(r"[/-]", label.strip())
    years = [int(parts[0])]
    if len(parts) > 1:
        second = parts[1]
        years.append(int(second) if len(second) == 4 else years[0] // 100 * 100 + int(second))
    return years


def _round(value, digits=2):
    if value is None:
        return ""
    return int(round(value)) if digits == 0 else round(value, digits)


def fubc9_rows(fubc_zip, countries9):
    """Rows of the 9th survey: rate = tonnes of nutrient / crop area."""
    rows = []
    for r in read_zip_csv(fubc_zip, FUBC_9_RAW):
        country, region = countries9[r["Original_country_name_in_FUBC_report"]]
        fao_area = r["FAO_area_used_Yes_No"] == "Yes"
        area = _number(r["FAO_area_ha"] if fao_area else r["IFA_area_ha"])
        if not area or area <= 0:
            continue
        rates = {n: (None if _number(r["IFA_%s_t" % n]) is None else _number(r["IFA_%s_t" % n]) / area * 1000.0)
                 for n in NUTRIENTS}
        if all(v is None for v in rates.values()):
            continue
        rows.append({"fubc_country": country, "region_ifa": region, "fubc_report": LATEST_REPORT, "year": r["Year"],
                     "reference_years": r["Year_for_FAO_area"], "fubc_crop": r["Original_crop_name_in_FUBC_report"],
                     "area_ha": _round(area, 0), "n_kg_per_ha": _round(rates["N"]),
                     "p2o5_kg_per_ha": _round(rates["P2O5"]), "k2o_kg_per_ha": _round(rates["K2O"]),
                     "rate_basis": "IFA_<nutrient>_t / %s" % ("FAO_area_ha" if fao_area else "IFA_area_ha"),
                     "note": "" if r["Comment"] in ("", "NA") else r["Comment"]})
    return rows


def earlier_report_rows(all_rows, country):
    """Rows of the latest report before FUBC 9 of a country: mean rate over the total crop area."""
    report = max(int(r["FUBC_report_number"]) for r in all_rows if r["Country"] == country)
    rows = []
    for r in all_rows:
        if r["Country"] != country or int(r["FUBC_report_number"]) != report:
            continue
        rates, bases = {}, set()
        for n in NUTRIENTS:
            aver, rate, share = (_number(r["Aver_%s_rate_kg_ha" % n]), _number(r["%s_rate_kg_ha" % n]),
                                 _number(r["%s_pc_fert" % n]))
            if aver is not None:
                rates[n] = aver
                bases.add("Aver_<nutrient>_rate_kg_ha")
            elif rate is not None and share is not None:
                rates[n] = rate * share / 100.0
                bases.add("<nutrient>_rate_kg_ha x <nutrient>_pc_fert / 100")
            else:
                rates[n] = None
        if all(v is None for v in rates.values()):
            continue
        area = _number(r["Crop_area_k_ha"])
        rows.append({"fubc_country": country, "region_ifa": r["Region_IFA"], "fubc_report": report, "year": r["Year"],
                     "reference_years": " ".join(str(y) for y in calendar_years(r["Year"])), "fubc_crop": r["Crop"],
                     "area_ha": "" if area is None else _round(area * 1000.0, 0), "n_kg_per_ha": _round(rates["N"]),
                     "p2o5_kg_per_ha": _round(rates["P2O5"]), "k2o_kg_per_ha": _round(rates["K2O"]),
                     "rate_basis": "; ".join(sorted(bases)), "note": ""})
    return rows


def build_rates(fubc_zip, country_mapping):
    all_rows = list(read_zip_csv(fubc_zip, FUBC_ALL))
    countries9 = {r["Original_country_name_in_FUBC_report"]: (r["Country"], r["Region_IFA"])
                  for r in all_rows if int(r["FUBC_report_number"]) == LATEST_REPORT}
    rows = fubc9_rows(fubc_zip, countries9)
    in_fubc9 = {country for country, _ in countries9.values()}
    known = {r["Country"]: r["Region_IFA"] for r in all_rows}
    for m in country_mapping:
        name = m["fubc_country"]
        if not name:
            continue
        if name not in known:
            raise ValueError("%s: FUBC country %r not in %s" % (m["country"], name, FUBC_ALL))
        if known[name] != m["region_ifa"]:
            raise ValueError("%s: region %r, FUBC says %r" % (m["country"], m["region_ifa"], known[name]))
        if name not in in_fubc9:
            rows.extend(earlier_report_rows(all_rows, name))
    rows.sort(key=lambda r: (r["fubc_country"], r["fubc_crop"]))
    years = Counter(r["reference_years"] for r in rows if r["fubc_report"] == LATEST_REPORT)
    return rows, int(years.most_common(1)[0][0])


def build_use(rfn_zip, country_mapping, rate_rows, fallback_year):
    m49 = {r["country"]: int(r["m49_code"]) for r in dataloader.rows("faostat_country_mapping.csv")}
    base_years, region_only = {}, set()
    for m in country_mapping:
        own = [r for r in rate_rows if r["fubc_country"] == m["fubc_country"]]
        if own and all(r["fubc_report"] == LATEST_REPORT for r in own):
            reference = {int(r["reference_years"]) for r in own}
        else:
            reference = {fallback_year}
            if own:
                region_only.add(m["country"])
        base_years[m["country"]] = sorted({year + d for year in reference for d in BASE_WINDOW})
    wanted = {m49[c]: c for c in base_years}
    values = defaultdict(dict)
    for r in read_zip_csv(rfn_zip, RFN_CSV):
        if r["Element Code"] != RFN_ELEMENT or r["Item Code"] not in RFN_ITEMS or not r["Value"].strip():
            continue
        country = wanted.get(int(r["Area Code (M49)"].lstrip("'")))
        if country is None:
            continue
        if r["Unit"] != RFN_UNIT:
            raise ValueError("FAOSTAT RFN unit %r, expected %r" % (r["Unit"], RFN_UNIT))
        values[(country, RFN_ITEMS[r["Item Code"]])][int(r["Year"])] = (float(r["Value"]), r["Flag"])
    rows = []
    for country in sorted(base_years):
        for nutrient in NUTRIENTS:
            series = values[(country, nutrient)]
            means, missing, flags = {}, [], Counter()
            for label, years in (("base", base_years[country]), ("target", TARGET_YEARS)):
                found = [series[y] for y in years if y in series]
                missing += [str(y) for y in years if y not in series]
                if not found:
                    raise ValueError("No FAOSTAT RFN value for %s %s in %s" % (country, nutrient, years))
                means[label] = statistics.mean(v for v, _ in found)
                flags.update(f for _, f in found)
            rows.append({"country": country, "nutrient": nutrient,
                         "base_years": " ".join(str(y) for y in base_years[country]),
                         "base_kg_per_ha_cropland": round(means["base"], 3),
                         "target_years": "%d-%d" % (TARGET_YEARS[0], TARGET_YEARS[-1]),
                         "target_kg_per_ha_cropland": round(means["target"], 3),
                         "flags": " ".join("%s:%d" % kv for kv in sorted(flags.items()) if kv[0]),
                         "note": "; ".join(
                             (["for the region rates only (decision L37)"] if country in region_only else [])
                             + (["no value for " + ", ".join(missing)] if missing else []))})
    return rows


def _write(path, columns, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print("%d rows written to %s" % (len(rows), path))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fubc-zip", default=str(dataloader.EXTERNAL_DATA_DIR / FUBC_ZIP))
    parser.add_argument("--rfn-zip", default=str(dataloader.EXTERNAL_DATA_DIR / RFN_ZIP))
    parser.add_argument("--out-dir", default=str(dataloader.DATA_DIR))
    args = parser.parse_args()
    country_mapping = dataloader.rows("ifa_fubc_country_mapping.csv")
    rates, fallback_year = build_rates(args.fubc_zip, country_mapping)
    use = build_use(args.rfn_zip, country_mapping, rates, fallback_year)
    out = Path(args.out_dir)
    _write(out / "ifa_fubc_rates.csv", RATES_COLUMNS, rates)
    _write(out / "faostat_fertiliser_use_country.csv", USE_COLUMNS, use)
    mapped = {r["fubc_crop"] for r in dataloader.rows("ifa_fubc_crop_mapping.csv")}
    unknown = sorted(mapped - {r["fubc_crop"] for r in rates})
    if unknown:
        print("Crop names of ifa_fubc_crop_mapping.csv not in the rates: %s" % unknown)


if __name__ == "__main__":
    main()

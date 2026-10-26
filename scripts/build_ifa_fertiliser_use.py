"""Build the mineral fertiliser-use table of decision L33 (WFLDB level 2 nutrient inputs).

Sources (zip files supplied by FC in data/external_data/, read without unpacking):
- IFA Fertilizer Use by Crop (FUBC): Ludemann C., Gruere A., Heffer P., Dobermann A. (2022) Global data on
  fertilizer use by crop and by country, Dryad, doi:10.5061/dryad.2rbnzs7qh, version of February 2025, CC0.

Output:
- data/ifa_fubc_rates.csv: mean rate of mineral N, P2O5 and K2O over the total crop area (fertilised or not) per
  FUBC country and crop name as reported. All countries of the 9th survey (FUBC 9, 2017-18, also needed for the
  region and world fallbacks): IFA_<nutrient>_t / crop area, with the FAO or the IFA area as chosen by the authors
  (FAO_area_used_Yes_No). Countries of the tool that are not in FUBC 9: their latest earlier report,
  Aver_<nutrient>_rate_kg_ha, else <nutrient>_rate_kg_ha x <nutrient>_pc_fert / 100 (rate on the fertilised area
  times the fertilised share).

The factor that brings the rates to 2021-2023 is built by scripts/build_ifastat_time_factor.py (decision L53;
before: FAOSTAT Fertilizers by Nutrient, built here, decisions L33, L35).

Usage (repository root):
    python scripts/build_ifa_fertiliser_use.py
    python scripts/build_ifa_fertiliser_use.py --fubc-zip <zip> --out-dir <dir>
"""
import argparse
import csv
import io
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "legacy_model"))

import dataloader  # noqa: E402

FUBC_ZIP = "IFA Fertilizer Use by Crop.zip"
FUBC_ALL = "FUBC_1_to_9_data.csv"
FUBC_9_RAW = "FUBC_9_raw_data.csv"
LATEST_REPORT = 9
NUTRIENTS = ("N", "P2O5", "K2O")
RATES_COLUMNS = ["fubc_country", "region_ifa", "fubc_report", "year", "reference_years", "fubc_crop", "area_ha",
                 "n_kg_per_ha", "p2o5_kg_per_ha", "k2o_kg_per_ha", "rate_basis", "note"]


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
    parser.add_argument("--out-dir", default=str(dataloader.DATA_DIR))
    args = parser.parse_args()
    country_mapping = dataloader.rows("ifa_fubc_country_mapping.csv")
    rates = build_rates(args.fubc_zip, country_mapping)
    out = Path(args.out_dir)
    _write(out / "ifa_fubc_rates.csv", RATES_COLUMNS, rates)
    mapped = {r["fubc_crop"] for r in dataloader.rows("ifa_fubc_crop_mapping.csv")}
    unknown = sorted(mapped - {r["fubc_crop"] for r in rates})
    if unknown:
        print("Crop names of ifa_fubc_crop_mapping.csv not in the rates: %s" % unknown)


if __name__ == "__main__":
    main()

"""Cross-check of the default irrigation water consumption (decision L44): is the national blue water footprint from
irrigation of Mialyk et al. (2024, 2010-2019) inside the range of Pfister & Bayer (2014, year 2000), minimum =
deficit irrigation, maximum = full irrigation?

Reads data/mialyk2024_*.csv and data/pfister2014_*.csv; both in m3 per t of the tool product (Mialyk x the kg of
FAOSTAT item per kg of product of its mapping, e.g. tea 4.5; Pfister tea is made tea). Writes one row per tool crop
and country with both values and prints the counts and the production-weighted shares.

Usage (repository root):
    python scripts/compare_mialyk_pfister.py [--out Literature/review_mialyk_vs_pfister2014.csv]
"""
import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "legacy_model"))

import dataloader  # noqa: E402

VERDICTS = ("inside", "below min", "above max")


def compare():
    mialyk_map = {r["crop"]: r for r in dataloader.rows("mialyk2024_crop_mapping.csv")}
    mialyk = {(r["mialyk_crop_code"], r["country"]): r for r in dataloader.rows("mialyk2024_national_blue_wf.csv")}
    pfister = {(r["pfister_crop"], r["country"]): r for r in dataloader.rows("pfister2014_blue_water_country.csv")}
    rows = []
    for p in dataloader.rows("pfister2014_crop_mapping.csv"):
        m = mialyk_map[p["crop"]]
        if p["use"] == "legacy" or m["use"] == "legacy":
            continue
        factor = float(m["kg_item_per_kg_product"] or 1.0)
        for country in sorted({c for (crop, c) in pfister if crop == p["pfister_crop"]}):
            pf = pfister[(p["pfister_crop"], country)]
            mi = mialyk.get((m["mialyk_crop_code"], country))
            if mi is None or pf["bw_min_m3_t"] == "":
                continue
            value = float(mi["wfb_i_m3_t"]) * factor
            low, high = float(pf["bw_min_m3_t"]), float(pf["bw_max_m3_t"])
            verdict = "below min" if value < low else "above max" if value > high else "inside"
            rows.append({"crop": p["crop"], "country": country, "mialyk_m3_t": round(value, 3),
                         "pfister_min_m3_t": low, "pfister_expected_m3_t": pf["bw_expected_m3_t"],
                         "pfister_max_m3_t": high, "verdict": verdict, "mialyk_production_t": mi["production_t"]})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=str(ROOT / "Literature" / "review_mialyk_vs_pfister2014.csv"))
    args = parser.parse_args()
    rows = compare()
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    countries = [r for r in rows if r["country"] != "GLO"]
    total = sum(float(r["mialyk_production_t"]) for r in countries)
    print("%d crop-country pairs (GLO excluded), written to %s" % (len(countries), args.out))
    for verdict in VERDICTS:
        chosen = [r for r in countries if r["verdict"] == verdict]
        print("  %-10s %4d pairs, %5.1f %% of the Mialyk production" % (
            verdict, len(chosen), 100.0 * sum(float(r["mialyk_production_t"]) for r in chosen) / total))


if __name__ == "__main__":
    main()

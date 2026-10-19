"""Build data/mialyk2024_national_blue_wf.csv, the national blue water footprint from irrigation per crop.

Source (decision L44): Mialyk O., Schyns J. F., Booij M. J., Su H., Hogeboom R. J., Berger M. (2024) Water
footprints and crop water use of 175 individual crops for 1990-2019 simulated with a global crop model.
Scientific Data 11, 206 (doi:10.1038/s41597-024-03051-3); dataset doi:10.4121/7b45bcc6-686b-404d-a910-13c87156716a,
version 3 of 2025-05-16, CC BY 4.0, file 'national_wf_175_crops_average_2010_2019.csv' (national averages
2010-2019; the header is the 4th line of the file). Unit water footprints in m3 per t of total national
production (irrigated and rainfed).

Kept: the items of data/mialyk2024_crop_mapping.csv (use direct or proxy), for the tool countries
matched by FAOSTAT area code (data/faostat_country_mapping.csv), plus one GLO row per item:
production-weighted mean of wfb_i and wfb_cr over all countries of the file (production = sum).
Columns of the file kept as they are: production_t, wfb_i_m3_t (blue from irrigation), wfb_cr_m3_t
(blue from capillary rise, not used by the model).

Usage (repository root):
    python scripts/build_mialyk_blue_water.py                              # file in data/external_data/
    python scripts/build_mialyk_blue_water.py --mialyk <csv> --out <path>  # other copy, write elsewhere
"""
import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "legacy_model"))

import dataloader  # noqa: E402

MIALYK_FILE = "national_wf_175_crops_average_2010_2019.csv"
COLUMNS = ["mialyk_crop_code", "mialyk_crop_name", "country", "faostat_area_code", "production_t", "wfb_i_m3_t",
           "wfb_cr_m3_t", "note"]


def read_mialyk(path):
    lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
    header = next((i for i, line in enumerate(lines) if line.startswith("crop_code,")), None)
    if header is None:
        raise ValueError("no header line starting with 'crop_code,' in %s" % path)
    return list(csv.DictReader(lines[header:]))


def build(mialyk_csv):
    area_to_country = {int(r["faostat_area_code"]): r["country"] for r in dataloader.rows("faostat_country_mapping.csv")
                       if r["country"] != "GLO"}
    codes = {r["mialyk_crop_code"] for r in dataloader.rows("mialyk2024_crop_mapping.csv")
             if r["use"] in ("direct", "proxy")}
    by_item = {}
    for row in read_mialyk(mialyk_csv):
        if row["crop_code"] in codes:
            by_item.setdefault(row["crop_code"], []).append(row)
    missing = sorted(codes - set(by_item), key=int)
    if missing:
        raise ValueError("items %s of mialyk2024_crop_mapping.csv not in %s" % (", ".join(missing), mialyk_csv))
    rows = []
    for code in sorted(by_item, key=int):
        items = by_item[code]
        name = items[0]["crop_name"]
        for row in items:
            country = area_to_country.get(int(row["country_code"]))
            if country is not None:
                rows.append({"mialyk_crop_code": code, "mialyk_crop_name": name, "country": country,
                             "faostat_area_code": row["country_code"], "production_t": row["production_t"],
                             "wfb_i_m3_t": row["wfb_i_m3_t"], "wfb_cr_m3_t": row["wfb_cr_m3_t"], "note": ""})
        production = sum(float(r["production_t"]) for r in items)
        if production <= 0:
            raise ValueError("no production for item %s" % code)
        blue_i = sum(float(r["wfb_i_m3_t"]) * float(r["production_t"]) for r in items) / production
        blue_cr = sum(float(r["wfb_cr_m3_t"]) * float(r["production_t"]) for r in items) / production
        rows.append({"mialyk_crop_code": code, "mialyk_crop_name": name, "country": "GLO", "faostat_area_code": "",
                     "production_t": round(production, 1), "wfb_i_m3_t": round(blue_i, 3),
                     "wfb_cr_m3_t": round(blue_cr, 3),
                     "note": "production-weighted mean over the %d countries of the file" % len(items)})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mialyk", default=str(dataloader.EXTERNAL_DATA_DIR / MIALYK_FILE),
                        help="Mialyk et al. national averages (default: data/external_data/%s)" % MIALYK_FILE)
    parser.add_argument("--out", default=str(dataloader.DATA_DIR / "mialyk2024_national_blue_wf.csv"))
    args = parser.parse_args()
    rows = build(args.mialyk)
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print("%d rows written to %s" % (len(rows), args.out))


if __name__ == "__main__":
    main()

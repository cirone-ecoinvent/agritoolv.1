"""Build data/ludemann2023_world_crop_coefficients.csv (decision L41: N uptake of the crops without WFLDB level 1
coefficients).

Source (zip file supplied by FC in data/external_data/, read without unpacking): Ludemann C., Hijbeek R., van Loon M.,
Murrell S., van Ittersum M., Dobermann A. (2023) Global data on crop nutrient concentration and harvest indices,
Dryad, doi:10.5061/dryad.n2z34tn0x, CC0 (README of 2024-09-30). Member World_crop_coefficients_for_UN_FAO.csv: the
Tier 1 (world) concentrations of the crop products used in the 2023 update of the UN FAO Cropland Nutrient Budget.

Output: one row per FAO item, values as published; "NA" becomes an empty cell. Units: kg of elemental N, P or K per
t fresh weight of crop product; dry matter and concentrations on a dry matter basis in %.

Usage (repository root):
    python scripts/build_ludemann_crop_coefficients.py
    python scripts/build_ludemann_crop_coefficients.py --zip <zip> --out <csv>
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

ZIP_NAME = "Global data on crop nutrient concentration and harvest indices.zip"
MEMBER = "World_crop_coefficients_for_UN_FAO.csv"
OUTPUT = "ludemann2023_world_crop_coefficients.csv"
# output column <- source column
COLUMNS = {
    "item_code": "item_code",
    "item": "item",
    "item_group_code": "item_group_code",
    "n_kg_per_t_fm": "N_kg_per_t_fresh_wt",
    "p_kg_per_t_fm": "P_kg_per_t_fresh_wt",
    "k_kg_per_t_fm": "K_kg_per_t_fresh_wt",
    "dm_pc": "DM_pc",
    "n_pc_dm": "N_pc",
    "p_pc_dm": "P_pc",
    "k_pc_dm": "K_pc",
}


def read_rows(zip_path):
    with zipfile.ZipFile(zip_path) as archive, archive.open(MEMBER) as raw:
        reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))
        return [{out: ("" if row[src] == "NA" else row[src]) for out, src in COLUMNS.items()} for row in reader]


def build(zip_path):
    rows = read_rows(zip_path)
    codes = [row["item_code"] for row in rows]
    if len(codes) != len(set(codes)):
        raise ValueError("duplicate item codes in %s" % MEMBER)
    return sorted(rows, key=lambda row: int(row["item_code"]))


def write(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(COLUMNS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--zip", type=Path, default=dataloader.EXTERNAL_DATA_DIR / ZIP_NAME)
    parser.add_argument("--out", type=Path, default=dataloader.DATA_DIR / OUTPUT)
    args = parser.parse_args()
    rows = build(args.zip)
    write(rows, args.out)
    print("%d items written to %s" % (len(rows), args.out))


if __name__ == "__main__":
    main()

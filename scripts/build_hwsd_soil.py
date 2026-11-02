"""Build data/hwsd2_soil.csv: soil properties and erodibility K per crop and country from the Harmonized World Soil
Database v2.0 (template v3 specification section 5.13).

Source: FAO & IIASA (2023) Harmonized World Soil Database version 2.0. data/external_data/HWSD2_RASTER.zip (HWSD2.bil,
30 arc-seconds, soil mapping unit per cell) and HWSD2_DB.zip (HWSD2.mdb, table HWSD2_LAYERS: soil units of each
mapping unit with their SHARE, layers D1-D7). Licence CC BY-NC-SA 3.0 IGO (see data/sources.csv).

Method:
1. Each soil unit with data in the topsoil layer D1 (0-20 cm; rock outcrops, water bodies and other units without
   values are left out):
   - clay, silt, sand, coarse fragments, pH in water of D1; ph_le7 = 1 when pH <= 7;
   - organic carbon 0-50 cm: mean of D1 (0-20 cm), D2 (20-40 cm) and D3 (40-60 cm) weighted by 20, 20 and 10 cm,
     over the layers with data (shallow soils: D1 only), as the soil volume of the nitrate model (0-50 cm);
   - k_renard: Renard et al. (1997) AH 703 Eq. 3-5 in SI units, K = 0.0034 + 0.0405 exp(-0.5 ((log10 Dg + 1.659) /
     0.7101) ** 2), Dg = exp(0.01 sum f_i ln m_i) (Eq. 3-6), times the stoniness factor St;
   - k_lanca: Bos et al. (2016) LANCA Eq. 7-8 (Wischmeier nomograph), K = (2.1e-4 M ** 1.14 (12 - OM) + 3.25 (s - 2)
     + 2.5 (p - 3)) / 100 x 0.1317 x St, M = (silt + very fine sand) (100 - clay), negative K set to 0; the printed
     Eq. 7 divides 0.1317 St by 100 again, read here as a misprint (K would be about 100 times below the K factors
     of the WFLDB Documentation 2017 Tab. 6, recalculated from Panagos et al. 2014);
   with St from the coarse fragments (lanca2016_stoniness_factors.csv), the permeability class p from the USDA
   texture class (lanca2016_permeability_classes.csv) and the parameters of hwsd_k_factor_parameters.csv.
2. Mapping unit = mean of its soil units weighted by SHARE (renormalised over the units with data).
3. SPAM cell (1/12 degree = 10 x 10 HWSD cells) = mean of the HWSD cells with data; then the weighted mean over the
   SPAM physical area of the crop in the country (spam_grid.py).
HWSD2.mdb is extracted to --workdir (about 90 MB) and deleted after use; it is read with the Microsoft Access ODBC
driver (pyodbc).

Usage (repository root, build environment):
    .venv-gis\\Scripts\\python scripts\\build_hwsd_soil.py --workdir DIR [--grid-cache FILE] [--soil-cache FILE]
"""
import argparse
import math
import zipfile
from pathlib import Path

import numpy as np
import pyodbc

import spam_grid

DB_ZIP = spam_grid.EXTERNAL_DATA_DIR / "HWSD2_DB.zip"
RASTER_ZIP = spam_grid.EXTERNAL_DATA_DIR / "HWSD2_RASTER.zip"
OUTPUT = spam_grid.DATA_DIR / "hwsd2_soil.csv"

HWSD_COLS, HWSD_ROWS, NODATA = 43200, 21600, 65535
BLOCK = HWSD_COLS // spam_grid.COLS  # HWSD cells per SPAM cell side
OC_LAYER_WEIGHTS = {"D1": 20.0, "D2": 20.0, "D3": 10.0}  # cm of each layer within 0-50 cm
VARIABLES = ["clay_pct", "silt_pct", "sand_pct", "coarse_pct", "ph_water", "ph_le7_share", "org_carbon_0_50_pct",
             "k_renard", "k_lanca"]


def _parameters():
    return {row["parameter"]: float(row["value"]) for row in spam_grid.read_csv("hwsd_k_factor_parameters.csv")}


def stoniness_factor(coarse_pct, classes):
    for row in classes:
        if coarse_pct <= float(row["coarse_max_pct"]):
            return float(row["stoniness_factor"])
    return float(classes[-1]["stoniness_factor"])


def k_renard(clay, silt, sand, st, par):
    log_dg = 0.01 * (clay * math.log(par["clay_mean_diameter_mm"]) + silt * math.log(par["silt_mean_diameter_mm"])
                     + sand * math.log(par["sand_mean_diameter_mm"])) / math.log(10.0)
    return (0.0034 + 0.0405 * math.exp(-0.5 * ((log_dg + 1.659) / 0.7101) ** 2)) * st


def k_lanca(clay, silt, sand, org_carbon, permeability, st, par):
    m = (silt + par["very_fine_sand_share_of_sand"] * sand) * (100.0 - clay)
    om = min(org_carbon * par["organic_matter_per_organic_carbon"], par["organic_matter_max_pct"])
    k = (2.1e-4 * m ** 1.14 * (12.0 - om) + 3.25 * (par["structure_class"] - 2.0)
         + 2.5 * (permeability - 3.0)) / 100.0 * 0.1317 * st
    return max(k, 0.0)


def mapping_unit_table(mdb_path):
    """Array [mapping unit id, variable] of the SHARE-weighted means, NaN for units without data."""
    par = _parameters()
    classes = spam_grid.read_csv("lanca2016_stoniness_factors.csv")
    permeability = {int(r["texture_usda_code"]): float(r["permeability_class"])
                    for r in spam_grid.read_csv("lanca2016_permeability_classes.csv")}
    connection = pyodbc.connect(r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + str(mdb_path))
    units = {}
    for smu, seq, share, layer, clay, silt, sand, coarse, texture, oc, ph in connection.cursor().execute(
            "SELECT HWSD2_SMU_ID, SEQUENCE, SHARE, LAYER, CLAY, SILT, SAND, COARSE, TEXTURE_USDA, ORG_CARBON, "
            "PH_WATER FROM HWSD2_LAYERS WHERE LAYER IN ('D1', 'D2', 'D3')"):
            unit = units.setdefault((smu, seq), {"share": share})
            unit[layer] = (clay, silt, sand, coarse, texture, oc, ph)
    connection.close()
    table = np.full((NODATA + 1, len(VARIABLES)), np.nan)
    sums, weights = {}, {}
    for (smu, _), unit in units.items():
        top = unit.get("D1")
        if top is None or any(v is None or v < 0 for v in top) or not unit["share"]:
            continue
        clay, silt, sand, coarse, texture, oc, ph = top
        oc_layers = [(OC_LAYER_WEIGHTS[layer], unit[layer][5]) for layer in OC_LAYER_WEIGHTS
                     if layer in unit and unit[layer][5] is not None and unit[layer][5] >= 0]
        st = stoniness_factor(coarse, classes)
        values = [clay, silt, sand, coarse, ph, 1.0 if ph <= 7.0 else 0.0,
                  sum(w * v for w, v in oc_layers) / sum(w for w, _ in oc_layers),
                  k_renard(clay, silt, sand, st, par),
                  k_lanca(clay, silt, sand, oc, permeability[int(texture)], st, par)]
        sums[smu] = sums.get(smu, 0.0) + unit["share"] * np.array(values)
        weights[smu] = weights.get(smu, 0.0) + unit["share"]
    for smu in sums:
        table[smu] = sums[smu] / weights[smu]
    return table


def spam_cell_means(table):
    """[variable] arrays on the SPAM grid: mean of the HWSD cells with data in each SPAM cell."""
    out = np.full((len(VARIABLES), spam_grid.ROWS, spam_grid.COLS), np.nan)
    row_bytes = HWSD_COLS * 2
    with zipfile.ZipFile(RASTER_ZIP) as zf, zf.open("HWSD2.bil") as raster:
        for r in range(spam_grid.ROWS):
            ids = np.frombuffer(raster.read(BLOCK * row_bytes), dtype="<u2").reshape(BLOCK, HWSD_COLS)
            values = table[ids]  # BLOCK x HWSD_COLS x variables
            valid = np.isfinite(values[..., 0])
            blocks = np.where(valid[..., None], values, 0.0).reshape(BLOCK, spam_grid.COLS, BLOCK, len(VARIABLES))
            total = blocks.sum(axis=(0, 2))
            count = valid.reshape(BLOCK, spam_grid.COLS, BLOCK).sum(axis=(0, 2))
            with np.errstate(invalid="ignore", divide="ignore"):
                out[:, r, :] = np.where(count[:, None] > 0, total / count[:, None], np.nan).T
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", required=True, help="folder for the extracted HWSD2.mdb")
    parser.add_argument("--grid-cache", help="npy file to store or reuse the country grid")
    parser.add_argument("--soil-cache", help="npy file to store or reuse the soil maps on the SPAM grid")
    args = parser.parse_args()
    grid, countries = spam_grid.country_grid(args.grid_cache)
    if args.soil_cache and Path(args.soil_cache).is_file():
        maps = np.load(args.soil_cache)
    else:
        with zipfile.ZipFile(DB_ZIP) as zf:
            path = Path(zf.extract("HWSD2.mdb", args.workdir)).resolve()
        try:
            table = mapping_unit_table(path)
        finally:
            path.unlink()
        maps = spam_cell_means(table)
        if args.soil_cache:
            np.save(args.soil_cache, maps)
    rows = spam_grid.weighted_country_means(dict(zip(VARIABLES, maps)), grid, countries,
                                            spam_grid.read_csv("spam2020_crop_mapping.csv"))
    columns = ["crop", "country", "weights", "area_ha", "coverage"] + VARIABLES
    digits = {"area_ha": 0, "coverage": 4, "clay_pct": 1, "silt_pct": 1, "sand_pct": 1, "coarse_pct": 1,
              "ph_water": 2, "ph_le7_share": 4, "org_carbon_0_50_pct": 3, "k_renard": 4, "k_lanca": 4}
    spam_grid.write_rows(OUTPUT, rows, columns, digits)
    print("written %s (%d rows)" % (OUTPUT.relative_to(spam_grid.ROOT), len(rows)))


if __name__ == "__main__":
    main()

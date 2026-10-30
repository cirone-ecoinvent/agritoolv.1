"""Build data/gloreda2023_rainfall_erosivity.csv: rainfall erosivity R per crop and country (template v3
specification section 5.13, decision L59).

Source: Global Rainfall Erosivity Database GloREDa (ESDAC, Panagos et al.), public release of 2023-08-07,
data/external_data/Public_GLOREDA_07082023.zip: 12 monthly GeoTIFFs Rfactor_<Month>.tif (WGS 84, 1/120 degree,
87.37 N to about 62 S, int16, nodata -32768, MJ mm/(ha h month)).

Method: mean of each month over the 1/120 degree cells whose centre lies in a 1/12 degree cell of the SPAM 2020 grid
(10 columns, 10 rows; the GloREDa rows start at 87.37 N and are assigned by their centre); annual R of a SPAM cell =
sum of the 12 monthly means (cells with a month without data are left out); weighted mean over the SPAM physical area
of the crop in the country (spam_grid.py). Each month is extracted to --workdir (about 250 MB) and deleted after use.

Cross-check printed per country: median of R_FINAL of the GloREDa stations (GloREDa.xlsx, sheet Annual).

Usage (repository root, build environment):
    .venv-gis\\Scripts\\python scripts\\build_gloreda_erosivity.py --workdir DIR [--grid-cache FILE] [--r-cache FILE]
"""
import argparse
import io
import statistics
import zipfile
from pathlib import Path

import numpy as np
import openpyxl
import tifffile

import spam_grid

GLOREDA_ZIP = spam_grid.EXTERNAL_DATA_DIR / "Public_GLOREDA_07082023.zip"
OUTPUT = spam_grid.DATA_DIR / "gloreda2023_rainfall_erosivity.csv"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
FINE = 120  # cells per degree
NODATA = -32768


def monthly_mean(zf, month, workdir):
    name = "Rfactor_%s.tif" % month
    path = Path(zf.extract(name, workdir))
    try:
        with tifffile.TiffFile(path) as tif:
            page = tif.pages[0]
            top = page.tags["ModelTiepointTag"].value[4]
            scale = page.tags["ModelPixelScaleTag"].value[0]
            assert abs(scale - 1.0 / FINE) < 1e-9 and page.tags["ModelTiepointTag"].value[3] == -180.0
            data = page.asarray()
    finally:
        path.unlink()
    rows, cols = data.shape
    assert cols == 360 * FINE
    centre_lat = top - (np.arange(rows) + 0.5) / FINE
    spam_row = np.floor((90.0 - centre_lat) * spam_grid.CELLS_PER_DEGREE).astype(np.int64)
    total = np.zeros((spam_grid.ROWS, spam_grid.COLS))
    count = np.zeros((spam_grid.ROWS, spam_grid.COLS))
    step = 1000
    for start in range(0, rows, step):
        chunk = data[start:start + step]
        valid = chunk != NODATA
        values = np.where(valid, chunk, 0).astype(np.float64)
        s = values.reshape(len(chunk), spam_grid.COLS, -1).sum(axis=2)
        c = valid.reshape(len(chunk), spam_grid.COLS, -1).sum(axis=2)
        target = spam_row[start:start + step]
        np.add.at(total, target, s)
        np.add.at(count, target, c)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(count > 0, total / count, np.nan), int((data != NODATA).sum()), int(data.max())


def station_medians():
    with zipfile.ZipFile(GLOREDA_ZIP) as zf:
        wb = openpyxl.load_workbook(io.BytesIO(zf.read("GloREDa.xlsx")), read_only=True)
    rows = wb["Annual"].iter_rows(values_only=True)
    header = next(rows)
    country, r = header.index("CNTR_ID"), header.index("R_FINAL")
    values = {}
    for row in rows:
        if row[r] is not None:
            values.setdefault(row[country], []).append(float(row[r]))
    return {c: (statistics.median(v), len(v)) for c, v in values.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", required=True, help="folder for the extracted monthly GeoTIFF")
    parser.add_argument("--grid-cache", help="npy file to store or reuse the country grid")
    parser.add_argument("--r-cache", help="npy file to store or reuse the annual R on the SPAM grid")
    args = parser.parse_args()
    grid, countries = spam_grid.country_grid(args.grid_cache)
    if args.r_cache and Path(args.r_cache).is_file():
        annual = np.load(args.r_cache)
    else:
        annual = np.zeros((spam_grid.ROWS, spam_grid.COLS))
        with zipfile.ZipFile(GLOREDA_ZIP) as zf:
            for month in MONTHS:
                mean, cells, maximum = monthly_mean(zf, month, args.workdir)
                annual += mean
                print("%-9s cells with data %d, max %d" % (month, cells, maximum))
        if args.r_cache:
            np.save(args.r_cache, annual)
    rows = spam_grid.weighted_country_means({"r_factor_mj_mm_per_ha_h_yr": annual}, grid, countries,
                                            spam_grid.read_csv("spam2020_crop_mapping.csv"))
    columns = ["crop", "country", "weights", "area_ha", "coverage", "r_factor_mj_mm_per_ha_h_yr"]
    spam_grid.write_rows(OUTPUT, rows, columns, {"area_ha": 0, "coverage": 4, "r_factor_mj_mm_per_ha_h_yr": 0})
    print("written %s (%d rows)" % (OUTPUT.relative_to(spam_grid.ROOT), len(rows)))
    stations = station_medians()
    print("\ncountry  R all crops  station median (n)")
    for row in rows:
        if row["crop"] == "all_crops":
            code = "RS" if row["country"] == "CS" else row["country"]
            median, n = stations.get(code, (None, 0))
            print("%-7s %12s  %s" % (row["country"], "%.0f" % row["r_factor_mj_mm_per_ha_h_yr"]
                                      if row["r_factor_mj_mm_per_ha_h_yr"] is not None else "-",
                                      "%.0f (%d)" % (median, n) if median is not None else "-"))


if __name__ == "__main__":
    main()

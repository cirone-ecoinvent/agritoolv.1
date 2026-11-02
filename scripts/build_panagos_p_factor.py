"""Build data/panagos2015b_p_factor.csv: support-practice factor P of the EU per crop and country (template v3
specification section 5.13).

Source: Panagos P., Borrelli P., Meusburger K., van der Zanden E.H., Poesen J., Alewell C. (2015) Modelling the effect
of support practices (P-factor) on the reduction of soil erosion by water at European scale. Environmental Science &
Policy 51: 23-34. ESDAC map data/external_data/P.zip, P.tif (ETRS89 LAEA, EPSG:3035, 100 m, float32, nodata
-3.4028e+38).

Method: the centre of each 100 m cell is converted to latitude and longitude (inverse Lambert azimuthal equal-area on
the GRS 80 ellipsoid, IOGP Guidance Note 7-2, method 9820) and assigned to the 1/12 degree cell of the SPAM 2020 grid
that contains it; P of a SPAM cell = mean of its 100 m cells with data; weighted mean over the SPAM physical area of
the crop in the country (spam_grid.py). coverage = share of the weighting area with a P value. The map covers the EU
only: a country whose coverage of all crops is below MIN_COUNTRY_COVERAGE gets no value (decision L62; CH, CS, RU, TR
and UA reach only the SPAM cells across the EU border), and the model uses P = 1 there. P.tif is extracted to --workdir (about 100 MB) and
deleted after use.

Usage (repository root, build environment):
    .venv-gis\\Scripts\\python scripts\\build_panagos_p_factor.py --workdir DIR [--grid-cache FILE] [--p-cache FILE]
"""
import argparse
import math
import zipfile
from pathlib import Path

import numpy as np
import tifffile

import spam_grid

P_ZIP = spam_grid.EXTERNAL_DATA_DIR / "P.zip"
OUTPUT = spam_grid.DATA_DIR / "panagos2015b_p_factor.csv"
MIN_COUNTRY_COVERAGE = 0.5

# EPSG:3035 ETRS89-extended / LAEA Europe, GRS 80
A, INVERSE_F = 6378137.0, 298.257222101
LAT0, LON0 = math.radians(52.0), math.radians(10.0)
FALSE_EASTING, FALSE_NORTHING = 4321000.0, 3210000.0
E2 = 2.0 / INVERSE_F - 1.0 / INVERSE_F ** 2
E = math.sqrt(E2)


def _q(sin_lat):
    return (1.0 - E2) * (sin_lat / (1.0 - E2 * sin_lat ** 2)
                         - 1.0 / (2.0 * E) * np.log((1.0 - E * sin_lat) / (1.0 + E * sin_lat)))


QP = _q(1.0)
BETA0 = math.asin(_q(math.sin(LAT0)) / QP)
RQ = A * math.sqrt(QP / 2.0)
D = A * (math.cos(LAT0) / math.sqrt(1.0 - E2 * math.sin(LAT0) ** 2)) / (RQ * math.cos(BETA0))


def laea_forward(lat_deg, lon_deg):
    """Easting, northing of latitude and longitude in degrees (check of the inverse)."""
    lat, lon = np.radians(lat_deg), np.radians(lon_deg)
    beta = np.arcsin(_q(np.sin(lat)) / QP)
    b = RQ * np.sqrt(2.0 / (1.0 + math.sin(BETA0) * np.sin(beta)
                            + math.cos(BETA0) * np.cos(beta) * np.cos(lon - LON0)))
    east = FALSE_EASTING + b * D * np.cos(beta) * np.sin(lon - LON0)
    north = FALSE_NORTHING + b / D * (math.cos(BETA0) * np.sin(beta)
                                      - math.sin(BETA0) * np.cos(beta) * np.cos(lon - LON0))
    return east, north


def laea_inverse(east, north):
    """Latitude and longitude in degrees of easting and northing in metres."""
    x, y = east - FALSE_EASTING, north - FALSE_NORTHING
    rho = np.sqrt((x / D) ** 2 + (D * y) ** 2)
    c = 2.0 * np.arcsin(np.minimum(rho / (2.0 * RQ), 1.0))
    with np.errstate(invalid="ignore", divide="ignore"):
        beta = np.where(rho > 0, np.arcsin(np.cos(c) * math.sin(BETA0)
                                           + D * y * np.sin(c) * math.cos(BETA0) / np.where(rho > 0, rho, 1.0)),
                        BETA0)
    lon = LON0 + np.arctan2(x * np.sin(c), D * rho * math.cos(BETA0) * np.cos(c)
                            - D ** 2 * y * math.sin(BETA0) * np.sin(c))
    lat = (beta + (E2 / 3.0 + 31.0 * E2 ** 2 / 180.0 + 517.0 * E2 ** 3 / 5040.0) * np.sin(2.0 * beta)
           + (23.0 * E2 ** 2 / 360.0 + 251.0 * E2 ** 3 / 3780.0) * np.sin(4.0 * beta)
           + (761.0 * E2 ** 3 / 45360.0) * np.sin(6.0 * beta))
    return np.degrees(lat), np.degrees(lon)


def check_projection():
    # IOGP Guidance Note 7-2, example of method 9820: 50 N, 5 E -> E 3962799.45, N 2999718.85
    east, north = laea_forward(50.0, 5.0)
    assert abs(east - 3962799.45) < 0.01 and abs(north - 2999718.85) < 0.01, (east, north)
    lat, lon = laea_inverse(np.array([3962799.45]), np.array([2999718.85]))
    assert abs(lat[0] - 50.0) < 1e-6 and abs(lon[0] - 5.0) < 1e-6, (lat, lon)


def spam_cell_means(path, block_rows=256):
    """Mean P of the 100 m cells in each SPAM cell, NaN where no cell has data. The 100 m rows are read in blocks
    and summed only over the range of SPAM indices that the block touches."""
    total = np.zeros(spam_grid.ROWS * spam_grid.COLS)
    count = np.zeros(spam_grid.ROWS * spam_grid.COLS)

    def add(index, values):
        if index:
            index, values = np.concatenate(index), np.concatenate(values)
            low = index.min()
            sums = np.bincount(index - low, weights=values)
            total[low:low + sums.size] += sums
            count[low:low + sums.size] += np.bincount(index - low, minlength=sums.size)

    with tifffile.TiffFile(path) as tif:
        page = tif.pages[0]
        scale = page.tags["ModelPixelScaleTag"].value
        tie = page.tags["ModelTiepointTag"].value
        assert scale[0] == scale[1] == 100.0 and page.tags["RowsPerStrip"].value == 1
        rows, cols = page.shape
        east = tie[3] + (np.arange(cols) + 0.5) * scale[0]
        fh = tif.filehandle
        block_index, block_values = [], []
        for r, (offset, size) in enumerate(zip(page.dataoffsets, page.databytecounts)):
            fh.seek(offset)
            values = page.decode(fh.read(size), r)[0].reshape(-1)[:cols]
            valid = (values >= 0.0) & (values <= 1.0)
            if valid.any():
                north = tie[4] - (r + 0.5) * scale[1]
                lat, lon = laea_inverse(east[valid], np.full(valid.sum(), north))
                spam_row = np.floor((90.0 - lat) * spam_grid.CELLS_PER_DEGREE).astype(np.int64)
                spam_col = np.floor((lon + 180.0) * spam_grid.CELLS_PER_DEGREE).astype(np.int64)
                block_index.append(spam_row * spam_grid.COLS + spam_col)
                block_values.append(values[valid].astype(np.float64))
            if (r + 1) % block_rows == 0:
                add(block_index, block_values)
                block_index, block_values = [], []
        add(block_index, block_values)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(count > 0, total / count, np.nan).reshape(spam_grid.ROWS, spam_grid.COLS)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", required=True, help="folder for the extracted P.tif")
    parser.add_argument("--grid-cache", help="npy file to store or reuse the country grid")
    parser.add_argument("--p-cache", help="npy file to store or reuse P on the SPAM grid")
    args = parser.parse_args()
    check_projection()
    grid, countries = spam_grid.country_grid(args.grid_cache)
    if args.p_cache and Path(args.p_cache).is_file():
        p_factor = np.load(args.p_cache)
    else:
        with zipfile.ZipFile(P_ZIP) as zf:
            path = Path(zf.extract("P.tif", args.workdir))
        try:
            p_factor = spam_cell_means(path)
        finally:
            path.unlink()
        if args.p_cache:
            np.save(args.p_cache, p_factor)
    rows = spam_grid.weighted_country_means({"p_factor": p_factor}, grid, countries,
                                            spam_grid.read_csv("spam2020_crop_mapping.csv"))
    outside = {row["country"] for row in rows if row["crop"] == "all_crops" and row["coverage"] < MIN_COUNTRY_COVERAGE}
    for row in rows:
        if row["country"] in outside:
            row["p_factor"] = None
    columns = ["crop", "country", "weights", "area_ha", "coverage", "p_factor"]
    spam_grid.write_rows(OUTPUT, rows, columns, {"area_ha": 0, "coverage": 4, "p_factor": 4})
    print("written %s (%d rows)" % (OUTPUT.relative_to(spam_grid.ROOT), len(rows)))


if __name__ == "__main__":
    main()

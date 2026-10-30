"""Country grid and crop-area weights on the 5 arc-minute grid of SPAM 2020 (template v3 specification section 5.13).

Shared by the scripts that aggregate global maps to the tool countries (build_gloreda_erosivity.py,
build_terraclimate_climate.py). Needs numpy, tifffile and pyshp: run these scripts with the build environment
.venv-gis, not with the model environment .venv.

Grid: WGS 84, 2160 rows x 4320 columns of 1/12 degree, row 0 at 90 N, column 0 at 180 W (the grid of the SPAM 2020
GeoTIFFs). A cell belongs to a country when its centre lies inside one of the GAUL 2024 level 1 polygons of the country
(even-odd rule over all rings of a polygon).

Weighted mean of a map X for crop k and country c (cells where X is defined):
    X(k, c) = sum(A_k x X) / sum(A_k)
with A_k the SPAM 2020 V2r2 physical area (IFPRI 2025, doi 10.7910/DVN/SWPENT; all technologies, layer _A, ha;
the yield layers _Y are not read: their unit changed from t/ha to kg/ha in V2r2) of the SPAM crop of k (spam2020_crop_mapping.csv: the FAOSTAT item of the crop mapped with the
faostat2crop table of the mapspamc R package, mapspamc_faostat_spam_crops.csv, and the separate SPAM 2020 crops).
When the crop has no SPAM area with data in the country, the weights are the total physical area of all SPAM crops.
"""
import csv
import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import shapefile
import tifffile

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
EXTERNAL_DATA_DIR = DATA_DIR / "external_data"
GAUL_ZIP = EXTERNAL_DATA_DIR / "GAUL_2024_L1.zip"
SPAM_ZIP = EXTERNAL_DATA_DIR / "SPAM 2020 V2r2.zip"
SPAM_GEOTIFF_ZIP = "Global_Geotiff/spam2020V2r2_global_physical_area.geotiff.zip"

ROWS, COLS, CELLS_PER_DEGREE = 2160, 4320, 12


def read_csv(filename):
    with open(DATA_DIR / filename, newline="", encoding="utf-8") as f:
        return [row for row in csv.DictReader(f) if any((v or "").strip() for v in row.values())]


def tool_countries():
    """{tool country code: ISO alpha-3} of the 39 countries (ifastat_country_mapping.csv, signed by FC)."""
    return {row["country"]: row["ifastat_alpha3"] for row in read_csv("ifastat_country_mapping.csv")}


def _fill_polygon(grid, shape, value):
    points = np.asarray(shape.points, dtype=float)
    if len(points) < 3:
        return
    bounds = list(shape.parts) + [len(points)]
    starts = np.concatenate([np.arange(a, b - 1) for a, b in zip(bounds[:-1], bounds[1:]) if b - a > 1])
    x0, y0 = points[starts, 0], points[starts, 1]
    x1, y1 = points[starts + 1, 0], points[starts + 1, 1]
    # row coordinate whose integers are the cell centres
    r0 = (90.0 - y0) * CELLS_PER_DEGREE - 0.5
    r1 = (90.0 - y1) * CELLS_PER_DEGREE - 0.5
    first = np.ceil(np.minimum(r0, r1)).astype(np.int64)
    count = np.ceil(np.maximum(r0, r1)).astype(np.int64) - first
    edges = np.nonzero(count > 0)[0]
    if not len(edges):
        return
    count = count[edges]
    edge = np.repeat(edges, count)
    offset = np.arange(count.sum()) - np.repeat(np.cumsum(count) - count, count)
    row = first[edge] + offset
    t = (row - r0[edge]) / (r1[edge] - r0[edge])
    col = (x0[edge] + t * (x1[edge] - x0[edge]) + 180.0) * CELLS_PER_DEGREE - 0.5
    order = np.lexsort((col, row))
    row, col = row[order], col[order]
    for r, a, b in zip(row[0::2], np.ceil(col[0::2]).astype(np.int64), np.ceil(col[1::2]).astype(np.int64)):
        if 0 <= r < ROWS:
            grid[r, max(a, 0):min(b, COLS)] = value


def country_grid(cache=None):
    """int16 grid of country indexes (position in the sorted tool countries, -1 outside) and the country list."""
    countries = sorted(tool_countries())
    if cache is not None and Path(cache).is_file():
        return np.load(cache), countries
    index = {alpha3: i for i, alpha3 in enumerate(tool_countries()[c] for c in countries)}
    grid = np.full((ROWS, COLS), -1, dtype=np.int16)
    with zipfile.ZipFile(GAUL_ZIP) as zf:
        reader = shapefile.Reader(shp=io.BytesIO(zf.read("GAUL_2024_L1.shp")),
                                  shx=io.BytesIO(zf.read("GAUL_2024_L1.shx")),
                                  dbf=io.BytesIO(zf.read("GAUL_2024_L1.dbf")))
        for i, record in enumerate(reader.iterRecords(fields=["iso3_code"])):
            if record[0] in index:
                _fill_polygon(grid, reader.shape(i), index[record[0]])
    if cache is not None:
        np.save(cache, grid)
    return grid, countries


_GEOTIFFS = None


def _geotiffs():
    """The inner archive of the physical-area GeoTIFFs, read once into memory (about 66 MB)."""
    global _GEOTIFFS
    if _GEOTIFFS is None:
        with zipfile.ZipFile(SPAM_ZIP) as zf:
            _GEOTIFFS = zipfile.ZipFile(io.BytesIO(zf.read(SPAM_GEOTIFF_ZIP)))
    return _GEOTIFFS


def spam_area(spam_crop):
    """SPAM 2020 physical area (ha, all technologies) of one SPAM crop on the grid, 0 where no data (NaN or the
    negative nodata value of V2r2)."""
    name = "spam2020V2r2_global_physical_area/spam2020_V2r2_global_A_%s_A.tif" % spam_crop
    area = tifffile.imread(io.BytesIO(_geotiffs().read(name))).astype(np.float64)
    assert area.shape == (ROWS, COLS), area.shape
    area = np.nan_to_num(area, nan=0.0)
    area[area < 0.0] = 0.0
    return area


def spam_crops():
    return sorted(n.split("_A_")[1][:4] for n in _geotiffs().namelist() if n.endswith("_A.tif"))


def weighted_country_means(values, grid, countries, crop_mapping, crops_of_interest=None):
    """Rows {crop, country, value, weights, area_ha, coverage} for every tool crop and country.

    values: dict {name: 2D array on the grid, NaN where undefined}; the means are computed for each name with the
    same weights. coverage = share of the weighting area where all values are defined."""
    n = len(countries)
    valid = np.ones((ROWS, COLS), dtype=bool)
    for array in values.values():
        valid &= np.isfinite(array)
    inside = grid >= 0
    index = grid[inside]

    def sums(weights):
        w = weights[inside]
        wv = w * valid[inside]
        total = np.bincount(index, weights=w, minlength=n)
        defined = np.bincount(index, weights=wv, minlength=n)
        means = {}
        for name, array in values.items():
            a = np.where(valid, array, 0.0)[inside]
            means[name] = np.bincount(index, weights=wv * a, minlength=n)
        return total, defined, means

    by_spam = {}
    all_area = np.zeros((ROWS, COLS))
    for spam_crop in spam_crops():
        area = spam_area(spam_crop)
        all_area += area
        by_spam[spam_crop] = sums(area)
    by_spam["all_crops"] = sums(all_area)
    out = []
    mapping = {row["crop"]: row["spam2020_crop"].upper() for row in crop_mapping}
    for crop in ["all_crops"] + sorted(mapping):
        for i, country in enumerate(countries):
            basis = "all_crops" if crop == "all_crops" else mapping[crop]
            total, defined, means = by_spam[basis]
            if defined[i] <= 0.0 and basis != "all_crops":
                basis = "all_crops"
                total, defined, means = by_spam[basis]
            row = {"crop": crop, "country": country, "weights": basis,
                   "area_ha": total[i], "coverage": defined[i] / total[i] if total[i] > 0 else 0.0}
            for name in values:
                row[name] = means[name][i] / defined[i] if defined[i] > 0 else None
            out.append(row)
    return out


def block_mean(fine, factor):
    """Mean of factor x factor blocks of a fine grid aligned with the SPAM grid, ignoring NaN."""
    rows, cols = fine.shape[0] // factor, fine.shape[1] // factor
    blocks = fine[:rows * factor, :cols * factor].reshape(rows, factor, cols, factor)
    count = np.isfinite(blocks).sum(axis=(1, 3))
    total = np.nansum(blocks, axis=(1, 3))
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(count > 0, total / np.maximum(count, 1), np.nan)


def write_rows(path, rows, columns, digits):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(columns)
        for row in rows:
            writer.writerow(["" if row[c] is None else (round(row[c], digits[c]) if c in digits else row[c])
                             for c in columns])


if __name__ == "__main__":
    sys.exit("helper module: run build_gloreda_erosivity.py or build_terraclimate_climate.py")

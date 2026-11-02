"""Build data/terraclimate1991_2020_climate.csv: annual precipitation and reference evapotranspiration per crop and
country (template v3 specification section 5.13, decision L59).

Source: TerraClimate v1.1 monthly climatology 1991-2020 (Abatzoglou et al. 2018, Scientific Data 5: 170191),
data/external_data/TerraClimate_19912020_ppt.nc and TerraClimate_19912020_pet.nc (netCDF-4, 1/24 degree, 12 months,
int32 with scale_factor 0.1, mm).

Method: annual value of a cell = sum of the 12 months (cells with a missing month are left out); mean of the 2 x 2
cells of each 1/12 degree cell of the SPAM 2020 grid; weighted mean over the SPAM physical area of the crop in the
country (spam_grid.py). ppt_pet_ratio = precipitation / PET of the aggregated values.

Usage (repository root, build environment):
    .venv-gis\\Scripts\\python scripts\\build_terraclimate_climate.py [--grid-cache FILE]
"""
import argparse

import h5py
import numpy as np

import spam_grid

OUTPUT = spam_grid.DATA_DIR / "terraclimate1991_2020_climate.csv"


def annual(variable):
    path = spam_grid.EXTERNAL_DATA_DIR / ("TerraClimate_19912020_%s.nc" % variable)
    with h5py.File(path, "r") as f:
        data = f[variable]
        fill = data.attrs["_FillValue"][0]
        scale = float(data.attrs["scale_factor"][0])
        offset = float(data.attrs["add_offset"][0])
        lat, lon = f["lat"][:], f["lon"][:]
        assert data.shape == (12, 4320, 8640) and lat[0] > lat[-1] and lon[0] < lon[-1]
        total = np.zeros(data.shape[1:])
        missing = np.zeros(data.shape[1:], dtype=bool)
        for month in range(12):
            values = data[month]
            missing |= values == fill
            total += values * scale + offset
    total[missing] = np.nan
    return spam_grid.block_mean(total, 2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--grid-cache", help="npy file to store or reuse the country grid")
    args = parser.parse_args()
    grid, countries = spam_grid.country_grid(args.grid_cache)
    values = {"annual_precipitation_mm": annual("ppt"), "annual_pet_mm": annual("pet")}
    rows = spam_grid.weighted_country_means(values, grid, countries, spam_grid.read_csv("spam2020_crop_mapping.csv"))
    for row in rows:
        p, pet = row["annual_precipitation_mm"], row["annual_pet_mm"]
        row["ppt_pet_ratio"] = p / pet if p is not None and pet else None
    columns = ["crop", "country", "weights", "area_ha", "coverage", "annual_precipitation_mm", "annual_pet_mm",
               "ppt_pet_ratio"]
    spam_grid.write_rows(OUTPUT, rows, columns, {"area_ha": 0, "coverage": 4, "annual_precipitation_mm": 0,
                                                  "annual_pet_mm": 0, "ppt_pet_ratio": 3})
    print("written %s (%d rows)" % (OUTPUT.relative_to(spam_grid.ROOT), len(rows)))


if __name__ == "__main__":
    main()

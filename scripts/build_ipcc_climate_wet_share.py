"""Build data/ipcc_climate_wet_share.csv: share of the crop area in a wet climate per crop and country, for the
climate-specific N2O factors of IPCC 2019 Refinement Vol. 4 Tables 11.1 and 11.3 (decision L64).

Climate rule (IPCC 2019 Refinement Vol. 4 Ch. 3 Annex 3A.5, Figure 3A.5.2, p. 3.48, note 4 of Table 11.1 and the
notes of Table 11.3):
- tropical = mean annual temperature (MAT) > 18 degC and <= 7 frost days per year;
- tropical cells are wet where the annual precipitation > 1000 mm, otherwise dry;
- all other cells are wet where annual precipitation / potential evapotranspiration > 1, otherwise dry.

Data: CRU TS 4.10 (Harris et al. 2020, Scientific Data 7: 109; run 2604091129), 1991-2020, decadal files
data/external_data/cru_ts4.10.{1991.2000,2001.2010,2011.2020}.{pre,pet,tmp,frs}.dat.nc.gz (netCDF classic, 0.5 degree,
monthly; read with netcdf_classic.py). Climatology of each calendar month = mean of its 30 values; annual
precipitation = sum of the 12 monthly means of pre (mm/month); annual PET = sum of the 12 monthly means of pet x days
of the month (pet in mm/day); MAT = mean of the 12 monthly means of tmp (degC); frost days = sum of the 12 monthly
means of frs (days). The cells are classified on the 0.5 degree grid; each 1/12 degree cell of the SPAM grid takes the
CRU cell that contains its centre (6 x 6 cells per CRU cell). CRU cells without data (sea) are left out.

Method: wet_share = mean of the wet cells (1) and dry cells (0) over the SPAM 2020 V2r2 physical area of the crop in
the country (spam_grid.py, GAUL 2024 countries, row all_crops for all crops). tropical_share, not read by the model,
is the share of the same area in the tropical zone.

Usage (repository root, build environment):
    .venv-gis\\Scripts\\python scripts\\build_ipcc_climate_wet_share.py [--grid-cache FILE]
"""
import argparse
import gzip

import numpy as np

import netcdf_classic
import spam_grid

OUTPUT = spam_grid.DATA_DIR / "ipcc_climate_wet_share.csv"
CRU_RUN = "2604091129"
DECADES = ("1991.2000", "2001.2010", "2011.2020")
UNITS = {"pre": "mm/month", "pet": "mm/day", "tmp": "degrees Celsius", "frs": "days"}
TROPICAL_MAT_C = 18.0
TROPICAL_FROST_DAYS = 7.0
TROPICAL_PRECIPITATION_MM = 1000.0


def cru_climatology(variable):
    """Mean of each calendar month 1991-2020, shape (12, 360, 720), north up, from 180 W; pet in mm per month."""
    sums, counts = np.zeros((12, 360, 720)), np.zeros((12, 360, 720))
    for decade in DECADES:
        with gzip.open(spam_grid.EXTERNAL_DATA_DIR / ("cru_ts4.10.%s.%s.dat.nc.gz" % (decade, variable))) as f:
            values, attributes = netcdf_classic.read(f.read())
        assert CRU_RUN in attributes[""]["source"] and attributes[variable]["units"] == UNITS[variable]
        assert values["lat"][0] == -89.75 and values["lon"][0] == -179.75
        data = values[variable].astype(float)
        assert data.shape == (120, 360, 720)
        data[data >= attributes[variable]["_FillValue"][0] / 10.0] = np.nan
        months = (np.datetime64("1900-01-01") + values["time"].astype("int64").astype("timedelta64[D]")) \
            .astype("datetime64[M]")
        days = ((months + np.timedelta64(1, "M")).astype("datetime64[D]") - months.astype("datetime64[D]")) \
            .astype(int)
        for t, month in enumerate(months.astype(int) % 12):
            sums[month] += data[t] * (days[t] if variable == "pet" else 1.0)
            counts[month] += 1
    assert np.all(counts == 30)
    return (sums / counts)[:, ::-1]


def classify(mat, frost_days, precipitation, pet):
    """(wet, tropical): 1 or 0 per cell, NaN without data."""
    with np.errstate(invalid="ignore", divide="ignore"):
        tropical = (mat > TROPICAL_MAT_C) & (frost_days <= TROPICAL_FROST_DAYS)
        wet = np.where(tropical, precipitation > TROPICAL_PRECIPITATION_MM, precipitation / pet > 1.0)
        unknown = ~np.isfinite(mat) | ((mat > TROPICAL_MAT_C) & ~np.isfinite(frost_days))
        unknown |= ~np.isfinite(precipitation) | (~tropical & ~(pet > 0.0))
    wet, tropical = wet.astype(float), tropical.astype(float)
    wet[unknown] = np.nan
    tropical[unknown] = np.nan
    return wet, tropical


def to_spam_grid(cru):
    factor = spam_grid.ROWS // cru.shape[0]
    return np.repeat(np.repeat(cru, factor, axis=0), factor, axis=1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--grid-cache", help="npy file to store or reuse the country grid")
    args = parser.parse_args()
    grid, countries = spam_grid.country_grid(args.grid_cache)
    wet, tropical = classify(cru_climatology("tmp").mean(axis=0), cru_climatology("frs").sum(axis=0),
                             cru_climatology("pre").sum(axis=0), cru_climatology("pet").sum(axis=0))
    rows = spam_grid.weighted_country_means({"wet_share": to_spam_grid(wet), "tropical_share": to_spam_grid(tropical)},
                                            grid, countries, spam_grid.read_csv("spam2020_crop_mapping.csv"))
    columns = ["crop", "country", "weights", "area_ha", "coverage", "wet_share", "tropical_share"]
    spam_grid.write_rows(OUTPUT, rows, columns, {"area_ha": 0, "coverage": 4, "wet_share": 3, "tropical_share": 3})
    print("written %s (%d rows)" % (OUTPUT.relative_to(spam_grid.ROOT), len(rows)))


if __name__ == "__main__":
    main()

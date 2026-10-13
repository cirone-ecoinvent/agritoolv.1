# Default yield per crop and country, kg/(ha and year), decision L23: FAOSTAT yield, mean of the
# latest 4 years (WFLDB Guidelines v3.0, section 3.2.1), GLO = FAOSTAT World; built from the
# FAOSTAT download by scripts/build_default_yield.py into data/default_yield.csv.
import dataloader

_DEFAULT_YIELD_TABLE = "default_yield.csv"


def _load_default_yields():
    yields = {}
    for row in dataloader.rows(_DEFAULT_YIELD_TABLE):
        yields.setdefault(row["crop"], {})[row["country"]] = float(row["yield_kg_per_ha_year"])
    return yields


YIELD_PER_YEAR_PER_CROP_PER_COUNTRY = _load_default_yields()

# Default total pesticides (active ingredients) per crop and country, g/ha, read from
# data/default_pesticides.csv: legacy values of the GD_crop sheet Pesticides_L1 (legacy, undocumented,
# provisional, per row), potato from the WFLDB 3.1 Documentation 2017 (decision L25).
import dataloader

_DEFAULT_PESTICIDES_TABLE = "default_pesticides.csv"


def _load_default_pesticides():
    pesticides = {}
    for row in dataloader.rows(_DEFAULT_PESTICIDES_TABLE):
        pesticides.setdefault(row["crop"], {})[row["country"]] = float(row["pesticides_g_per_ha"])
    return pesticides


TOTAL_PESTICIDES_PER_CROP_PER_COUNTRY = _load_default_pesticides()

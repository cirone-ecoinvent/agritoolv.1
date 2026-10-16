# Default total pesticides (active ingredients) per crop and country, g/ha (decision L43):
# - crops of data/wfldb2017_pesticides_crop_mapping.csv: total a.i. of the WFLDB 3.1 Documentation 2017
#   (data/wfldb2017_pesticides_total_ai.csv, kg/ha x 1000). "direct" datasets give the value of their
#   country and enter the GLO mean (also countries outside the tool: palm MY, coffee HN); "other_grade"
#   datasets give the value of their country to the other grade or species of the crop when WFLDB has
#   no dataset of that grade there (tomato, orange, coffee); "not_used" datasets are ignored.
#   GLO = simple mean of the direct datasets of the crop (as the legacy GLO, decision L25).
# - other crops and countries: data/default_pesticides.csv, legacy GD_crop sheet Pesticides_L1
#   (legacy, undocumented, provisional, per row).
from statistics import mean

import dataloader

_DEFAULT_PESTICIDES_TABLE = "default_pesticides.csv"
_WFLDB_TABLE = "wfldb2017_pesticides_total_ai.csv"
_WFLDB_MAPPING = "wfldb2017_pesticides_crop_mapping.csv"


def _load_legacy_pesticides():
    pesticides = {}
    for row in dataloader.rows(_DEFAULT_PESTICIDES_TABLE):
        pesticides.setdefault(row["crop"], {})[row["country"]] = float(row["pesticides_g_per_ha"])
    return pesticides


def _load_wfldb_pesticides():
    """{crop: {country: g/ha}} with GLO, from the WFLDB 2017 datasets mapped to the crop."""
    datasets = {row["wfldb_dataset_code"]: row for row in dataloader.rows(_WFLDB_TABLE)}
    pesticides, direct = {}, {}
    for use in ("direct", "other_grade"):
        for row in dataloader.rows(_WFLDB_MAPPING):
            if row["use"] != use:
                continue
            dataset = datasets[row["wfldb_dataset_code"]]
            grams = float(dataset["total_ai_kg_per_ha"]) * 1000.0
            table = pesticides.setdefault(row["crop"], {})
            if use == "direct":
                if dataset["country"] in table:
                    raise ValueError("two direct WFLDB datasets for %s %s" % (row["crop"], dataset["country"]))
                table[dataset["country"]] = grams
                direct.setdefault(row["crop"], []).append(grams)
            elif dataset["country"] in table:
                raise ValueError("other_grade dataset %s for %s, which has a direct dataset"
                                 % (row["wfldb_dataset_code"], row["crop"]))
            else:
                table[dataset["country"]] = grams
    for crop, table in pesticides.items():
        table["GLO"] = mean(direct[crop])
    return pesticides


def _load_default_pesticides():
    pesticides = _load_legacy_pesticides()
    for crop, table in _load_wfldb_pesticides().items():
        legacy = pesticides.setdefault(crop, {})
        if "GLO" in legacy:
            raise ValueError("legacy GLO row left for %s, which takes GLO from WFLDB 2017" % crop)
        overlap = set(legacy) & set(table)
        if overlap:
            raise ValueError("legacy rows %s left for %s, which WFLDB 2017 covers" % (sorted(overlap), crop))
        legacy.update(table)
    return pesticides


TOTAL_PESTICIDES_PER_CROP_PER_COUNTRY = _load_default_pesticides()

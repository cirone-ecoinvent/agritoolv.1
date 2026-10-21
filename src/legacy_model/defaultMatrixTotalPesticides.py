# Default total pesticides (active ingredients) per crop and country, g/(ha and crop cycle):
# - crops whose FAOSTAT item (data/faostat_crop_item_mapping.csv) is a crop of the Global atlas of pesticide use
#   (data/atlas2026_pesticides_country.csv, built by scripts/build_atlas_pesticides.py; decision L48): applied mass
#   of all a.i. 2016-2020 / FAOSTAT area harvested, kg/ha x 1000. The values flagged by the build script take the
#   use of data/atlas2026_pesticides_review.csv: "atlas" keeps the value, "fallback" (like a country without an atlas
#   value) takes the WFLDB 2017 value of the country (decision L43) if any, else GLO. GLO = applied mass of all
#   countries of the atlas / FAOSTAT World area.
# - other crops with WFLDB 2017 datasets (data/wfldb2017_pesticides_crop_mapping.csv; decision L43): total a.i. of
#   the WFLDB 3.1 Documentation 2017 (data/wfldb2017_pesticides_total_ai.csv, kg/ha x 1000). "direct" datasets give
#   the value of their country and enter the GLO mean (also countries outside the tool); "other_grade" datasets give
#   the value of their country to the other grade or species of the crop when WFLDB has no dataset of that grade
#   there (tomato, orange, coffee); "not_used" datasets are ignored. GLO = simple mean of the direct datasets.
# - other crops: data/default_pesticides.csv, legacy GD_crop sheet Pesticides_L1 (legacy, undocumented, provisional,
#   per row).
from statistics import mean

import dataloader

_DEFAULT_PESTICIDES_TABLE = "default_pesticides.csv"
_WFLDB_TABLE = "wfldb2017_pesticides_total_ai.csv"
_WFLDB_MAPPING = "wfldb2017_pesticides_crop_mapping.csv"
_ATLAS_TABLE = "atlas2026_pesticides_country.csv"
_ATLAS_REVIEW = "atlas2026_pesticides_review.csv"


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


def _load_atlas_pesticides(wfldb):
    """{crop: {country: g/ha}} with GLO of the tool crops whose FAOSTAT item is an atlas crop; WFLDB 2017 values of
    the crop (wfldb, as _load_wfldb_pesticides) for the countries without an atlas value or with use "fallback"."""
    atlas = {}
    for row in dataloader.rows(_ATLAS_TABLE):
        atlas.setdefault(row["faostat_item_code"], {})[row["country"]] = row
    review = {(row["atlas_crop"], row["country"]): row["use"] for row in dataloader.rows(_ATLAS_REVIEW)}
    pesticides = {}
    for crop in dataloader.rows("faostat_crop_item_mapping.csv"):
        if crop["faostat_item_code"] not in atlas:
            continue
        table = {}
        for country, row in atlas[crop["faostat_item_code"]].items():
            use = review.get((row["atlas_crop"], country), "atlas")
            if use not in ("atlas", "fallback"):
                raise ValueError("%s: use %r of %s %s" % (_ATLAS_REVIEW, use, row["atlas_crop"], country))
            if use == "atlas":
                if not row["kg_ai_per_ha"]:
                    raise ValueError("%s: %s %s has no value" % (_ATLAS_TABLE, row["atlas_crop"], country))
                table[country] = float(row["kg_ai_per_ha"]) * 1000.0
        for country, grams in wfldb.get(crop["crop"], {}).items():
            if country != "GLO":
                table.setdefault(country, grams)
        pesticides[crop["crop"]] = table
    return pesticides


def _load_default_pesticides():
    pesticides = _load_legacy_pesticides()
    wfldb = _load_wfldb_pesticides()
    atlas = _load_atlas_pesticides(wfldb)
    for crop, table in list(atlas.items()) + [(crop, table) for crop, table in wfldb.items() if crop not in atlas]:
        legacy = pesticides.setdefault(crop, {})
        if legacy:
            raise ValueError("legacy rows %s left for %s, which the atlas or WFLDB 2017 covers" % (sorted(legacy), crop))
        legacy.update(table)
    return pesticides


TOTAL_PESTICIDES_PER_CROP_PER_COUNTRY = _load_default_pesticides()

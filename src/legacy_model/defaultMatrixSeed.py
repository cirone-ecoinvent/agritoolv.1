# Seeds per ha of the sown crops, kg/(ha and crop cycle) (decision L46): the crops of data/seed_rate_crop_mapping.csv
# with use 'sua_tcf' come from data/default_seed.csv (FAOSTAT SUA seed / area harvested of the next year, 2021-2023,
# checked against the FAO Technical Conversion Factors; built by scripts/build_default_seed.py); the crops with use
# 'legacy' keep the GLO values of _LEGACY_SEEDS.
# Seedlings and trees per ha (decision L47): the crops of data/ecoinvent312_planting_crop_mapping.csv with use
# 'ecoinvent' or 'proxy' come from the ecoinvent 3.12 datasets of data/ecoinvent312_planting_rates.csv (built by
# scripts/build_ecoinvent_planting_rates.py), in the quantity of the mapping: per ha and crop cycle, or per ha and year
# for the plantings amortised over the plantation lifetime (defaultGeneration.PlantingDefaultGenerator multiplies them by
# the orchard lifetime) and for mint; the crops with use 'legacy' keep _LEGACY_SEEDLINGS and _LEGACY_TREES.
# legacy, undocumented, provisional: _LEGACY_SEEDS, _LEGACY_SEEDLINGS and _LEGACY_TREES (generated from the Quantis
# workbook GD_crop)
import statistics
from collections import defaultdict

import dataloader

_DEFAULT_SEED_TABLE = "default_seed.csv"
_PLANTING_MAPPING = "ecoinvent312_planting_crop_mapping.csv"
_PLANTING_RATES = "ecoinvent312_planting_rates.csv"

#from GD_crop Seeds_L0
#only glo as all values per country are the same
_LEGACY_SEEDS = {
    "carrot": {"GLO": 4.2},
    "cassava": {"GLO": 0.0},
    "coriander": {"GLO": 0.0},
    "flax": {"GLO": 0.0},
    "guar": {"GLO": 0.0},
    "hemp": {"GLO": 0.0},
    "sugarbeet": {"GLO": 2.1},
    "sweetcorn": {"GLO": 25.0},
    "turmeric": {"GLO": 100.0},
}

#GD_crop Seedlings_L0
_LEGACY_SEEDLINGS = {
    "chilli": {"GLO": 0.0},
    "eggplant": {"GLO": 0.0},
    "ginger": {"GLO": 0.0},
    "raspberry": {},
}

#No values, as data in GD crops are for the whole lifetime
#GD_crop Trees_L0
_LEGACY_TREES = {
    "blueberry": {},
    "cranberry": {},
    "pineapple": {},
    "sugarcane": {},
}


def _load_default_seeds():
    seeds = {crop: dict(values) for crop, values in _LEGACY_SEEDS.items()}
    for row in dataloader.rows(_DEFAULT_SEED_TABLE):
        seeds.setdefault(row["crop"], {})[row["country"]] = float(row["seed_kg_per_ha"])
    return seeds


def _load_planting_rates(template_field, legacy):
    """{crop: {country: rate}} of the crops of the template field: legacy values, and for the crops with use 'ecoinvent'
    or 'proxy' the mean of the ecoinvent datasets of the crop whose geography is the country or one of its regions
    (BR-MG -> BR), without the excluded geographies of the mapping; GLO = mean of the RoW datasets or, when ecoinvent has
    no RoW dataset with a planting input, mean of the country values (all geographies of the crop)."""
    countries = {row["country"] for row in dataloader.rows("faostat_country_mapping.csv")} - {"GLO"}
    rates = dataloader.rows(_PLANTING_RATES)
    table = {crop: dict(values) for crop, values in legacy.items()}
    for crop in dataloader.rows(_PLANTING_MAPPING):
        if crop["template_field"] != template_field or crop["use"] == "legacy":
            continue
        activities = set(crop["ecoinvent_activities"].split("|"))
        excluded = set(crop["excluded_geographies"].split("|")) - {""}
        values = defaultdict(list)
        for row in rates:
            if row["activity_name"] in activities and row["geography"] not in excluded:
                values[row["geography"].split("-")[0]].append(float(row[crop["quantity"]]))
        if not values:
            raise ValueError("%s: no dataset of %s in %s" % (_PLANTING_MAPPING, crop["crop"], _PLANTING_RATES))
        means = {country: statistics.mean(v) for country, v in values.items()}
        table[crop["crop"]] = {country: mean for country, mean in means.items() if country in countries}
        table[crop["crop"]]["GLO"] = means["RoW"] if "RoW" in means else statistics.mean(means.values())
    return table


NB_SEEDS_PER_PARTIAL_CROP_PER_COUNTRY = _load_default_seeds()

# seedlings per ha and crop cycle; asparagus (amortised) and mint: per ha and year
NB_SEEDLINGS_PER_PARTIAL_CROP_PER_COUNTRY = _load_planting_rates("nb_seedlings", _LEGACY_SEEDLINGS)

# trees per ha and year (amortised)
NB_PLANTED_TREES_PER_PARTIAL_CROP_PER_COUNTRY = _load_planting_rates("nb_planted_trees", _LEGACY_TREES)

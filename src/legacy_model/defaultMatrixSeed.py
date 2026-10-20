# Seeds per ha of the sown crops, kg/(ha and crop cycle) (decision L46): the crops of data/seed_rate_crop_mapping.csv
# with use 'sua_tcf' come from data/default_seed.csv (FAOSTAT SUA seed / area harvested of the next year, 2021-2023,
# checked against the FAO Technical Conversion Factors; built by scripts/build_default_seed.py); the crops with use
# 'legacy' keep the GLO values of _LEGACY_SEEDS.
# legacy, undocumented, provisional: _LEGACY_SEEDS and the seedling and tree matrices below (generated from the Quantis
# workbook GD_crop)
import dataloader

_DEFAULT_SEED_TABLE = "default_seed.csv"

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


def _load_default_seeds():
    seeds = {crop: dict(values) for crop, values in _LEGACY_SEEDS.items()}
    for row in dataloader.rows(_DEFAULT_SEED_TABLE):
        seeds.setdefault(row["crop"], {})[row["country"]] = float(row["seed_kg_per_ha"])
    return seeds


NB_SEEDS_PER_PARTIAL_CROP_PER_COUNTRY = _load_default_seeds()

#GD_crop Seedlings_L0
NB_SEEDLINGS_PER_PARTIAL_CROP_PER_COUNTRY = {
    "asparagus_green": {
    },
    "asparagus_white": {
    },
   "bellpepper": {
      "GLO": 0.0
   },
    "cabbage_red": {
        "GLO": 0.0
    },
    "cabbage_white": {
        "GLO": 0.0
    },
   "chilli": {
      "GLO": 0.0
   },
   "eggplant": {
      "GLO": 0.0
   },
    "ginger": {
        "GLO": 0.0
    },
   "mint":{
   },
   "onion":{
      "GLO":3.301886792
   },
   "raspberry": {
   },
    "strawberry_fresh": {
   },
    "strawberry_processing": {
    },
    "tomato_fresh": {
        "GLO": 3.125
    },
    "tomato_processing": {
        "GLO": 3.125
   }
}

#No values, as data in GD crops are for the whole lifetime
#GD_crop Trees_L0
NB_PLANTED_TREES_PER_PARTIAL_CROP_PER_COUNTRY = {
   "almond":{
   },
   "apple":{
   },
   "apricot":{
   },
   "banana":{
   },
   "blueberry": {
   },
   "cashew": {
   },
   "cocoa":{
   },
   "coconut":{
   },
    "coffee_arabica": {
    },
    "coffee_robusta": {
   },
   "cranberry": {
   },
   "grape": {
   },
    "lemon": {
    },
    "citruslime": {
    },
   "mandarin":{
   },
   "mango": {
   },
   "mulberry": {
   },
   "olive":{
   },
    "orange_fresh": {
    },
    "orange_processing": {
    },
   "palmtree":{
   },
   "peach":{
   },
   "pear":{
   },
   "pineapple":{
   },
    "pomegranate": {
    },
   "tea":{
   }
}
# legacy, undocumented, provisional: the crop tables, irrigation electricity / diesel split, EI_IRR ratios and soil
# erodibility of this module (generated from the Quantis workbook GD_crop); the country soil, precipitation and
# irrigation water source tables are read from data/wfldb2017_*.csv (decision L22), the manure shares are computed
# from FAOSTAT (decision L29), the irrigation technique shares from FAO AQUASTAT (decision L44), the mineral
# fertiliser mixes from IFASTAT (decision L45), the orchard lifetime from the ecoinvent 3.12 datasets (decision L50)
import statistics
from collections import defaultdict

import dataloader
from models.fertilisermodel import NFertiliserType, KFertiliserType, \
    PFertiliserType
from models.irrigationmodel import IrrigationType, WaterUseType
from models.manuremodel import ManureModel
from models.modelEnums import SoilTexture
from models.pmodel import LandUseCategory

# Country tables of the WFLDB 2017 background parameters (decision L22): ecoinvent 3 report
# WFLDB_BackgroundParameters_2017.xlsx, sheets 1-2; MA and CS are not in WFLDB (legacy values).
_WFLDB_PARAMETERS = "wfldb2017_agr_system_parameters.csv"
_WFLDB_WATER_SOURCES = "wfldb2017_irrigation_water_sources.csv"
_WFLDB_K_FACTORS = "wfldb2017_soil_type_k_factors.csv"


def _wfldb_country_column(column):
    return {country: row[column] for country, row in dataloader.table(_WFLDB_PARAMETERS).items()}


def _wfldb_erodibility_per_country():
    """K = sum of the soil-type shares x K-factor ** (recalculated from Panagos et al. 2014) of the WFLDB
    Documentation 2017, Tab. 6 (decision L27); countries without WFLDB soil types (MA, CS) are left out."""
    k_factors = {soil_type: row["k_factor_panagos2014_t_h_per_mj_mm"]
                 for soil_type, row in dataloader.table(_WFLDB_K_FACTORS).items()}
    erodibility = {}
    for country, row in dataloader.table(_WFLDB_PARAMETERS).items():
        shares = {soil_type: row[soil_type + "_soils_ratio"] for soil_type in k_factors}
        if None not in shares.values():
            erodibility[country] = sum(shares[t] * k_factors[t] for t in k_factors)
    return erodibility


# mm/year
ANNUAL_PRECIPITATION_PER_COUNTRY = _wfldb_country_column("annual_precipitation_mm")
CLAY_CONTENT_PER_COUNTRY = _wfldb_country_column("clay_content_ratio")
# WFLDB share of sandy soils (WRB soil type), used as sand content of the soil texture (L22)
SAND_CONTENT_PER_COUNTRY = _wfldb_country_column("sandy_soils_ratio")
# topsoil organic carbon, kg C/kg soil (WFLDB row "Humus content", calculated from the carbon content; L26)
SOIL_CARBON_CONTENT_PER_COUNTRY = _wfldb_country_column("soil_organic_carbon_ratio")
SOIL_WITH_PH_UNDER_OR_7_PER_COUNTRY = _wfldb_country_column("soil_ph_le7_ratio")
YEARLY_PRECIPITATION_AS_SNOW_PER_COUNTRY = _wfldb_country_column("precipitation_as_snow_ratio")
IRR_WATERUSE_RATIO_PER_COUNTRY = {
    country: {WaterUseType.groundwater: row["groundwater"],
              WaterUseType.surfacewater: row["surfacewater"],
              WaterUseType.nonconventional: row["nonconventional"]}
    for country, row in dataloader.table(_WFLDB_WATER_SOURCES).items()}
# Manure types per country (decision L29): FAOSTAT manure N applied to soils 2021-2023, liquid/solid split
# with the IPCC 2019 manure management systems of the country's region (decision L42), liquid volume shares
# and solid mass shares; share of the N applied as liquid manure
_COUNTRIES = [row["country"] for row in dataloader.rows("faostat_country_mapping.csv") if row["country"] != "GLO"]
_MANURE_SHARES = {country: ManureModel.country_shares(country) for country in _COUNTRIES}
MANURE_LIQUID_RATIO_PER_COUNTRY = {country: shares[0] for country, shares in _MANURE_SHARES.items()}
MANURE_SOLID_RATIO_PER_COUNTRY = {country: shares[1] for country, shares in _MANURE_SHARES.items()}
MANURE_LIQUID_N_FRACTION_PER_COUNTRY = {country: ManureModel.liquid_n_fraction(country) for country in _COUNTRIES}
# t h/(MJ mm)
SOIL_ERODIBILITY_FACTOR_PER_COUNTRY = _wfldb_erodibility_per_country()


def _orchard_lifetime_per_crop():
    """Plantation lifetime in years of the crops of orchard_lifetime_crop_mapping.csv (decision L50). Crops with use
    'ecoinvent' or 'proxy': mean of the ecoinvent 3.12 datasets of ecoinvent312_orchard_lifetime.csv whose geography is
    the country or one of its regions (BR-MG -> BR), without the datasets made with this tool and the excluded
    geographies, rounded to the whole year; GLO = the GLO dataset, else glo_lifetime_years of the mapping, else the
    mean of the country values. Crops with use 'fc' or 'legacy': glo_lifetime_years for all countries."""
    datasets = dataloader.rows("ecoinvent312_orchard_lifetime.csv")
    table = {}
    for crop in dataloader.rows("orchard_lifetime_crop_mapping.csv"):
        if crop["use"] in ("fc", "legacy"):
            table[crop["crop"]] = {"GLO": float(crop["glo_lifetime_years"])}
            continue
        activities = set(crop["ecoinvent_activities"].split("|"))
        excluded = set(crop["excluded_geographies"].split("|")) - {""}
        values = defaultdict(list)
        for row in datasets:
            if row["activity_name"] in activities and row["geography"] not in excluded \
                    and row["made_with_this_tool"] == "no":
                values[row["geography"].split("-")[0]].append(float(row["lifetime_years"]))
        if not values:
            raise ValueError("orchard_lifetime_crop_mapping.csv: no dataset of %s in ecoinvent312_orchard_lifetime.csv"
                             % crop["crop"])
        means = {geography: float(round(statistics.mean(v))) for geography, v in values.items()}
        table[crop["crop"]] = {country: mean for country, mean in means.items() if country in _COUNTRIES}
        if "GLO" in means:
            table[crop["crop"]]["GLO"] = means["GLO"]
        elif crop["glo_lifetime_years"]:
            table[crop["crop"]]["GLO"] = float(crop["glo_lifetime_years"])
        else:
            table[crop["crop"]]["GLO"] = float(round(statistics.mean(means.values())))
    return table


# years
ORCHARD_LIFETIME_PER_CROP_PER_COUNTRY = _orchard_lifetime_per_crop()


def _n_uptake_per_kg_main_product():
    """kg N per kg fresh main product, residues included (WFLDB Guidelines v3.0 section 3.6.1; decision L28):
    (N main product + residue ratio x N residues) / 1000, with the contents of the WFLDB Background Parameters
    2017 sheet 4 and the residue ratio = by-product / main product reference yield of GRUDAF 2009 Tab. 1
    (or the legacy ratio given in n_uptake_crop_parameters.csv). Tree crops: main product only, their residues are a
    fixed amount per ha (N_UPTAKE_OF_TREE_RESIDUES_PER_CROP)."""
    contents = dataloader.table("wfldb2017_crop_nutrient_contents.csv")
    grudaf = dataloader.table("grudaf2009_table1_reference_yields.csv")
    n_uptake = {}
    for row in dataloader.rows("n_uptake_crop_parameters.csv"):
        content = contents[row["wfldb_crop"]]
        if row["grudaf_crop"]:
            reference = grudaf[row["grudaf_crop"]]
            ratio = reference["by_product_reference_yield_dt_per_ha"] / reference["main_reference_yield_dt_per_ha"]
        else:
            ratio = float(row["residue_ratio"] or 0.0)
        n_uptake[row["crop"]] = (content["n_main_g_per_kg_fm"] + ratio * content["n_residue_g_per_kg_fm"]) / 1000.0
    return n_uptake


def _n_uptake_of_tree_residues():
    """kg N/(ha and crop cycle) in the residues of the tree crops (tree_residues = yes in n_uptake_crop_parameters.csv;
    decision L32): tree_crop_residues_kg_fm_per_ha x N of haulm or stem of the WFLDB Background Parameters 2017
    sheet 4, independent of the yield."""
    contents = dataloader.table("wfldb2017_crop_nutrient_contents.csv")
    residues = dataloader.param("tree_crop_residues_kg_fm_per_ha")
    return {row["crop"]: residues * contents[row["wfldb_crop"]]["n_residue_g_per_kg_fm"] / 1000.0
            for row in dataloader.rows("n_uptake_crop_parameters.csv") if row["tree_residues"] == "yes"}


def _n_uptake_per_kg_main_product_other_crops():
    """kg N per kg fresh main product of the crops without WFLDB level 1 coefficients (decision L41), for the N uptake
    of the nitrate model and the default mineral N of decision L57 (n_uptake_other_crop_parameters.csv): N of the
    crop product of Ludemann et al. 2023 (World coefficients of the FAO Cropland Nutrient Budget) or, for fibre flax
    and hemp, N of main and by-product of GRUDAF 2009 Tab. 1 per kg of main product; plus, for the field crops, the
    above-ground residues of IPCC 2019 Table 11.1a: DRY x R_AG x N_AG."""
    ludemann = dataloader.table("ludemann2023_world_crop_coefficients.csv")
    grudaf = dataloader.table("grudaf2009_table1_reference_yields.csv")
    ipcc = dataloader.table("ipcc2019_table11_1a.csv")
    n_uptake = {}
    for row in dataloader.rows("n_uptake_other_crop_parameters.csv"):
        if row["grudaf_crop"]:
            reference = grudaf[row["grudaf_crop"]]
            n = ((reference["n_uptake_main_kg_per_ha"] + reference["n_uptake_by_product_kg_per_ha"])
                 / (reference["main_reference_yield_dt_per_ha"] * 100.0))  # dt -> kg
        else:
            n = ludemann[row["ludemann_item_code"]]["n_kg_per_t_fm"] / 1000.0
        if row["ipcc_residue_crop"]:
            residues = ipcc[row["ipcc_residue_crop"]]
            n += residues["dry"] * residues["r_ag"] * residues["n_ag_kg_per_kg_dm"]
        n_uptake[row["crop"]] = n
    return n_uptake


# kg N / kg FM of the main product
N_UPTAKE_PER_KG_MAIN_PRODUCT_PER_CROP = _n_uptake_per_kg_main_product()
# kg N / kg FM of the main product, crops without level 1 coefficients (nitrate model, L57)
N_UPTAKE_PER_KG_MAIN_PRODUCT_OTHER_CROPS = _n_uptake_per_kg_main_product_other_crops()
# Default mineral N of the crops without level 1 coefficients where IFA gives no rate for the country (decision L57):
# ifa_crop_median or n_uptake; crops not listed (mulberry): 0
MINERAL_N_RULE_WITHOUT_IFA_RATE = {row["crop"]: row["mineral_n_without_ifa_rate"]
                                   for row in dataloader.rows("n_uptake_other_crop_parameters.csv")}
# kg N / ha of the tree residues
N_UPTAKE_OF_TREE_RESIDUES_PER_CROP = _n_uptake_of_tree_residues()
# Legumes: their default N uptake counts only legume_uptake_share of the uptake (decision L30)
# kg N / ha of the crops without coefficients (mulberry): legacy, undocumented, provisional (decision L55)
LEGACY_N_UPTAKE_PER_CROP_PER_COUNTRY = dataloader.crop_country_table("legacy_n_uptake.csv", "n_uptake_kg_per_ha")
LEGUME_CROPS = frozenset(crop for crop, row in dataloader.table("crop_types.csv", numeric=False).items()
                         if row["legume"] == "yes")


def _pk_per_kg_main_product():
    """kg P2O5 and kg K2O per kg fresh main product (WFLDB Guidelines v3.0 section 3.6.1: for P and K only the
    products taken off the field; decision L31), with the contents of the WFLDB Background Parameters 2017 sheet 4,
    for the crops of n_uptake_crop_parameters.csv and pk_crop_parameters.csv."""
    contents = dataloader.table("wfldb2017_crop_nutrient_contents.csv")
    crops = dataloader.rows("n_uptake_crop_parameters.csv") + dataloader.rows("pk_crop_parameters.csv")
    return {row["crop"]: {"p2o5": contents[row["wfldb_crop"]]["p2o5_main_g_per_kg_fm"] / 1000.0,
                          "k2o": contents[row["wfldb_crop"]]["k2o_main_g_per_kg_fm"] / 1000.0}
            for row in crops}


# kg P2O5 and kg K2O / kg FM of the main product, {crop: {"p2o5": ..., "k2o": ...}}
PK_PER_KG_MAIN_PRODUCT_PER_CROP = _pk_per_kg_main_product()

_IFA_LEVELS = ("exact", "subgroup", "group")
_IFA_NUTRIENTS = ("n", "p2o5", "k2o")
_IFA_REGION_MIN_COUNTRIES = 2  # a region rate needs at least two FUBC countries (decision L37)


def _ifa_best_match(rows, crop, mapping):
    """(level, rows) of the best match level of a crop among the FUBC rows of one country, (None, []) if none."""
    found = {}
    for row in rows:
        level = mapping.get((row["fubc_crop"], crop))
        if level:
            found.setdefault(level, []).append(row)
    for level in _IFA_LEVELS:
        if level in found:
            return level, found[level]
    return None, []


def _ifa_area_mean(rows):
    """Area-weighted mean rate per nutrient, None for a nutrient without a value."""
    rates = {}
    for nutrient in _IFA_NUTRIENTS:
        pairs = [(float(row[nutrient + "_kg_per_ha"]), float(row["area_ha"] or 1.0))
                 for row in rows if row[nutrient + "_kg_per_ha"]]
        rates[nutrient] = sum(v * a for v, a in pairs) / sum(a for _, a in pairs) if pairs else None
    return rates


def _ifa_region_rate(pools, crop, mapping, factor, fubc_factor):
    """Rate per nutrient of a crop from the FUBC countries of a region that report it at the best match level found
    in the region, each country's rate combined by area: median over the countries times the factor of the country
    (decision L37), at most the highest rate of these countries, each brought to 2021-2023 with its own factor
    (decision L53; a country without factor counts unscaled); None if fewer countries than _IFA_REGION_MIN_COUNTRIES
    report the crop."""
    per_level = {}
    for rows in pools:
        level, matched = _ifa_best_match(rows, crop, mapping)
        if level:
            per_level.setdefault(level, []).append((rows[0]["fubc_country"], _ifa_area_mean(matched)))
    level = next((level for level in _IFA_LEVELS if level in per_level), None)
    if level is None or len(per_level[level]) < _IFA_REGION_MIN_COUNTRIES:
        return None
    rates = {}
    for nutrient in _IFA_NUTRIENTS:
        values = [(fubc_country, country_rates[nutrient]) for fubc_country, country_rates in per_level[level]
                  if country_rates[nutrient] is not None]
        if not values:
            rates[nutrient] = None
            continue
        highest = max(rate * (fubc_factor.get((fubc_country, nutrient)) or 1.0) for fubc_country, rate in values)
        rates[nutrient] = min(statistics.median(rate for _, rate in values) * factor[nutrient], highest)
    return rates


def _ifa_mineral_fertiliser():
    """kg N, P2O5 and K2O/ha of mineral fertilisers per crop and country, IFA Fertilizer Use by Crop (Ludemann et al.
    2022; decisions L33, L34, L37): mean rate over the total crop area, {crop: {country: {"n": .., "p2o5": ..,
    "k2o": ..}}}, None for a nutrient without a value.

    FUBC crop names are matched to the crops with ifa_fubc_crop_mapping.csv. The FUBC data of the country first
    (ifa_fubc_country_mapping.csv): the best match level (exact, then subgroup, then group), the rows of that level
    combined by area. A crop missing there, and every crop of the countries without FUBC data: the FUBC 9 countries of
    the IFA region of the country, median over the countries at the best level found in the region, at least
    _IFA_REGION_MIN_COUNTRIES countries (decision L37), at most the highest rate of these countries (decision L53).
    Rates of FUBC 9 and of the regions are brought to 2021-2023 with the ratio of the IFASTAT consumption of the
    country (ifastat_fertiliser_time_factor.csv, decision L53); the earlier reports of the countries without FUBC 9
    data are used as they are."""
    mapping = {(row["fubc_crop"], crop): row["match"]
               for row in dataloader.rows("ifa_fubc_crop_mapping.csv") for crop in row["crops"].split()}
    by_country = {}
    for row in dataloader.rows("ifa_fubc_rates.csv"):
        by_country.setdefault(row["fubc_country"], []).append(row)
    latest = max(int(row["fubc_report"]) for rows in by_country.values() for row in rows)
    scale, fubc_scale = {}, {}
    for row in dataloader.rows("ifastat_fertiliser_time_factor.csv"):
        factor = float(row["factor"]) if row["factor"] else None
        if row["country"]:
            scale[(row["country"], row["nutrient"].lower())] = factor
        if row["fubc_country"]:
            fubc_scale[(row["fubc_country"], row["nutrient"].lower())] = factor
    table = {}
    for country_row in dataloader.rows("ifa_fubc_country_mapping.csv"):
        country = country_row["country"]
        own = by_country.get(country_row["fubc_country"], [])
        region = [rows for rows in by_country.values()
                  if rows[0]["region_ifa"] == country_row["region_ifa"] and int(rows[0]["fubc_report"]) == latest]
        factor = {nutrient: scale[(country, nutrient)] for nutrient in _IFA_NUTRIENTS}
        for crop in {crop for _, crop in mapping}:
            level, matched = _ifa_best_match(own, crop, mapping)
            if level:
                own_factor = factor if int(matched[0]["fubc_report"]) == latest else dict.fromkeys(factor, 1.0)
                rates = {nutrient: None if rate is None else rate * own_factor[nutrient]
                         for nutrient, rate in _ifa_area_mean(matched).items()}
            else:
                rates = _ifa_region_rate(region, crop, mapping, factor, fubc_scale)
            if rates is not None:
                table.setdefault(crop, {})[country] = rates
    return table


# kg N, P2O5 and K2O/ha of mineral fertilisers in 2021-2023 (IFA, decisions L33, L34, L37, L53),
# {crop: {country: {..}}}
IFA_MINERAL_FERTILISER_PER_CROP_PER_COUNTRY = _ifa_mineral_fertiliser()

#Generated from GD_crop GrossEnergy_C_L1 column D, kgC/kgDM
# Mireille&Raphaël for Bell pepper, cabbage, cashew, cassava, chilli, cotton, eggplant, flax, grape, guar, hemp, lentil, mango, mulberry
# Castor bean: http://www.modernscientificpress.com/Journals/ViewArticle.aspx?gkN1Z6Pb60HNQPymfPQlZIiDnrBBtQSfoCsKufNADqZ4TrWuS7h5KvbfIK0SLlFq
# Chickpea:Calculated from Energy Gross Calorific data
# Coriander:https://www.biogeosciences-discuss.net/bg-2017-322/bg-2017-322.pdf
# Ginger: https://www.biogeosciences-discuss.net/bg-2017-322/bg-2017-322.pdf
# Pearl Millet:https://www.biogeosciences-discuss.net/bg-2017-322/bg-2017-322.pdf
# Sesame seed: https://www.biogeosciences-discuss.net/bg-2017-322/bg-2017-322.pdf
# Turmenic: https://www.biogeosciences-discuss.net/bg-2017-322/bg-2017-322.pdf
# Pomegranate: https://www.biogeosciences-discuss.net/bg-2017-322/bg-2017-322.pdf
CARBON_CONTENT_PER_CROP = {
                "almond":0.62655914,
                "apple":0.431788079,
                "apricot":0.475,
    "asparagus_green": 0.475,
    "asparagus_white": 0.475,
                "banana":0.429522,
    "bellpepper": 0.73,
    "blueberry": 0.4494,
    "cabbage_red": 0.64,
    "cabbage_white": 0.64,
                "carrot":0.475,
    "cashew": 0.9,
    "cassava": 0.875,
    "castor_beans": 0.52,
    "chick_pea": 0.399,
    "chilli": 0.73,
                "cocoa":0.535987,
                "coconut":0.645262412752311,
    "coffee_arabica": 0.475,
    "coffee_robusta": 0.475,
    "coriander": 0.43,
    "cotton": 0.45,
    "cranberry": 0.4451,
    "eggplant": 0.54,
    "flax": 0.46,
    "ginger": 0.43,
    "grape": 0.8,
    "guar": 0.45,
    "hemp": 0.44,
    "lemon": 0.3841230769,
    "citruslime": 0.3841230769,
    "lentil": 0.6,
                "linseed":0.590234292,
                "maizegrain":0.43501682,
                "mandarin":0.3841230769,
    "mango": 0.75,
                "mint":0.445395683453237,
    "mulberry": 0.7,
                "oat":0.475,
                "olive":0.599451774112943,
                "onion":0.424377803,
    "orange_fresh": 0.3841230769,
    "orange_processing": 0.3841230769,
                "palmtree":0.599451774112943,
                "peach":0.412732283,
                "peanut":0.58063,
                "pear":0.475,
    "pearl_millet": 0.413,
                "pineapple":0.5, #no src
    "pomegranate": 0.471,
                "potato":0.423959628,
                "rapeseed":0.47088,
    "raspberry": 0.4553,
                "rice":0.475,
    "sesame_seed": 0.43,
                "soybean":0.681929577464789,
    "strawberry_fresh": 0.475,
    "strawberry_processing": 0.475,
                "sugarbeet":0.38146638,
                "sugarcane":0.475,
                "sunflower":0.842802816901409,
                "sweetcorn":0.43501682,
                "tea":0.475,
    "tomato_fresh": 0.383275862,
    "tomato_processing": 0.383275862,
    "turmeric": 0.43,
                "wheat":0.42410592
    }


#from GD_crop Cfactor_L1
# Mireille&Raphaël for Bell pepper, cabbage, cashew, cassava, chilli, cotton, eggplant, flax, grape, guar, hemp, lentil, mango, mulberry
# Castor bean: (oil seeds) https://www.sciencedirect.com/science/article/pii/S0264837715001611
# Chickpea: (dried pulses) https://www.sciencedirect.com/science/article/pii/S0264837715001611
# Coriander:(other fodder crops) https://www.sciencedirect.com/science/article/pii/S0264837715001611
# Ginger:(potatoes) https://www.sciencedirect.com/science/article/pii/S0264837715001611
# Pearl millet:(MIllet and other cereals) https://www.sciencedirect.com/science/article/pii/S0264837715001611
# Sesame seed: (oil seeds) https://www.sciencedirect.com/science/article/pii/S0264837715001611
# Turmenic:(potatoes) https://www.sciencedirect.com/science/article/pii/S0264837715001611
# Pomegranate: (grove) https://www.researchgate.net/figure/235986141_TABLE-2--CORINE-land-use-code-and-corresponding-C-factor
CROP_FACTOR_PER_CROP = {
        "almond":0.1,
        "apple":0.1,
        "apricot":0.1,
    "asparagus_green": 0.5,
    "asparagus_white": 0.5,
        "banana":0.33,
    "bellpepper": 0.3,
    "blueberry": 0.3,
    "cabbage_red": 0.3,
    "cabbage_white": 0.3,
    "carrot": 0.5,
    "cashew": 0.25,
    "cassava": 0.5,
    "castor_beans": 0.23,
    "chick_pea": 0.32,
    "chilli": 0.3,
        "cocoa":0.21,
        "coconut":0.3,
    "coffee_arabica": 0.26,
    "coffee_robusta": 0.26,
    "coriander": 0.18,
    "cotton": 0.6,
    "cranberry": 0.3,
    "eggplant": 0.48,
    "flax": 0.18,
    "ginger": 0.34,
    "grape": 0.15,
    "guar": 0.3,
    "hemp": 0.45,
    "lemon": 0.1,
    "citruslime": 0.1,
    "lentil": 0.3,
        "linseed":0.18,
        "maizegrain":0.35,
        "mandarin":0.1,
    "mango": 0.25,
        "mint":0.47,
    "mulberry": 0.5,
        "oat":0.26,
        "olive":0.1,
        "onion":0.45,
    "orange_fresh": 0.1,
    "orange_processing": 0.1,
        "palmtree":0.21,
        "peach":0.1,
        "peanut":0.51,
        "pear":0.1,
    "pearl_millet": 0.18,
    "pineapple": 0.48,
    "pomegranate": 0.1,
        "potato":0.44,
        "rapeseed":0.33,
    "raspberry": 0.3,
        "rice":0.17,
    "sesame_seed": 0.28,
        "soybean":0.28,
    "strawberry_fresh": 0.47,
    "strawberry_processing": 0.47,
        "sugarbeet":0.35,
        "sugarcane":0.4,
        "sunflower":0.32,
        "sweetcorn":0.37,
        "tea":0.3,
    "tomato_fresh": 0.47,
    "tomato_processing": 0.47,
    "turmeric": 0.34,
    "wheat": 0.22
        }

#src: ecoinvent report no. 15a
# Mireille&Raphaël for Bell pepper, cabbage, cashew, cassava, chilli, cotton, eggplant, flax, grape, guar, hemp, lentil, mango, mulberry
# Castor beans: Calculated from Crop Carbon Content value
# Chickpea (only seed):  Calculated from Crop Carbon Content value https://books.google.ch/books?id=zf3VpYKr9aUC&pg=PA103&lpg=PA103&dq=energy+gross+calorific+value+chickpea&source=bl&ots=erh2xBkc-8&sig=G4DzPDl7hxErg1n1yBS3dy3235Q&hl=en&sa=X&ved=0ahUKEwi2goCvrpjYAhVRoqQKHbhzD_IQ6AEILTAB#v=onepage&q=energy%20gross%20calorific%20value%20chickpea&f=false
# Coriander: Calculated from Crop Carbon Content value
# Ginger: Calculated from Crop Carbon Content value
# Millet: Calculated from Crop Carbon Content value
# Sesame seed: Calculated from Crop Carbon Content value
# Turmenic: Calculated from Crop Carbon Content value
# Pomegranate: Calculated from Crop Carbon Content value
#MJ/kgDM
ENERGY_GROSS_CALORIFIC_VALUE_PER_CROP_PARTIAL = {
    "bellpepper": 30.92,
    "blueberry": 13.28,
    "cabbage_red": 27.17,
    "cabbage_white": 27.17,
    "cashew": 37.95,
    "cassava": 36.9,
    "castor_beans": 21.87,
    "chick_pea": 16.81,
    "chilli": 30.92,
    "coriander": 18.15,
    "cotton": 19.06,
    "cranberry": 11.91,
    "eggplant": 22.79,
    "flax": 19.19,
    "ginger": 18.15,
    "grape": 33.91,
    "guar": 18.98,
    "hemp": 18.75,
    "lentil": 25.3,
            "maizegrain": 18.52,
    "mango": 31.75,
    "mulberry": 18.98,
    "pearl_millet": 17.41,
    "pomegranate": 19.85,
            "potato": 17.59,
            "rapeseed": 26.48,
    "raspberry": 10.72,
            "rice": 18.11,#Wheat grains
    "sesame_seed": 18.15,
    "strawberry_fresh": 12.57,
    "strawberry_processing": 12.57,
            "soybean": 22.98,
            "sugarbeet": 16.43,
            "sunflower": 30.25,#sunflower grains
            "sweetcorn": 18.52,#grain maize
    "turmeric": 18.15,
            "wheat": 18.11#Wheat grains
            }

# Mineral fertiliser mixes per country (decision L45): share of each fertiliser type in the N, P2O5 and K2O consumed
# in 2021-2023, from the fertilizer consumption by product of IFA, IFASTAT (data/ifastat_fertiliser_mix.csv, built by
# scripts/build_ifastat_fertiliser_mix.py with the product -> type rules of data/ifastat_product_type_mapping.csv).
_FERTILISER_MIX = "ifastat_fertiliser_mix.csv"
_FERTILISER_MIX_TYPES = {"N": NFertiliserType, "P2O5": PFertiliserType, "K2O": KFertiliserType}


def _fertiliser_mix(nutrient):
    fertiliser_types = _FERTILISER_MIX_TYPES[nutrient]
    mix = {}
    for row in dataloader.rows(_FERTILISER_MIX):
        if row["nutrient"] == nutrient:
            shares = mix.setdefault(row["country"], {fertiliser_type: 0.0 for fertiliser_type in fertiliser_types})
            shares[fertiliser_types(row["fertiliser_type"])] = float(row["share"])
    return {country: {fertiliser_type: share / sum(shares.values()) for fertiliser_type, share in shares.items()}
            for country, shares in mix.items()}


FERT_N_RATIO_PER_COUNTRY = _fertiliser_mix("N")
FERT_P_RATIO_PER_COUNTRY = _fertiliser_mix("P2O5")
FERT_K_RATIO_PER_COUNTRY = _fertiliser_mix("K2O")

# Generated in GD_crop (combinaison of IrrTechn_L0 and IrrTechn_L1)
# using =""""&B$3&""":{IrrigationType.surface_irrigation_no_energy:0.0"&",  IrrigationType.surface_irrigation_electricity:"&B5&",  IrrigationType.surface_irrigation_diesel:"&B6&",  IrrigationType.sprinkler_irrigation_electricity:"&B7&",  IrrigationType.sprinkler_irrigation_diesel:"&B8&",  IrrigationType.drip_irrigation_electricity:"&B9&", IrrigationType.drip_irrigation_diesel:"&B10&"},"
# Technique shares of ICID 2012 (WFLDB Guidelines v3.0 Tab. 32) or level 0 defaults. Since decision L44 only
# used for the countries marked legacy in data/irrigation_technique_source.csv (NL) and for the
# electricity / diesel split of each country.
_LEGACY_IRR_TECH_RATIO_PER_COUNTRY = {
   "AR":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.24105504587156,
      IrrigationType.surface_irrigation_diesel:0.723165137614679,
      IrrigationType.sprinkler_irrigation_electricity:0.0036697247706422,
      IrrigationType.sprinkler_irrigation_diesel:0.0110091743119266,
      IrrigationType.drip_irrigation_electricity:0.00527522935779817,
      IrrigationType.drip_irrigation_diesel:0.0158256880733945
   },
   "AU":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.718978388998035,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.206082514734774,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.0749390962671906,
      IrrigationType.drip_irrigation_diesel:0
   },
   "BE":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.0185185185185185,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.972222222222222,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.00925925925925926,
      IrrigationType.drip_irrigation_diesel:0
   },
   "BR":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.192036629213483,
      IrrigationType.surface_irrigation_diesel:0.192036629213483,
      IrrigationType.sprinkler_irrigation_electricity:0.271124494382022,
      IrrigationType.sprinkler_irrigation_diesel:0.271124494382022,
      IrrigationType.drip_irrigation_electricity:0.0368388764044944,
      IrrigationType.drip_irrigation_diesel:0.0368388764044944
   },
   "CA":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.207973563218391,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.785090804597701,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.00693563218390805,
      IrrigationType.drip_irrigation_diesel:0
   },
   "CH":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.0185185185185185,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.972222222222222,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.00925925925925926,
      IrrigationType.drip_irrigation_diesel:0
   },
   "CI":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.22,
      IrrigationType.surface_irrigation_diesel:0.66,
      IrrigationType.sprinkler_irrigation_electricity:0.02875,
      IrrigationType.sprinkler_irrigation_diesel:0.08625,
      IrrigationType.drip_irrigation_electricity:0.00125,
      IrrigationType.drip_irrigation_diesel:0.00375
   },
   "CL":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.964220183486238,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.0146788990825688,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.0211009174311927,
      IrrigationType.drip_irrigation_diesel:0
   },
   "CN":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.461248060708263,
      IrrigationType.surface_irrigation_diesel:0.461248060708263,
      IrrigationType.sprinkler_irrigation_electricity:0.024677150084317,
      IrrigationType.sprinkler_irrigation_diesel:0.024677150084317,
      IrrigationType.drip_irrigation_electricity:0.0140747892074199,
      IrrigationType.drip_irrigation_diesel:0.0140747892074199
   },
   "CO":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.24105504587156,
      IrrigationType.surface_irrigation_diesel:0.723165137614679,
      IrrigationType.sprinkler_irrigation_electricity:0.0036697247706422,
      IrrigationType.sprinkler_irrigation_diesel:0.0110091743119266,
      IrrigationType.drip_irrigation_electricity:0.00527522935779817,
      IrrigationType.drip_irrigation_diesel:0.0158256880733945
   },
   "CR":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.225806451612903,
      IrrigationType.surface_irrigation_diesel:0.67741935483871,
      IrrigationType.sprinkler_irrigation_electricity:0.0161290322580645,
      IrrigationType.sprinkler_irrigation_diesel:0.0483870967741936,
      IrrigationType.drip_irrigation_electricity:0.00806451612903226,
      IrrigationType.drip_irrigation_diesel:0.0241935483870968
   },
   "DE":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.0185185185185185,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.972222222222222,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.00925925925925926,
      IrrigationType.drip_irrigation_diesel:0
   },
   "EC":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.24105504587156,
      IrrigationType.surface_irrigation_diesel:0.723165137614679,
      IrrigationType.sprinkler_irrigation_electricity:0.0036697247706422,
      IrrigationType.sprinkler_irrigation_diesel:0.0110091743119266,
      IrrigationType.drip_irrigation_electricity:0.00527522935779817,
      IrrigationType.drip_irrigation_diesel:0.0158256880733945
   },
   "ES":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.296592219020173,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.225506628242075,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.477901152737752,
      IrrigationType.drip_irrigation_diesel:0
   },
   "FI":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.857142857142857,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.142857142857143,
      IrrigationType.drip_irrigation_diesel:0
   },
   "FR":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.488586206896552,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.475793103448276,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.0356206896551724,
      IrrigationType.drip_irrigation_diesel:0
   },
   "GH":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.22,
      IrrigationType.surface_irrigation_diesel:0.66,
      IrrigationType.sprinkler_irrigation_electricity:0.02875,
      IrrigationType.sprinkler_irrigation_diesel:0.08625,
      IrrigationType.drip_irrigation_electricity:0.00125,
      IrrigationType.drip_irrigation_diesel:0.00375
   },
   "HU":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.127272727272727,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.840909090909091,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.0318181818181818,
      IrrigationType.drip_irrigation_diesel:0
   },
   "ID":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.245394736842105,
      IrrigationType.surface_irrigation_diesel:0.736184210526316,
      IrrigationType.sprinkler_irrigation_electricity:0.00131578947368421,
      IrrigationType.sprinkler_irrigation_diesel:0.00394736842105263,
      IrrigationType.drip_irrigation_electricity:0.00328947368421053,
      IrrigationType.drip_irrigation_diesel:0.00986842105263158
   },
   "IL":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.0043290043290044,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.25974025974026,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.735930735930736,
      IrrigationType.drip_irrigation_diesel:0
   },
   "IN":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.459423481116585,
      IrrigationType.surface_irrigation_diesel:0.459423481116585,
      IrrigationType.sprinkler_irrigation_electricity:0.0249995073891626,
      IrrigationType.sprinkler_irrigation_diesel:0.0249995073891626,
      IrrigationType.drip_irrigation_electricity:0.0155770114942529,
      IrrigationType.drip_irrigation_diesel:0.0155770114942529
   },
   "IT":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.41882734082397,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.367476779026217,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.213695880149813,
      IrrigationType.drip_irrigation_diesel:0
   },
   "KE":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.22,
      IrrigationType.surface_irrigation_diesel:0.66,
      IrrigationType.sprinkler_irrigation_electricity:0.02875,
      IrrigationType.sprinkler_irrigation_diesel:0.08625,
      IrrigationType.drip_irrigation_electricity:0.00125,
      IrrigationType.drip_irrigation_diesel:0.00375
   },
   "LK":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.245394736842105,
      IrrigationType.surface_irrigation_diesel:0.736184210526316,
      IrrigationType.sprinkler_irrigation_electricity:0.00131578947368421,
      IrrigationType.sprinkler_irrigation_diesel:0.00394736842105263,
      IrrigationType.drip_irrigation_electricity:0.00328947368421053,
      IrrigationType.drip_irrigation_diesel:0.00986842105263158
   },
   "MX":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.903225806451613,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.0645161290322581,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.032258064516129,
      IrrigationType.drip_irrigation_diesel:0
   },
    "MA": {
        IrrigationType.surface_irrigation_no_energy: 0.0,
        IrrigationType.surface_irrigation_electricity: 0.0715,
        IrrigationType.surface_irrigation_diesel: 0.6435,
        IrrigationType.sprinkler_irrigation_electricity: 0.0085,
        IrrigationType.sprinkler_irrigation_diesel: 0.0765,
        IrrigationType.drip_irrigation_electricity: 0.02,
        IrrigationType.drip_irrigation_diesel: 0.18
    },
   "NL":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.0185185185185185,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.972222222222222,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.00925925925925926,
      IrrigationType.drip_irrigation_diesel:0
   },
   "NZ":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.0185185185185185,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.972222222222222,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.00925925925925926,
      IrrigationType.drip_irrigation_diesel:0
   },
   "PE":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.24105504587156,
      IrrigationType.surface_irrigation_diesel:0.723165137614679,
      IrrigationType.sprinkler_irrigation_electricity:0.0036697247706422,
      IrrigationType.sprinkler_irrigation_diesel:0.0110091743119266,
      IrrigationType.drip_irrigation_electricity:0.00527522935779817,
      IrrigationType.drip_irrigation_diesel:0.0158256880733945
   },
   "PH":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.247728618421053,
      IrrigationType.surface_irrigation_diesel:0.743185855263158,
      IrrigationType.sprinkler_irrigation_electricity:0.00118009868421053,
      IrrigationType.sprinkler_irrigation_diesel:0.00354029605263158,
      IrrigationType.drip_irrigation_electricity:0.00109128289473684,
      IrrigationType.drip_irrigation_diesel:0.00327384868421053
   },
   "PL":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.87,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.05,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.08,
      IrrigationType.drip_irrigation_diesel:0
   },
   "RU":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.229022988505747,
      IrrigationType.surface_irrigation_diesel:0.687068965517241,
      IrrigationType.sprinkler_irrigation_electricity:0.0132183908045977,
      IrrigationType.sprinkler_irrigation_diesel:0.0396551724137931,
      IrrigationType.drip_irrigation_electricity:0.00775862068965517,
      IrrigationType.drip_irrigation_diesel:0.0232758620689655
   },
    "CS": {
        IrrigationType.surface_irrigation_no_energy: 0.0,
        IrrigationType.surface_irrigation_electricity: 0.0251,
        IrrigationType.surface_irrigation_diesel: 0.0251,
        IrrigationType.sprinkler_irrigation_electricity: 0.44655,
        IrrigationType.sprinkler_irrigation_diesel: 0.44655,
        IrrigationType.drip_irrigation_electricity: 0.02835,
        IrrigationType.drip_irrigation_diesel: 0.02835
    },
   "TH":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.245394736842105,
      IrrigationType.surface_irrigation_diesel:0.736184210526316,
      IrrigationType.sprinkler_irrigation_electricity:0.00131578947368421,
      IrrigationType.sprinkler_irrigation_diesel:0.00394736842105263,
      IrrigationType.drip_irrigation_electricity:0.00328947368421053,
      IrrigationType.drip_irrigation_diesel:0.00986842105263158
   },
   "TR":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.878277153558053,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.0936329588014981,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.0280898876404494,
      IrrigationType.drip_irrigation_diesel:0
   },
   "UA":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.25,
      IrrigationType.sprinkler_irrigation_diesel:0.75,
      IrrigationType.drip_irrigation_electricity:0,
      IrrigationType.drip_irrigation_diesel:0
   },
   "US":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.433690111336032,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.49992624048583,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.0663836481781377,
      IrrigationType.drip_irrigation_diesel:0
   },
   "VN":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.245394736842105,
      IrrigationType.surface_irrigation_diesel:0.736184210526316,
      IrrigationType.sprinkler_irrigation_electricity:0.00131578947368421,
      IrrigationType.sprinkler_irrigation_diesel:0.00394736842105263,
      IrrigationType.drip_irrigation_electricity:0.00328947368421053,
      IrrigationType.drip_irrigation_diesel:0.00986842105263158
   },
   "ZA":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.115149401197605,
      IrrigationType.surface_irrigation_diesel:0.115149401197605,
      IrrigationType.sprinkler_irrigation_electricity:0.275466766467066,
      IrrigationType.sprinkler_irrigation_diesel:0.275466766467066,
      IrrigationType.drip_irrigation_electricity:0.109383832335329,
      IrrigationType.drip_irrigation_diesel:0.109383832335329
   }
}

# Irrigation technique shares per country (decision L44): area equipped for full control irrigation per
# technique, FAO AQUASTAT (data/aquastat_irrigation_technique_area.csv: 2020 export; BE, CH, RU from the
# ecoinvent irrigation workbook), a technique not reported counts 0; the countries marked legacy in
# data/irrigation_technique_source.csv keep the shares above. Each technique share is split between
# electricity and diesel pumps with the legacy electricity share of the country (legacy, undocumented,
# provisional; the same share for all techniques in GD_crop).
_IRRIGATION_TECHNIQUE_TYPES = {
    "surface": (IrrigationType.surface_irrigation_electricity, IrrigationType.surface_irrigation_diesel),
    "sprinkler": (IrrigationType.sprinkler_irrigation_electricity, IrrigationType.sprinkler_irrigation_diesel),
    "localized": (IrrigationType.drip_irrigation_electricity, IrrigationType.drip_irrigation_diesel),
}


def _legacy_electricity_share(country):
    legacy = _LEGACY_IRR_TECH_RATIO_PER_COUNTRY[country]
    electricity = sum(legacy[electric] for electric, _ in _IRRIGATION_TECHNIQUE_TYPES.values())
    diesel = sum(legacy[diesel] for _, diesel in _IRRIGATION_TECHNIQUE_TYPES.values())
    return electricity / (electricity + diesel)


def _irrigation_technique_shares():
    areas = {}
    for row in dataloader.rows("aquastat_irrigation_technique_area.csv"):
        areas.setdefault(row["country"], {})[row["technique"]] = float(row["area_kha"])
    shares = {}
    for row in dataloader.rows("irrigation_technique_source.csv"):
        country = row["country"]
        if row["source"] == "legacy":
            shares[country] = dict(_LEGACY_IRR_TECH_RATIO_PER_COUNTRY[country])
            continue
        if row["source"] != "aquastat":
            raise ValueError("irrigation_technique_source.csv: unknown source %r for %s" % (row["source"], country))
        total = sum(areas[country].values())
        electricity = _legacy_electricity_share(country)
        table = {irrigation_type: 0.0 for irrigation_type in IrrigationType}
        for technique, (electric, diesel) in _IRRIGATION_TECHNIQUE_TYPES.items():
            share = areas[country].get(technique, 0.0) / total
            table[electric] = share * electricity
            table[diesel] = share * (1.0 - electricity)
        shares[country] = table
    return shares


IRR_TECH_RATIO_PER_COUNTRY = _irrigation_technique_shares()

EI_IRR_RATIO_TO_AIR = {
    "BR": 0.62,
    "CA": 0.75,
    "CN": 0.51,
    "CO": 0.52,
    "FR": 0.75,
    "DE": 0.78,
    "IN": 0.51,
    "MA": 0.56,
    "PE": 0.52,
    "PH": 0.50,
    "CS": 0.74,
    "ZA": 0.71,
    "ES": 0.70,
    "US": 0.66,
    "GLO": 0.55
}

EI_IRR_RATIO_TO_RIVER = {
    "BR": 0.08,
    "CA": 0.05,
    "CN": 0.10,
    "CO": 0.10,
    "FR": 0.05,
    "DE": 0.04,
    "IN": 0.10,
    "MA": 0.09,
    "PE": 0.10,
    "PH": 0.10,
    "CS": 0.05,
    "ZA": 0.06,
    "ES": 0.06,
    "US": 0.07,
    "GLO": 0.09
}

EI_IRR_RATIO_TO_GROUNDWATER = {
    "BR": 0.30,
    "CA": 0.20,
    "CN": 0.39,
    "CO": 0.38,
    "FR": 0.20,
    "DE": 0.18,
    "IN": 0.39,
    "MA": 0.35,
    "PE": 0.38,
    "PH": 0.40,
    "CS": 0.21,
    "ZA": 0.23,
    "ES": 0.24,
    "US": 0.27,
    "GLO": 0.36
}

LAND_USE_CATEGORY_PER_CROP = {
        "almond":LandUseCategory.fruit_trees,
        "apple":LandUseCategory.fruit_trees,
        "apricot":LandUseCategory.fruit_trees,
    "asparagus_green": LandUseCategory.vegetables,
    "asparagus_white": LandUseCategory.vegetables,
        "banana":LandUseCategory.fruit_trees,
    "bellpepper": LandUseCategory.vegetables,
    "blueberry": LandUseCategory.fruit_trees,
    "cabbage_red": LandUseCategory.vegetables,
    "cabbage_white": LandUseCategory.vegetables,
        "carrot":LandUseCategory.vegetables,
    "cashew": LandUseCategory.fruit_trees,
    "cassava": LandUseCategory.arable_land,
    "castor_beans": LandUseCategory.fruit_trees,
    "chick_pea": LandUseCategory.arable_land,
    "chilli": LandUseCategory.vegetables,
        "cocoa":LandUseCategory.fruit_trees,
        "coconut":LandUseCategory.fruit_trees,
    "coffee_arabica": LandUseCategory.fruit_trees,
    "coffee_robusta": LandUseCategory.fruit_trees,
    "coriander": LandUseCategory.vegetables,
    "cotton": LandUseCategory.arable_land,
    "cranberry": LandUseCategory.fruit_trees,
    "eggplant": LandUseCategory.vegetables,
    "flax": LandUseCategory.arable_land,
    "ginger": LandUseCategory.vegetables,
    "grape": LandUseCategory.fruit_trees,
    "guar": LandUseCategory.arable_land,
    "hemp": LandUseCategory.arable_land,
    "lemon": LandUseCategory.fruit_trees,
    "citruslime": LandUseCategory.fruit_trees,
    "lentil": LandUseCategory.arable_land,
        "linseed":LandUseCategory.arable_land,
        "maizegrain":LandUseCategory.arable_land,
        "mandarin":LandUseCategory.fruit_trees,
    "mango": LandUseCategory.fruit_trees,
        "mint":LandUseCategory.vegetables,
    "mulberry": LandUseCategory.fruit_trees,
        "oat":LandUseCategory.arable_land,
        "olive":LandUseCategory.fruit_trees,
        "onion":LandUseCategory.vegetables,
    "orange_fresh": LandUseCategory.fruit_trees,
    "orange_processing": LandUseCategory.fruit_trees,
        "palmtree":LandUseCategory.fruit_trees,
        "peach":LandUseCategory.fruit_trees,
        "peanut":LandUseCategory.arable_land,
        "pear":LandUseCategory.fruit_trees,
    "pearl_millet": LandUseCategory.arable_land,
        "pineapple":LandUseCategory.arable_land,
    "pomegranate": LandUseCategory.fruit_trees,
        "potato":LandUseCategory.arable_land,
        "rapeseed":LandUseCategory.arable_land,
    "raspberry": LandUseCategory.fruit_trees,
        "rice":LandUseCategory.arable_land,
    "sesame_seed": LandUseCategory.arable_land,
        "soybean":LandUseCategory.arable_land,
    "strawberry_fresh": LandUseCategory.vegetables,
    "strawberry_processing": LandUseCategory.vegetables,
        "sugarbeet":LandUseCategory.arable_land,
        "sugarcane":LandUseCategory.arable_land,
        "sunflower":LandUseCategory.arable_land,
        "sweetcorn":LandUseCategory.arable_land,
        "tea":LandUseCategory.vegetables,
    "tomato_fresh": LandUseCategory.vegetables,
    "tomato_processing": LandUseCategory.vegetables,
    "turmeric": LandUseCategory.vegetables,
        "wheat":LandUseCategory.arable_land
        }

#from GD_crop RootingDepth_L0 and RootingDepth_L1
# Mireille&Raphaël for Bell pepper, cabbage, cassava, cotton, eggplant, flax, guar, hemp, lentil, mango, mulberry
# Chloé's file for cashew, chilli, coffee, grape, peanut, potato, pineapple, strawberry, sugar beet, sugar cane,
# tea, tomato, wheat
# Castor bean: (Comar, Tilley et al. 2004)
# Chickpea: ecocrop (FAO)
# Coriander: http://veggieharvest.com/herbs/cilantro.html // http://files.hawaii.gov/dlnr/cwrm/publishedreports/PR200808.pdf
# Ginger: http://veggieharvest.com/herbs/ginger.html
# Millet: ask Sämi
# Sesame seed: ask Sämi
# Turmenic: ask Sämi
# Pomegranate: ask Sämi
#in m
ROOTING_DEPTH_PER_CROP = {
                        "almond": 1.5,
                        "apple": 1.5,
                        "apricot": 1.5,
    "asparagus_green": 0.5,
    "asparagus_white": 0.5,
                        "banana": 1.5,
    "bellpepper": 0.6,
    "blueberry": 0.45,
    "cabbage_red": 0.25,
    "cabbage_white": 0.25,
                        "carrot": 0.5,
    "cashew": 0.5,
    "cassava": 1.5,
    "castor_beans": 1.5,
    "chick_pea": 1.5,
    "chilli": 0.8,
                        "cocoa": 2.0,
                        "coconut": 1.5,
    "coffee_arabica": 1.2,
    "coffee_robusta": 1.2,
    "coriander": 0.33,
    "cotton": 1.35,
    "cranberry": 0.9,
    "eggplant": 0.8,
    "flax": 0.5,
    "ginger": 0.275,
    "grape": 1.5,
    "guar": 0.5,
    "hemp": 0.5,
    "lemon": 1.5,
    "citruslime": 1.5,
    "lentil": 0.5,
                        "linseed": 0.9,
                        "maizegrain": 1.35,
                        "mandarin": 1.5,
    "mango": 1,
                        "mint": 0.5,
    "mulberry": 1,
                        "oat": 1.2,
                        "olive": 1.5,
                        "onion": 0.5,
    "orange_fresh": 1.5,
    "orange_processing": 1.5,
                        "palmtree": 1,
                        "peach": 1.5,
    "peanut": 0.5,
                        "pear": 1.5,
    "pearl_millet": 1.5,
                        "pineapple": 0.5,
    "pomegranate": 1.0,
    "potato": 0.3,
                        "rapeseed": 0.9,
    "raspberry": 0.9,
                        "rice": 0.6,
    "sesame_seed": 0.6,
                        "soybean": 0.95,
    "strawberry_fresh": 0.45,
    "strawberry_processing": 0.45,
    "sugarbeet": 0.9,
    "sugarcane": 1.5,
                        "sunflower": 1.35,
                        "sweetcorn": 1.35,
    "tea": 1.2,
    "tomato_fresh": 1.0,
    "tomato_processing": 1.0,
    "turmeric": 0.45,
    "wheat": 0.7
}

#src except unknown: EUROPEAN COMMISSION DIRECTORATE GENERAL JRC JOINT RESEARCH CENTRE Space Applications Institute European Soil Bureau
SOIL_ERODIBILITY_FACTOR_PER_SOIL_TEXTURE = {
                        SoilTexture.unknown:0.032,#Panagos et al. 2014
                        SoilTexture.coarse:0.0115,
                        SoilTexture.medium:0.0311,
                        SoilTexture.medium_fine:0.0438,
                        SoilTexture.fine:0.0339,
                        SoilTexture.very_fine:0.017
                        }

#From GD_crop WaterNutrient_L1 column C
#  Mireille&Raphaël for Bell pepper, cabbage, cashew, cassava, chilli, cotton, eggplant, flax, grape, guar, hemp, lentil, mango, mulberry
# Castor bean:pdf  Castor_Bean_Moisture in documentation file;http://www.cropj.com/gharibzahedi_5_1_2011_1_7.pdf
# Chickpea: http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.548.9690&rep=rep1&type=pdf (leaf water content, averaged from graph p.37): http://etd.aau.edu.et/bitstream/123456789/10830/1/Getahun%20Yemata.pdf
# Coriander: http://www.academicjournals.org/article/article1390549943_Bhat%2520et%2520al.pdf
# Ginger: http://www.fao.org/fileadmin/user_upload/inpho/docs/Post_Harvest_Compendium_-_Ginger.pdf
# Millet: ask Sämi / Pauline: http://agropedia.iitk.ac.in/content/harvesting-and-storage-pearl-millet
# Sesame seed: ask Sämi / Pauline:http://www.globalsciencebooks.info/Online/GSBOnline/images/2010/SSB_4(1)/SSB_4(1)69-72o.pdf
# Turmenic: ask Sämi / Pauline: http://www.fao.org/3/a-ax446e.pdf
# Pomegranate: ask Sämi / Pauline: http://www.ijat-aatsea.com/pdf/v7_n6_11_November/6_IJAT_2011_7_6___R._Riyahi_FX.pdf
WATER_CONTENT_FM_RATIO_PER_CROP = {
        "almond": 0.0565,
        "apple": 0.849,
        "apricot": 0.853,
    "asparagus_green": 0.92,
    "asparagus_white": 0.92,
        "banana": 0.781,
    "bellpepper": 0.88,
    "blueberry": 0.8421,
    "cabbage_red": 0.9,
    "cabbage_white": 0.9,
        "carrot": 0.882,
    "cashew": 0.05,
    "cassava": 0.6,
    "castor_beans": 0.094,
    "chick_pea": 0.09,
    "chilli": 0.88,
        "cocoa": 0.056,
        "coconut": 0.446,
    "coffee_arabica": 0.102,
    "coffee_robusta": 0.102,
    "coriander": 0.0808,
    "cotton": 0.09,
    "cranberry": 0.8732,
    "eggplant": 0.93,
    "flax": 0.11,
    "ginger": 0.12,
    "grape": 0.81,
    "guar": 0.1,
    "hemp": 0.4,
    "lemon": 0.842,
    "citruslime": 0.842,
    "lentil": 0.08,
        "linseed": 0.1,
        "maizegrain": 0.14,
        "mandarin": 0.842,
    "mango": 0.84,
        "mint": 0.681,
    "mulberry": 0.7,
        "oat": 0.15,
        "olive": 0.748,
        "onion": 0.886,
    "orange_fresh": 0.842,
    "orange_processing": 0.842,
        "palmtree": 0.47,
        "peach": 0.873,
        "peanut": 0.05968,
        "pear": 0.829,
    "pearl_millet": 0.2,
        "pineapple": 0.87,#src: web
    "pomegranate": 0.78,
        "potato": 0.78,
        "rapeseed": 0.12,
    "raspberry": 0.8575,
        "rice": 0.131,
    "sesame_seed": 0.057,
        "soybean": 0.11,
    "strawberry_fresh": 0.895,
    "strawberry_processing": 0.895,
        "sugarbeet": 0.77,
        "sugarcane": 0.774,
        "sunflower": 0.06,
        "sweetcorn": 0.72,
        "tea": 0.0764,
    "tomato_fresh": 0.942,
    "tomato_processing": 0.942,
    "turmeric": 0.12,
        "wheat": 0.15
        }


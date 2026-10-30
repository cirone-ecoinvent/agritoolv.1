"""Decision L29: default manure of the crops with a computed N uptake (L28) from the N uptake, WFLDB L1 method
(Guidelines v3.0 section 3.6.2) with FAOSTAT manure N 2021-2023 per country; manure shares per country. Since
decision L42 the N of cattle, buffalo, pigs and laying hens is split with the IPCC 2019 manure management systems."""
import importlib.util
from pathlib import Path

import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS
from defaultTables import MANURE_LIQUID_RATIO_PER_COUNTRY, MANURE_SOLID_RATIO_PER_COUNTRY, \
    MANURE_LIQUID_N_FRACTION_PER_COUNTRY
from models.manuremodel import ManureModel, LiquidManureType, SolidManureType

ROOT = Path(__file__).resolve().parents[2]


def _defaults(**inputs):
    return DefaultValuesWrapper(inputs, DEFAULTS_VALUES_GENERATORS)


def _available_n(defaults):
    """Available N (GRUDAF Nverf) of the default manure [kg N/ha]: (liquid, solid)."""
    liquid = sum(v * ManureModel._content(k, "n_available") for k, v in defaults["liquid_manure_quantities"].items())
    solid = sum(v * ManureModel._content(k, "n_available") for k, v in defaults["solid_manure_quantities"].items())
    return liquid * defaults["liquid_manure_part_before_dilution"], solid / 1000.0


@pytest.mark.parametrize("crop, country, yield_per_cycle", [
    ("wheat", "FR", 7000.0), ("rice", "IN", 4300.0), ("potato", "MA", 30000.0), ("sugarbeet", "CS", 50000.0)])
def test_available_n_of_the_default_manure_is_the_organic_share_of_the_n_uptake(crop, country, yield_per_cycle):
    defaults = _defaults(crop=crop, country=country, yield_main_product_per_crop_cycle=yield_per_cycle)
    liquid, solid = _available_n(defaults)
    organic_share = 1.0 - dataloader.param("mineral_n_share_of_n_uptake")
    assert liquid + solid == pytest.approx(organic_share * defaults["nitrogen_uptake_by_crop"])
    assert liquid / (liquid + solid) == pytest.approx(MANURE_LIQUID_N_FRACTION_PER_COUNTRY[country])


def test_default_manure_follows_the_n_uptake():
    low = _defaults(crop="wheat", country="IT", yield_main_product_per_crop_cycle=3000.0)
    high = _defaults(crop="wheat", country="IT", yield_main_product_per_crop_cycle=6000.0)
    assert high["total_manureliquid"] == pytest.approx(2.0 * low["total_manureliquid"])
    assert high["total_manuresolid"] == pytest.approx(2.0 * low["total_manuresolid"])


def test_dilution_and_manure_mix_of_the_template_keep_the_available_n():
    base = _defaults(crop="wheat", country="FR", yield_main_product_per_crop_cycle=7000.0)
    diluted = _defaults(crop="wheat", country="FR", yield_main_product_per_crop_cycle=7000.0,
                        liquid_manure_part_before_dilution=0.25)
    assert diluted["total_manureliquid"] == pytest.approx(2.0 * base["total_manureliquid"])
    pig_only = dict.fromkeys(LiquidManureType, 0.0)
    pig_only[LiquidManureType.pig] = 1.0
    pigs = _defaults(crop="wheat", country="FR", yield_main_product_per_crop_cycle=7000.0,
                     liquid_manure_proportions=pig_only)
    assert _available_n(pigs)[0] == pytest.approx(_available_n(base)[0])
    assert pigs["total_manureliquid"] != pytest.approx(base["total_manureliquid"])


def test_reviewed_country_factors():
    # review table of decision L42 (Literature/review_manure_ipcc_mms.csv): IN 0.0009 m3 and 91.7 kg solid manure
    # per kg N uptake (L29 with the WFLDB split: 0.0522 m3 and 48.0 kg); share of liquid N FR 0.427 -> 0.450
    defaults = _defaults(crop="rice", country="IN", yield_main_product_per_crop_cycle=4300.0)
    n_uptake = defaults["nitrogen_uptake_by_crop"]
    assert defaults["total_manureliquid"] / n_uptake == pytest.approx(0.00091, abs=5e-6)
    assert defaults["total_manuresolid"] / n_uptake == pytest.approx(91.69, abs=0.005)
    assert MANURE_LIQUID_N_FRACTION_PER_COUNTRY["FR"] == pytest.approx(0.4497, abs=5e-5)


def test_mulberry_gets_no_manure():
    # crops without level 1 coefficients: decisions L40 and L57, test_manure_other_crops.py
    defaults = _defaults(crop="mulberry", country="IN", yield_main_product_per_crop_cycle=9000.0)
    assert defaults["total_manureliquid"] == defaults["total_manuresolid"] == 0.0  # decisions L55, L57


def test_country_shares_cover_the_tool_countries_and_sum_to_one():
    countries = set(dataloader.table("luc_blonk_country_expansion.csv"))
    assert set(MANURE_LIQUID_RATIO_PER_COUNTRY) == set(MANURE_SOLID_RATIO_PER_COUNTRY) == countries
    for table, enum in ((MANURE_LIQUID_RATIO_PER_COUNTRY, LiquidManureType),
                        (MANURE_SOLID_RATIO_PER_COUNTRY, SolidManureType)):
        for country, shares in table.items():
            assert set(shares) == set(enum) and sum(shares.values()) == pytest.approx(1.0, abs=1e-12), country
            assert shares[enum.other] == 0.0, country


def test_liquid_n_fraction_is_the_ipcc_split_of_the_faostat_n():
    # decision L42, Western Europe rows of IPCC 2019 Tables 10A.6, 10A.7 (high productivity) and 10A.9: liquid =
    # lagoon, liquid/slurry, pits; solid = solid storage, dry lot, daily spread, poultry litter; buffalo: dairy row
    # only (no non-dairy buffalo row for Western Europe)
    liquid_share = {"Cattle, dairy": 43 / 74, "Cattle, non-dairy": 22 / 52, "Buffalo": 34 / 97,
                    "Swine, market": 85 / 100, "Swine, breeding": 84 / 100, "Chickens, layers": 44 / 100}
    n = {r["item"]: float(r["n_applied_mean_kg"])
         for r in dataloader.rows("faostat_manure_n_applied_country.csv") if r["country"] == "FR"}
    solid_only = ["Chickens, broilers", "Turkeys", "Ducks", "Horses", "Asses", "Mules and hinnies", "Sheep", "Goats"]
    liquid = {item: n.get(item, 0.0) * share for item, share in liquid_share.items()}
    total_liquid = sum(liquid.values())
    solid = sum(n.get(item, 0.0) for item in list(liquid_share) + solid_only) - total_liquid
    assert MANURE_LIQUID_N_FRACTION_PER_COUNTRY["FR"] == pytest.approx(total_liquid / (total_liquid + solid))
    # liquid volume shares = N / total N per m3 of undiluted manure, normalised
    units = {LiquidManureType.cattle: liquid["Cattle, dairy"] + liquid["Cattle, non-dairy"] + liquid["Buffalo"],
             LiquidManureType.pig: liquid["Swine, breeding"] + liquid["Swine, market"],
             LiquidManureType.laying_hens: liquid["Chickens, layers"]}
    units = {k: v / ManureModel._content(k, "n_total") for k, v in units.items()}
    for k, v in units.items():
        assert MANURE_LIQUID_RATIO_PER_COUNTRY["FR"][k] == pytest.approx(v / sum(units.values()))


def test_table_equals_the_faostat_download():
    script = ROOT / "scripts" / "build_faostat_manure_country.py"
    spec = importlib.util.spec_from_file_location("build_faostat_manure_country", script)
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    download = dataloader.EXTERNAL_DATA_DIR / build.FAOSTAT_FILE
    if not download.is_file():
        pytest.skip("FAOSTAT download not in data/external_data/")
    rebuilt = [{k: str(v) for k, v in row.items()} for row in build.build(download)]
    assert rebuilt == [dict(row) for row in dataloader.rows("faostat_manure_n_applied_country.csv")]

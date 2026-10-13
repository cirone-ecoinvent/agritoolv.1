"""Decision L29: default manure of the crops with a computed N uptake (L28) from the N uptake, WFLDB L1 method
(Guidelines v3.0 section 3.6.2) with FAOSTAT manure N 2021-2023 per country; manure shares per country."""
import importlib.util
from pathlib import Path

import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS
from defaultMatrixTotalManure import TOTAL_MANURE_LIQUID_PER_CROP_PER_COUNTRY, TOTAL_MANURE_SOLID_PER_CROP_PER_COUNTRY
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
    # review table confirmed by FC on 2026-10-13: IN 0.0522 m3 and 48.0 kg solid manure per kg N uptake
    defaults = _defaults(crop="rice", country="IN", yield_main_product_per_crop_cycle=4300.0)
    n_uptake = defaults["nitrogen_uptake_by_crop"]
    assert defaults["total_manureliquid"] / n_uptake == pytest.approx(0.0522, abs=5e-5)
    assert defaults["total_manuresolid"] / n_uptake == pytest.approx(48.0, abs=0.05)
    assert MANURE_LIQUID_N_FRACTION_PER_COUNTRY["FR"] == pytest.approx(0.427, abs=5e-4)


def test_other_crops_keep_the_legacy_matrices():
    defaults = _defaults(crop="apple", country="IT", yield_main_product_per_crop_cycle=35000.0)
    assert defaults["total_manureliquid"] == TOTAL_MANURE_LIQUID_PER_CROP_PER_COUNTRY["apple"]["IT"]
    assert defaults["total_manuresolid"] == TOTAL_MANURE_SOLID_PER_CROP_PER_COUNTRY["apple"]["IT"]


def test_country_shares_cover_the_tool_countries_and_sum_to_one():
    countries = set(dataloader.table("luc_blonk_country_expansion.csv"))
    assert set(MANURE_LIQUID_RATIO_PER_COUNTRY) == set(MANURE_SOLID_RATIO_PER_COUNTRY) == countries
    for table, enum in ((MANURE_LIQUID_RATIO_PER_COUNTRY, LiquidManureType),
                        (MANURE_SOLID_RATIO_PER_COUNTRY, SolidManureType)):
        for country, shares in table.items():
            assert set(shares) == set(enum) and sum(shares.values()) == pytest.approx(1.0, abs=1e-12), country
            assert shares[enum.other] == 0.0, country


def test_liquid_n_fraction_is_the_wfldb_split_of_the_faostat_n():
    n = {r["item"]: float(r["n_applied_mean_kg"])
         for r in dataloader.rows("faostat_manure_n_applied_country.csv") if r["country"] == "FR"}
    both_forms = ["Cattle, dairy", "Cattle, non-dairy", "Buffalo", "Swine, breeding", "Swine, market", "Chickens, layers"]
    solid_only = ["Chickens, broilers", "Turkeys", "Ducks", "Horses", "Asses", "Mules and hinnies", "Sheep", "Goats"]
    liquid = 0.5 * sum(n.get(item, 0.0) for item in both_forms)
    solid = liquid + sum(n.get(item, 0.0) for item in solid_only)
    assert MANURE_LIQUID_N_FRACTION_PER_COUNTRY["FR"] == pytest.approx(liquid / (liquid + solid))
    # liquid volume shares = N / total N per m3 of undiluted manure, normalised
    units = {LiquidManureType.cattle: 0.5 * (n["Cattle, dairy"] + n["Cattle, non-dairy"] + n.get("Buffalo", 0.0)),
             LiquidManureType.pig: 0.5 * (n["Swine, breeding"] + n["Swine, market"]),
             LiquidManureType.laying_hens: 0.5 * n["Chickens, layers"]}
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

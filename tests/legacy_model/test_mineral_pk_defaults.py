"""Decision L31: default mineral P2O5 and K2O = P2O5 (K2O) taken off the field with the main product (yield x content
of the WFLDB Background Parameters 2017 sheet 4) minus the P2O5 (K2O) of the manure in use, 0 when the manure brings
more (WFLDB Guidelines v3.0 sections 3.6.1-3.6.2). This is level 1; the default is level 2 where IFA gives a rate
(decision L33, test_ifa_level2_defaults.py)."""
import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS, \
    MineralPhosphorusPotassiumDefaultGenerator as PK
from defaultTables import PK_PER_KG_MAIN_PRODUCT_PER_CROP as PK_PER_KG
from models.manuremodel import ManureModel, LiquidManureType

NUTRIENTS = ("p2o5", "k2o")


def _defaults(**inputs):
    return DefaultValuesWrapper(inputs, DEFAULTS_VALUES_GENERATORS)


def _manure(defaults, nutrient):
    """kg P2O5 or K2O/ha of the manure in use (GRUDAF 2009 Table 39)."""
    liquid = sum(v * ManureModel._content(k, nutrient) for k, v in defaults["liquid_manure_quantities"].items())
    solid = sum(v * ManureModel._content(k, nutrient) for k, v in defaults["solid_manure_quantities"].items())
    return liquid * defaults["liquid_manure_part_before_dilution"] + solid / 1000.0


def test_crops_and_contents():
    n_uptake_crops = {r["crop"] for r in dataloader.rows("n_uptake_crop_parameters.csv")}
    pk_crops = {r["crop"] for r in dataloader.rows("pk_crop_parameters.csv")}
    assert not n_uptake_crops & pk_crops
    assert set(PK_PER_KG) == n_uptake_crops | pk_crops and len(PK_PER_KG) == 40
    assert PK_PER_KG["wheat"] == {"p2o5": pytest.approx(0.0082), "k2o": pytest.approx(0.0043)}
    assert PK_PER_KG["coffee_robusta"] == PK_PER_KG["coffee_arabica"]
    assert PK_PER_KG["citruslime"] == PK_PER_KG["lemon"]  # proxy, decision L32


@pytest.mark.parametrize("crop, country, yield_per_cycle", [
    ("wheat", "FR", 7000.0), ("potato", "IN", 25000.0), ("tomato_fresh", "IT", 70000.0), ("soybean", "BR", 3200.0),
    ("apple", "IT", 40000.0), ("tea", "KE", 2500.0)])
def test_default_mineral_pk_is_the_offtake_minus_the_manure(crop, country, yield_per_cycle):
    defaults = _defaults(crop=crop, country=country, yield_main_product_per_crop_cycle=yield_per_cycle)
    for nutrient in NUTRIENTS:
        expected = max(0.0, yield_per_cycle * PK_PER_KG[crop][nutrient] - _manure(defaults, nutrient))
        assert PK.level1(defaults, nutrient) == pytest.approx(expected)


def test_cereal_k2o_is_zero_when_the_manure_brings_more():
    defaults = _defaults(crop="wheat", country="FR", yield_main_product_per_crop_cycle=7000.0)
    assert _manure(defaults, "k2o") > 7000.0 * PK_PER_KG["wheat"]["k2o"]
    assert PK.level1(defaults, "k2o") == 0.0
    assert PK.level1(defaults, "p2o5") > 0.0


def test_the_manure_of_the_template_is_subtracted():
    # 20 m3 pig slurry, half undiluted: 10 m3 x (3.8 + 3.2) / 2 kg P2O5 and x (4.4 + 3.2) / 2 kg K2O (GRUDAF Table 39)
    pig = dict.fromkeys(LiquidManureType, 0.0)
    pig[LiquidManureType.pig] = 1.0
    defaults = _defaults(crop="potato", country="DE", yield_main_product_per_crop_cycle=40000.0,
                         total_manureliquid=20.0, liquid_manure_proportions=pig, total_manuresolid=0.0)
    assert PK.level1(defaults, "p2o5") == pytest.approx(40000.0 * 0.0013 - 35.0)
    assert PK.level1(defaults, "k2o") == pytest.approx(40000.0 * 0.0054 - 38.0)


@pytest.mark.parametrize("crop, country, yield_per_cycle, wfldb_p2o5, wfldb_k2o", [
    ("potato", "RU", 13113.0, 6, 41), ("oat", "FI", 3242.0, 9, 0), ("carrot", "IL", 64261.0, 0, 167),
    ("tomato_fresh", "MX", 30629.0, 0, 61), ("banana", "CR", 47698.0, 1, 189), ("lemon", "MX", 13783.0, 0, 10),
    ("tea", "KE", 2064.0, 0, 0), ("tea", "LK", 1440.0, 0, 0)])
def test_wfldb_l1_datasets_are_reproduced(crop, country, yield_per_cycle, wfldb_p2o5, wfldb_k2o):
    # WFLDB 3.1 Documentation 2017, Excel annex sheets 2a-2c: datasets with P and K at L1; yield of the L1
    # fertilisers (N mineral / 0.8 / N per kg for the crops of L28, else the dataset yield). The manure shares
    # are FAOSTAT 2021-2023 (L29), not WFLDB 2009-2012, and the IPCC 2019 split of the manure forms (L42), not
    # 50/50, hence the tolerance (K2O: carrot IL 161 and banana CR 180 kg, all-solid cattle manure).
    defaults = _defaults(crop=crop, country=country, yield_main_product_per_crop_cycle=yield_per_cycle)
    assert PK.level1(defaults, "p2o5") == pytest.approx(wfldb_p2o5, abs=4.0)
    assert PK.level1(defaults, "k2o") == pytest.approx(wfldb_k2o, abs=10.0)


def test_other_crops_without_ifa_rate_have_no_default():
    # other crops with an IFA rate: decision L34, test_ifa_other_crops.py
    defaults = _defaults(crop="turmeric", country="IN", yield_main_product_per_crop_cycle=20000.0)
    assert defaults["p2O5_from_mineral_fert"] == defaults["k2O_from_mineral_fert"] == 0.0

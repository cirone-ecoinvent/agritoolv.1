"""Decision L28: default N uptake = yield per crop cycle x N per kg of main product incl. residues (WFLDB
Background Parameters 2017 sheet 4, residue ratio from GRUDAF 2009 Tab. 1), default mineral N = 0.8 x N uptake."""
import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS
from defaultTables import N_UPTAKE_PER_KG_MAIN_PRODUCT_PER_CROP as N_PER_KG


def _defaults(**inputs):
    return DefaultValuesWrapper(inputs, DEFAULTS_VALUES_GENERATORS)


def test_wheat_reproduces_grudaf_table1():
    # Winterweizen: 60 dt grain with 121 kg N, 70 dt straw with 22 kg N; WFLDB sheet 4: 20.2 and 3.1 g N/kg FM
    assert N_PER_KG["wheat"] == pytest.approx((20.2 + 70.0 / 60.0 * 3.1) / 1000.0)
    assert 6000.0 * N_PER_KG["wheat"] == pytest.approx(121 + 22, abs=1.0)


def test_n_uptake_and_mineral_n_follow_the_yield_of_the_crop_cycle():
    defaults = _defaults(crop="wheat", country="IT", yield_main_product_per_crop_cycle=6500.0)
    assert defaults["nitrogen_uptake_by_crop"] == pytest.approx(6.5 * (20.2 + 70.0 / 60.0 * 3.1))
    assert defaults["nitrogen_from_mineral_fert"] == pytest.approx(0.8 * defaults["nitrogen_uptake_by_crop"])


def test_crop_without_residue_n_uses_the_main_product_only():
    assert N_PER_KG["sugarcane"] == pytest.approx(1.779072 / 1000.0)


def test_legacy_residue_ratio_is_tagged():
    rows = {r["crop"]: r for r in dataloader.rows("n_uptake_crop_parameters.csv")}
    for crop in ("rice", "tomato_fresh", "banana"):
        assert rows[crop]["residue_ratio"] and rows[crop]["note"].endswith("legacy, undocumented, provisional")
    assert N_PER_KG["rice"] == pytest.approx((12.5 + 1.0 * 6.23616) / 1000.0)


def test_parameters_cover_known_crops_and_are_signed():
    crops = dataloader.table("crop_types.csv", numeric=False)
    contents = dataloader.table("wfldb2017_crop_nutrient_contents.csv")
    for row in dataloader.rows("n_uptake_crop_parameters.csv"):
        assert row["crop"] in crops and row["wfldb_crop"] in contents, row
        assert row["status"] == "confirmed" and row["reviewed_by"], row


def test_other_crops_keep_the_legacy_matrices():
    defaults = _defaults(crop="blueberry", country="US", yield_main_product_per_crop_cycle=9000.0)
    assert "blueberry" not in N_PER_KG
    assert defaults["nitrogen_uptake_by_crop"] == pytest.approx(11.3787048)  # legacy US
    assert defaults["nitrogen_from_mineral_fert"] == pytest.approx(87.0)

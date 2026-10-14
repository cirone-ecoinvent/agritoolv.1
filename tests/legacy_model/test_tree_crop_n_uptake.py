"""Decision L32: default N uptake of the tree crops = yield per crop cycle x N of the main product + N of a fixed amount
of residues per ha (tree_crop_residues_kg_fm_per_ha x N of haulm or stem, WFLDB Background Parameters 2017 sheet 4);
the default mineral N (L28), manure (L29) and mineral P and K (L31) follow from it."""
import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS
from defaultMatrixNUptake import NITROGEN_UPTAKE_PER_CROP_PER_COUNTRY as LEGACY_N_UPTAKE
from defaultMatrixTotalManure import TOTAL_MANURE_LIQUID_PER_CROP_PER_COUNTRY, TOTAL_MANURE_SOLID_PER_CROP_PER_COUNTRY
from defaultTables import N_UPTAKE_PER_KG_MAIN_PRODUCT_PER_CROP as N_PER_KG, N_UPTAKE_OF_TREE_RESIDUES_PER_CROP as TREE_N
from models.manuremodel import ManureModel

TREES = {"almond", "apple", "apricot", "citruslime", "cocoa", "coconut", "coffee_arabica", "coffee_robusta", "lemon",
         "mandarin", "olive", "orange_fresh", "orange_processing", "peach", "pear", "tea"}


def _defaults(**inputs):
    return DefaultValuesWrapper(inputs, DEFAULTS_VALUES_GENERATORS)


def _available_n(defaults):
    """Available N (GRUDAF Nverf) of the default manure [kg N/ha]."""
    liquid = sum(v * ManureModel._content(k, "n_available") for k, v in defaults["liquid_manure_quantities"].items())
    solid = sum(v * ManureModel._content(k, "n_available") for k, v in defaults["solid_manure_quantities"].items())
    return liquid * defaults["liquid_manure_part_before_dilution"] + solid / 1000.0


def test_tree_crops_and_residue_n():
    assert set(TREE_N) == TREES and TREES <= set(N_PER_KG)
    for crop in TREES:
        assert TREE_N[crop] == pytest.approx(18.6)  # 6000 kg FM x 3.1 g N/kg FM
    assert N_PER_KG["almond"] == pytest.approx(20.3694 / 1000.0)  # main product only
    assert N_PER_KG["citruslime"] == N_PER_KG["lemon"]
    residues = {r["name"]: r for r in dataloader.rows("model_parameters.csv")}["tree_crop_residues_kg_fm_per_ha"]
    assert residues["source"].endswith("legacy, undocumented, provisional")  # amount not stated in the WFLDB reports


def test_n_uptake_mineral_n_and_manure_follow_the_yield():
    defaults = _defaults(crop="apple", country="IT", yield_main_product_per_crop_cycle=40000.0)
    assert defaults["nitrogen_uptake_by_crop"] == pytest.approx(40000.0 * 0.5 / 1000.0 + 18.6)
    assert defaults["nitrogen_from_mineral_fert"] == pytest.approx(0.8 * defaults["nitrogen_uptake_by_crop"])
    assert _available_n(defaults) == pytest.approx(0.2 * defaults["nitrogen_uptake_by_crop"])


@pytest.mark.parametrize("crop, country, wfldb_yield", [
    ("apple", "CL", 43328), ("cocoa", "CI", 613), ("cocoa", "GH", 457), ("coconut", "ID", 6116), ("coconut", "PH", 4415),
    ("lemon", "MX", 13783), ("tea", "KE", 2064), ("tea", "LK", 1440)])
def test_legacy_matrix_is_the_same_rule(crop, country, wfldb_yield):
    # GD_crop Nuptake_L1 at the yields marked L1 in the WFLDB 3.1 Documentation 2017, Excel annex sheet 2c (rounded)
    defaults = _defaults(crop=crop, country=country, yield_main_product_per_crop_cycle=float(wfldb_yield))
    assert defaults["nitrogen_uptake_by_crop"] == pytest.approx(LEGACY_N_UPTAKE[crop][country], abs=0.03)


@pytest.mark.parametrize("crop, country, wfldb_yield, wfldb_n_mineral", [
    ("coconut", "PH", 4415, 44), ("lemon", "MX", 13783, 33), ("tea", "KE", 2064, 82), ("tea", "LK", 1440, 62)])
def test_wfldb_l1_datasets_are_reproduced(crop, country, wfldb_yield, wfldb_n_mineral):
    # WFLDB 3.1 Documentation 2017, Excel annex sheet 2c: datasets with yield and N mineral at L1
    defaults = _defaults(crop=crop, country=country, yield_main_product_per_crop_cycle=float(wfldb_yield))
    assert defaults["nitrogen_from_mineral_fert"] == pytest.approx(wfldb_n_mineral, abs=1.0)


def test_berries_and_crops_without_fertiliser_defaults_keep_the_legacy_matrices():
    blueberry = _defaults(crop="blueberry", country="US", yield_main_product_per_crop_cycle=9000.0)
    assert blueberry["total_manureliquid"] == TOTAL_MANURE_LIQUID_PER_CROP_PER_COUNTRY["blueberry"]["US"]
    assert blueberry["total_manuresolid"] == TOTAL_MANURE_SOLID_PER_CROP_PER_COUNTRY["blueberry"]["US"]
    grape = _defaults(crop="grape", country="FR", yield_main_product_per_crop_cycle=9000.0)
    assert grape["nitrogen_uptake_by_crop"] == pytest.approx(30.0)
    assert grape["nitrogen_from_mineral_fert"] == grape["total_manureliquid"] == grape["total_manuresolid"] == 0.0


def test_tree_rows_are_signed():
    rows = [r for r in dataloader.rows("n_uptake_crop_parameters.csv") if r["tree_residues"] == "yes"]
    assert {r["crop"] for r in rows} == TREES
    for row in rows:
        assert not row["grudaf_crop"] and not row["residue_ratio"], row
        assert row["status"] == "confirmed" and row["reviewed_by"], row

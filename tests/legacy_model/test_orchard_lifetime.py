"""Decision L50: default orchard lifetime per crop and country from the ecoinvent 3.12 datasets
(data/ecoinvent312_orchard_lifetime.csv, built by scripts/build_orchard_lifetime.py; crops in
data/orchard_lifetime_crop_mapping.csv) or set by FC."""
import importlib.util
import os
from pathlib import Path

import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS
from defaultMatrixSeed import NB_PLANTED_TREES_PER_PARTIAL_CROP_PER_COUNTRY

ROOT = Path(__file__).resolve().parents[2]
MAPPING = {row["crop"]: row for row in dataloader.rows("orchard_lifetime_crop_mapping.csv")}
CROP_TYPES = dataloader.table("crop_types.csv", numeric=False)
PLANTING_RATES = dataloader.rows("ecoinvent312_planting_rates.csv")


def _lifetime(crop, country):
    return DefaultValuesWrapper(dict(crop=crop, country=country), DEFAULTS_VALUES_GENERATORS)["orchard_lifetime"]


def test_mapping_covers_exactly_the_amortised_crops():
    amortised = {crop for crop, row in CROP_TYPES.items() if row["planting_amortised_over_lifetime"] == "yes"}
    assert set(MAPPING) == amortised
    assert all(row["status"] == "confirmed" and row["reviewed_by"] == "FC" for row in MAPPING.values())


@pytest.mark.parametrize("crop, country, years", [
    ("apple", "FR", 20), ("apple", "CH", 15), ("pear", "CH", 15), ("grape", "CH", 25), ("grape", "IN", 20),
    ("grape", "FR", 25), ("cocoa", "CI", 50), ("cocoa", "BR", 50), ("coconut", "PH", 60), ("mandarin", "ZA", 25),
    ("orange_fresh", "ZA", 33), ("asparagus_white", "FR", 9), ("asparagus_green", "DE", 9), ("tea", "IN", 20),
    ("sugarcane", "BR", 5), ("sugarcane", "IN", 5), ("cashew", "IN", 25), ("pineapple", "CR", 2),
    ("blueberry", "US", 25), ("cranberry", "US", 20), ("raspberry", "RS", 8), ("mulberry", "IN", 20),
])
def test_default_lifetime(crop, country, years):
    assert _lifetime(crop, country) == years


def test_other_crops_have_no_orchard_lifetime():
    # decision L51: the greenhouse no longer reads the orchard lifetime, so annual crops need none
    for crop in ("wheat", "tomato_fresh"):
        with pytest.raises(KeyError, match="orchard_lifetime_crop_mapping.csv"):
            _lifetime(crop, "FR")


def test_template_lifetime_is_kept():
    wrapper = DefaultValuesWrapper(dict(crop="cocoa", country="CI", orchard_lifetime=25.0), DEFAULTS_VALUES_GENERATORS)
    assert wrapper["orchard_lifetime"] == 25.0


def test_datasets_made_with_this_tool_are_not_used():
    rows = dataloader.rows("ecoinvent312_orchard_lifetime.csv")
    assert [(r["activity_name"], r["geography"]) for r in rows if r["made_with_this_tool"] == "yes"] == \
        [("tea production, dried", "IN-HP")]


def test_trees_planted_match_the_ecoinvent_transformation():
    # with the dataset lifetime, the default trees per ha planted equal the ecoinvent plantings per ha and crop cycle
    cocoa_ci = [r for r in PLANTING_RATES if r["activity_name"] == "cocoa bean production, sun-dried"
                and r["geography"] == "CI"][0]
    trees = NB_PLANTED_TREES_PER_PARTIAL_CROP_PER_COUNTRY["cocoa"]["CI"] * _lifetime("cocoa", "CI")
    assert trees == pytest.approx(float(cocoa_ci["per_ha_and_crop_cycle"]), rel=0.01)


@pytest.mark.skipif(not (dataloader.EXTERNAL_DATA_DIR / "exchanges (3.12, undef).xlsx").exists()
                    or not os.environ.get("AGRITOOL_SLOW_TESTS"),
                    reason="ecoinvent release file not available or slow tests not requested")
def test_table_is_rebuilt_from_the_release_file():
    spec = importlib.util.spec_from_file_location("build", ROOT / "scripts" / "build_orchard_lifetime.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = module.build(dataloader.EXTERNAL_DATA_DIR / "exchanges (3.12, undef).xlsx")
    stored = dataloader.rows("ecoinvent312_orchard_lifetime.csv")
    assert [(r["activity_name"], r["geography"], float(r["lifetime_years"]), r["made_with_this_tool"]) for r in rows] \
        == [(r["activity_name"], r["geography"], float(r["lifetime_years"]), r["made_with_this_tool"]) for r in stored]

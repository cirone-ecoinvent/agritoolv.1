"""Decision L47: default seedlings and trees per ha from the ecoinvent 3.12 datasets (data/ecoinvent312_planting_rates.csv,
built by scripts/build_ecoinvent_planting_rates.py; crops in data/ecoinvent312_planting_crop_mapping.csv); plantings
amortised over the plantation lifetime are the yearly rate x the orchard lifetime."""
import importlib.util
import os
import statistics
from pathlib import Path

import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS, TREE_BASED_CROPS, \
    SEEDLINGS_BASED_CROPS
from defaultMatrixSeed import NB_SEEDLINGS_PER_PARTIAL_CROP_PER_COUNTRY, NB_PLANTED_TREES_PER_PARTIAL_CROP_PER_COUNTRY, \
    _LEGACY_SEEDLINGS, _LEGACY_TREES

ROOT = Path(__file__).resolve().parents[2]
MAPPING = {row["crop"]: row for row in dataloader.rows("ecoinvent312_planting_crop_mapping.csv")}
RATES = dataloader.rows("ecoinvent312_planting_rates.csv")
CROP_TYPES = dataloader.table("crop_types.csv", numeric=False)


def _build_module():
    spec = importlib.util.spec_from_file_location("build", ROOT / "scripts" / "build_ecoinvent_planting_rates.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rates(activity, geography, quantity):
    return [float(row[quantity]) for row in RATES if row["activity_name"] == activity and row["geography"] == geography]


def _defaults(crop, country, **inputs):
    return DefaultValuesWrapper(dict(crop=crop, country=country, **inputs), DEFAULTS_VALUES_GENERATORS)


def test_mapping_covers_the_tree_and_seedling_crops():
    assert {crop for crop, row in MAPPING.items() if row["template_field"] == "nb_planted_trees"} == \
        set(TREE_BASED_CROPS)
    assert {crop for crop, row in MAPPING.items() if row["template_field"] == "nb_seedlings"} == \
        set(SEEDLINGS_BASED_CROPS)
    assert {crop for crop, row in MAPPING.items() if row["use"] == "legacy"} == set(_LEGACY_SEEDLINGS) | set(_LEGACY_TREES)
    assert {crop for crop, row in MAPPING.items() if row["use"] == "proxy"} == \
        {"citruslime", "asparagus_green", "cabbage_red"}


def test_amortised_plantings_and_mint_use_the_yearly_rate():
    for crop, row in MAPPING.items():
        if row["use"] == "legacy":
            continue
        amortised = CROP_TYPES[crop]["planting_amortised_over_lifetime"] == "yes"
        expected = "per_ha_and_year" if amortised or crop == "mint" else "per_ha_and_crop_cycle"
        assert row["quantity"] == expected, crop


def test_every_mapped_activity_has_datasets_and_consistent_rates():
    activities = {row["activity_name"] for row in RATES}
    for row in MAPPING.values():
        for activity in filter(None, row["ecoinvent_activities"].split("|")):
            assert activity in activities, activity
    for row in RATES:
        assert float(row["per_ha_and_crop_cycle"]) / float(row["per_ha_and_year"]) == \
            pytest.approx(float(row["lifetime_years"]), rel=1e-3)


def test_country_values_are_means_of_the_country_and_regional_datasets():
    trees, seedlings = NB_PLANTED_TREES_PER_PARTIAL_CROP_PER_COUNTRY, NB_SEEDLINGS_PER_PARTIAL_CROP_PER_COUNTRY
    apple_ch = [x for name in MAPPING["apple"]["ecoinvent_activities"].split("|")[1:]
                for x in _rates(name, "CH", "per_ha_and_year")]
    assert len(apple_ch) == 5 and trees["apple"]["CH"] == pytest.approx(statistics.mean(apple_ch))
    coffee_br = [x for name in MAPPING["coffee_arabica"]["ecoinvent_activities"].split("|")
                 for geography in ("BR-SP", "BR-MG") for x in _rates(name, geography, "per_ha_and_year")]
    assert len(coffee_br) == 6 and trees["coffee_arabica"]["BR"] == pytest.approx(statistics.mean(coffee_br))
    assert "HN" not in trees["coffee_arabica"]
    assert trees["tea"]["IN"] == pytest.approx(_rates("tea production, dried", "IN-HP", "per_ha_and_year")[0])
    tomato_row = [x for name in MAPPING["tomato_fresh"]["ecoinvent_activities"].split("|")
                  for x in _rates(name, "RoW", "per_ha_and_crop_cycle")]
    assert len(tomato_row) == 3 and seedlings["tomato_fresh"]["GLO"] == pytest.approx(statistics.mean(tomato_row))


def test_glo_without_row_dataset_is_the_mean_of_the_countries():
    # grape: RoW has no planting input in ecoinvent 3.12; IN has one dataset, CH six
    grape = NB_PLANTED_TREES_PER_PARTIAL_CROP_PER_COUNTRY["grape"]
    assert grape["GLO"] == pytest.approx((grape["IN"] + grape["CH"]) / 2)
    assert NB_PLANTED_TREES_PER_PARTIAL_CROP_PER_COUNTRY["palmtree"]["GLO"] == \
        NB_PLANTED_TREES_PER_PARTIAL_CROP_PER_COUNTRY["palmtree"]["ID"]


def test_trees_planted_are_the_yearly_rate_times_the_orchard_lifetime():
    apple_row = _rates("apple production", "RoW", "per_ha_and_year")[0]
    assert apple_row == pytest.approx(129.053)
    defaults = _defaults("apple", "FR")
    assert defaults["orchard_lifetime"] == 20
    assert defaults["seed_quantities"] == {"apple": pytest.approx(apple_row * 20)}
    # the yearly planting (number / orchard lifetime) is the ecoinvent rate also with another lifetime
    cocoa_ci = _rates("cocoa bean production, sun-dried", "CI", "per_ha_and_year")[0]
    defaults = _defaults("cocoa", "CI", orchard_lifetime=50.0)
    assert defaults["nb_planted_trees"] / defaults["orchard_lifetime"] == pytest.approx(cocoa_ci)
    asparagus = _rates("white asparagus production", "FR", "per_ha_and_year")[0]
    assert _defaults("asparagus_white", "FR")["nb_seedlings"] == pytest.approx(asparagus * 20)
    assert _defaults("asparagus_green", "FR")["nb_seedlings"] == pytest.approx(asparagus * 20)


def test_onion_india_is_excluded_and_takes_glo():
    # ecoinvent onion IN: 3.30189 seedlings per ha, the legacy default of this tool (excluded by FC)
    assert _rates("onion production", "IN", "per_ha_and_crop_cycle") == [pytest.approx(3.30189)]
    assert MAPPING["onion"]["excluded_geographies"] == "IN"
    onion = NB_SEEDLINGS_PER_PARTIAL_CROP_PER_COUNTRY["onion"]
    assert "IN" not in onion and onion["GLO"] == pytest.approx(_rates("onion production", "RoW", "per_ha_and_crop_cycle")[0])
    assert _defaults("onion", "IN")["nb_seedlings"] == onion["GLO"]
    assert {crop for crop, row in MAPPING.items() if row["excluded_geographies"]} == {"onion"}


def test_annual_seedlings_are_per_ha_and_crop_cycle():
    assert _defaults("onion", "CN")["seed_quantities"] == {"onion": pytest.approx(443560.0)}
    assert _defaults("tomato_fresh", "NL")["nb_seedlings"] == \
        pytest.approx(_rates("tomato production, fresh grade, in heated greenhouse", "NL", "per_ha_and_crop_cycle")[0])
    assert _defaults("mint", "IN")["nb_seedlings"] == \
        pytest.approx(_rates("mint production", "IN", "per_ha_and_year")[0])
    assert _defaults("strawberry_processing", "ES")["nb_seedlings"] == \
        _defaults("strawberry_fresh", "ES")["nb_seedlings"]


def test_legacy_crops_keep_the_legacy_values():
    for crop, country in (("blueberry", "US"), ("pineapple", "CR"), ("sugarcane", "BR"), ("raspberry", "CS"),
                          ("chilli", "IN"), ("ginger", "IN")):
        assert _defaults(crop, country)["seed_quantities"] == {crop: 0.0}


@pytest.mark.skipif(not os.environ.get("AGRITOOL_SLOW_TESTS"), reason="about 60 s; set AGRITOOL_SLOW_TESTS=1")
def test_planting_table_equals_the_ecoinvent_exchanges():
    build = _build_module()
    source = dataloader.EXTERNAL_DATA_DIR / build.EXCHANGES_FILE
    if not source.is_file():
        pytest.skip("ecoinvent 3.12 exchanges file not in data/external_data/")
    rebuilt, _ = build.build(source)
    assert [{key: str(value) for key, value in row.items()} for row in rebuilt] == \
        [dict(row) for row in RATES]

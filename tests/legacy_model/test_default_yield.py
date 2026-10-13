"""Decisions L23-L24: default yield per crop cycle and country from FAOSTAT (mean 2021-2024,
GLO = World), used when the template gives no yield."""
import statistics

import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS
from defaultMatrixYieldPerCropCycle import YIELD_PER_CROP_CYCLE_PER_CROP_PER_COUNTRY as YIELDS


def _default(field, **inputs):
    return DefaultValuesWrapper(inputs, DEFAULTS_VALUES_GENERATORS)[field]


def test_every_crop_has_a_glo_yield_and_only_tool_countries():
    crops = dataloader.table("crop_types.csv", numeric=False)
    countries = {r["country"] for r in dataloader.rows("faostat_country_mapping.csv")}
    assert set(YIELDS) == set(crops)
    for crop, table in YIELDS.items():
        assert "GLO" in table, crop
        assert set(table) <= countries, crop


def test_mappings_cover_all_crops_and_are_confirmed():
    crops = dataloader.table("crop_types.csv", numeric=False)
    mapping = dataloader.rows("faostat_crop_item_mapping.csv")
    assert {r["crop"] for r in mapping} == set(crops)
    for row in mapping + dataloader.rows("faostat_country_mapping.csv"):
        assert row["status"] == "confirmed" and row["reviewed_by"], row
        if row.get("match") == "none":
            assert row["faostat_item_code"] == "", row


@pytest.mark.parametrize("crop, country, faostat_values", [
    # FAOSTAT QCL, element Yield (kg/ha), 2021-2024
    ("wheat", "FR", [6928.4, 6996.7, 7201.6, 5973.5]),
    ("rice", "IN", [4203.3, 4238.8, 4313.5, 4313.2]),
    ("coffee_arabica", "GLO", [866.4, 885.9, 911.7, 904.4]),
])
def test_yield_is_the_mean_of_the_latest_four_faostat_years(crop, country, faostat_values):
    assert YIELDS[crop][country] == pytest.approx(statistics.mean(faostat_values), abs=1e-3)


def test_tea_is_made_tea_from_green_leaf():
    # FAOSTAT 'Tea leaves' World 2021-2024; 4.5 kg green leaf per kg made tea (Thevathasan & Thevadasan 1987)
    assert YIELDS["tea"]["GLO"] == pytest.approx(statistics.mean([6664.0, 5766.1, 5925.7, 5911.0]) / 4.5, abs=1e-3)


def test_flax_glo_is_world_production_over_area():
    # FAOSTAT reports no World yield for 'Flax, raw or retted': production (t) / area harvested (ha)
    production = [897882.04, 875994.92, 708536.0, 1293266.0]
    area = [240861.0, 256741.0, 249984.0, 281974.0]
    expected = statistics.mean(1000.0 * p / a for p, a in zip(production, area))
    assert YIELDS["flax"]["GLO"] == pytest.approx(expected, abs=1e-3)


@pytest.mark.parametrize("crop", ["guar", "mulberry", "pomegranate"])
def test_crops_without_faostat_item_keep_no_default_yield(crop):
    assert YIELDS[crop] == {"GLO": 0.0}


def test_empty_template_yield_uses_the_faostat_yield_per_crop_cycle():
    # FAOSTAT yield is per area harvested: two harvests a year do not halve it (decision L24)
    inputs = dict(crop="rice", country="IN", crop_cycle_per_year=2.0)
    assert _default("yield_main_product_per_crop_cycle", **inputs) == pytest.approx(4267.2)
    assert _default("yield_main_product_per_year", **inputs) == pytest.approx(4267.2 * 2.0)
    assert _default("yield_main_product_per_crop_cycle", crop="wheat", country="FR") == YIELDS["wheat"]["FR"]


def test_country_without_faostat_value_falls_back_to_glo():
    assert "CH" not in YIELDS["cocoa"]
    assert _default("yield_main_product_per_crop_cycle", crop="cocoa", country="CH") == YIELDS["cocoa"]["GLO"]

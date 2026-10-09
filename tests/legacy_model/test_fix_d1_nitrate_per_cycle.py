"""Decision D1: SQCB-NO3 regression applied per crop cycle.

Intercept and soil-N term scaled by the occupation period t = 1 / crop_cycle_per_year; water on an
annual basis; S and U as cycle totals. Reference: reference_models.nitrate_leaching.
"""
import pytest

from models.nmodel import NModel

BASE_INPUTS = {
    "crop": "wheat", "soc_change_kg_c": 0.0, "luc_from_forest_or_grassland": "no",
    "ammonia_due_to_manure": 0.0, "ammonia_due_to_mineral_fert": 0.0,
    "ammonia_due_to_other_orga_fert": 0.0, "bulk_density_of_soil": 1300.0,
    "c_per_n_ratio": 11.0, "clay_content": 0.30108, "considered_soil_volume": 5000.0,
    "drained_part": 0.0, "nitrogen_from_all_manure": 0.0, "nitrogen_from_crop_residues": 0.0,
    "nitrogen_from_mineral_fert": 0.0, "nitrogen_from_other_orga_fert": 0.0,
    "soluble_nitrogen_from_organic_fert": 0.0,
    "nitrogen_uptake_by_crop": 150.0, "norg_per_ntotal_ratio": 0.85,
    "organic_carbon_content": 0.011, "average_annual_precipitation": 800.0,
    "crop_cycle_per_year": 1.0, "rooting_depth": 0.7, "water_use_total": 0.0,
}


def _model(**overrides):
    inputs = dict(BASE_INPUTS)
    inputs.update(overrides)
    return NModel(inputs)


def _leaching(model, s=131.5):
    norg = model._compute_nitrogen_in_soil_orga_matter(model._compute_carbon_in_soil_orga_matter())
    return model._compute_nitrogen_leaching(s, norg)


def test_annual_case_matches_reference():
    assert _leaching(_model()) == pytest.approx(31.831482, rel=1e-6)


def test_half_year_cycle_matches_reference():
    # reference: duration_yr = 0.5 -> 14.844360 kg N
    assert _leaching(_model(crop_cycle_per_year=2.0)) == pytest.approx(14.844360, rel=1e-6)


def test_irrigation_of_the_cycle_is_annualised():
    # 2000 m3/ha in a half-year cycle = 200 mm per cycle = 400 mm/yr added to P
    model = _model(crop_cycle_per_year=2.0, water_use_total=2000.0)
    assert model._compute_annual_water_in_mm() == pytest.approx(800.0 + 400.0)


def test_negative_regression_is_clamped_to_zero():
    assert _leaching(_model(nitrogen_uptake_by_crop=1e6)) == 0.0

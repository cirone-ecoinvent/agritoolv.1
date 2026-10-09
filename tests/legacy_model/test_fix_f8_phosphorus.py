"""Fix F8: phosphorus (Prasuhn 2006 / SALCAfieldP 2023): drainage factor 6 on the drained share
only, run-off zero for known slopes <= 3 %, all parameters from CSV files.
Reference: reference_models.phosphate_leaching / phosphate_runoff / phosphorus_erosion."""
import pytest

from models.atomicmass import P_TO_PO4_FACTOR
from models.pmodel import LandUseCategory, PModel

BASE_INPUTS = {
    "crop_cycle_per_year": 1.0, "drained_part": 0.0, "eroded_soil": 0.0,
    "land_use_category": LandUseCategory.arable_land, "known_slope_pct": None,
    "p2o5_in_liquid_manure": 0.0, "p2o5_in_liquid_sludge": 0.0, "p2O5_from_mineral_fert": 0.0,
    "p2o5_in_solid_manure": 0.0,
}


def _model(**overrides):
    inputs = dict(BASE_INPUTS)
    inputs.update(overrides)
    return PModel(inputs)


def test_leaching_reference_case():
    # 40 kg P2O5 slurry, arable: 0.07 * (1 + 0.2/80*40) = 0.077 kg P -> 0.236094 kg PO4
    out = _model(p2o5_in_liquid_manure=40.0).compute()
    assert out["m_P_PO4_groundwater"] == pytest.approx(0.236094, rel=1e-4)
    assert out["m_P_PO4_surfacewater_drained"] == 0.0


def test_drainage_factor_6_applies_to_the_drained_share_only():
    out = _model(p2o5_in_liquid_manure=40.0, drained_part=0.25).compute()
    assert out["m_P_PO4_groundwater"] == pytest.approx(0.236094 * 0.75, rel=1e-4)
    assert out["m_P_PO4_surfacewater_drained"] == pytest.approx(0.236094 * 6 * 0.25, rel=1e-4)


def test_runoff_base_and_slope_threshold():
    base = _model().compute()["m_P_PO4_surfacewater_ro"]
    assert base == pytest.approx(0.175 * P_TO_PO4_FACTOR, rel=1e-6)
    assert _model(known_slope_pct=2.0).compute()["m_P_PO4_surfacewater_ro"] == 0.0
    assert _model(known_slope_pct=3.0).compute()["m_P_PO4_surfacewater_ro"] == 0.0
    assert _model(known_slope_pct=5.0).compute()["m_P_PO4_surfacewater_ro"] == pytest.approx(base)


def test_runoff_fertilisation_correction():
    out = _model(p2O5_from_mineral_fert=80.0, p2o5_in_liquid_manure=80.0,
                 p2o5_in_solid_manure=80.0).compute()
    f_ro = 1 + 0.2 + 0.7 + 0.4
    assert out["m_P_PO4_surfacewater_ro"] == pytest.approx(0.175 * f_ro * P_TO_PO4_FACTOR, rel=1e-6)


def test_erosion_reference_case():
    # 10 t soil: 10000 * 0.00095 * 1.86 * 0.2 = 3.534 kg P
    assert _model(eroded_soil=10_000.0).compute()["m_P_P_surfacewater_erosion"] == pytest.approx(3.534, rel=1e-6)


def test_occupation_period_scales_yearly_averages():
    half = _model(crop_cycle_per_year=2.0).compute()
    full = _model().compute()
    assert half["m_P_PO4_groundwater"] == pytest.approx(full["m_P_PO4_groundwater"] / 2)
    assert half["m_P_PO4_surfacewater_ro"] == pytest.approx(full["m_P_PO4_surfacewater_ro"] / 2)


def test_legacy_only_land_use_classes_still_available():
    out = _model(land_use_category=LandUseCategory.fruit_trees).compute()
    assert out["m_P_PO4_groundwater"] == pytest.approx(0.06 * P_TO_PO4_FACTOR, rel=1e-6)

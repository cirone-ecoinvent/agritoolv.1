"""Fix F1: NOx = 0.04 kg NO2 per kg N applied net of NH3-N (EEA 2016 3.D Tab. 3-1)."""
import pytest

from models.atomicmass import NH3_TO_N_FACTOR, N_TO_NO2_FACTOR
from models.nmodel import NModel

BASE_INPUTS = {
    "crop": "wheat", "soc_change_kg_c": 0.0, "luc_from_forest_or_grassland": "no",
    "ammonia_due_to_manure": 0.0, "ammonia_due_to_mineral_fert": 0.0,
    "ammonia_due_to_other_orga_fert": 0.0, "bulk_density_of_soil": 1300.0,
    "c_per_n_ratio": 11.0, "clay_content": 0.2, "considered_soil_volume": 5000.0,
    "drained_part": 0.0, "nitrogen_from_all_manure": 0.0, "nitrogen_from_crop_residues": 0.0,
    "nitrogen_from_mineral_fert": 0.0, "nitrogen_from_other_orga_fert": 0.0,
    "nitrogen_uptake_by_crop": 100.0, "norg_per_ntotal_ratio": 0.85,
    "soluble_nitrogen_from_organic_fert": 0.0,
    "organic_carbon_content": 0.011, "average_annual_precipitation": 800.0, "crop_cycle_per_year": 1.0,
    "rooting_depth": 0.7, "water_use_total": 0.0,
}


def _model(**overrides):
    inputs = dict(BASE_INPUTS)
    inputs.update(overrides)
    return NModel(inputs)


def test_nox_matches_reference_case():
    # reference_models.nox(100, 10) == 3.670588 with 17/14 and 46/14; the model layer uses
    # exact atomic masses, hence the 1e-3 tolerance.
    model = _model(nitrogen_from_mineral_fert=100.0, ammonia_due_to_mineral_fert=10.0)
    nox = model._compute_nox_as_no2(100.0, 10.0)
    assert nox == pytest.approx(3.670588, rel=1e-3)
    expected = 0.012173913 * (100.0 - 10.0 * NH3_TO_N_FACTOR) * N_TO_NO2_FACTOR
    assert nox == pytest.approx(expected, rel=1e-9)


def test_nox_is_0_04_kg_no2_per_kg_net_n():
    # 0.012173913 kg NOx-N/kg N x 46/14 = 0.04 kg NO2/kg N (exact atomic masses: 3.9985)
    assert _model()._compute_nox_as_no2(100.0, 0.0) == pytest.approx(4.0, rel=1e-3)


def test_nox_never_negative_when_nh3_exceeds_n_applied():
    assert _model()._compute_nox_as_no2(1.0, 10.0) == 0.0


def test_nox_flows_into_compute_output():
    out = _model(nitrogen_from_mineral_fert=100.0, ammonia_due_to_mineral_fert=10.0).compute()
    assert out["m_N_Nox_as_n2o_air"] == pytest.approx(3.670588, rel=1e-3)

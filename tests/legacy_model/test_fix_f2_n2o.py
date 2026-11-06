"""Fix F2: N2O = IPCC Eq. 11.1 + 11.9 + 11.10 with N_som, EF1FR for flooded rice on the direct term only,
volatilised N only in the indirect term. Factors of the IPCC 2019 Refinement by wet and dry climate since decision
L64 (test_ipcc2019_n2o.py); the reference_models.n2o case of the fix used the IPCC 2006 factors."""
import pytest

from models.atomicmass import N_TO_N2O_FACTOR, N_TO_NH3_FACTOR, N_TO_NO2_FACTOR, N_TO_NO3_FACTOR
from models.nmodel import NModel

BASE_INPUTS = {
    "crop": "wheat",
    "ammonia_due_to_manure": 0.0, "ammonia_due_to_mineral_fert": 0.0,
    "ammonia_due_to_other_orga_fert": 0.0, "bulk_density_of_soil": 1300.0,
    "c_per_n_ratio": 11.0, "clay_content": 0.30108, "considered_soil_volume": 5000.0,
    "drained_part": 0.0, "nitrogen_from_all_manure": 0.0, "nitrogen_from_crop_residues": 0.0,
    "nitrogen_from_mineral_fert": 0.0, "nitrogen_from_other_orga_fert": 0.0,
    "soluble_nitrogen_from_organic_fert": 0.0, "soc_change_kg_c": 0.0,
    "luc_from_forest_or_grassland": "no",
    "nitrogen_uptake_by_crop": 150.0, "norg_per_ntotal_ratio": 0.85,
    "organic_carbon_content": 0.011, "average_annual_precipitation": 800.0,
    "crop_cycle_per_year": 1.0, "rooting_depth": 0.7, "water_use_total": 0.0, "wet_climate_share": 1.0,
}

# N inputs of the reference case: 100 kg mineral N, 20 kg N of crop residues + 5 kg N_som as other inputs
REF = dict(n_synthetic=100.0, n_other=25.0, nh3_kg=10.0, nox_kg=5.0, no3_kg=50.0)


def _model(**overrides):
    inputs = dict(BASE_INPUTS)
    inputs.update(overrides)
    return NModel(inputs)


def _n2o(model, flooded):
    return model._compute_n2o_total(REF["n_synthetic"], REF["n_other"], REF["nh3_kg"], REF["nox_kg"],
                                    REF["no3_kg"] / N_TO_NO3_FACTOR, flooded_rice=flooded)


def _indirect_n(ef4):
    return ef4 * (REF["nh3_kg"] / N_TO_NH3_FACTOR + REF["nox_kg"] / N_TO_NO2_FACTOR) \
        + 0.011 * REF["no3_kg"] / N_TO_NO3_FACTOR


def test_n2o_reference_case_with_nsom_in_a_wet_climate():
    direct = 0.016 * REF["n_synthetic"] + 0.006 * REF["n_other"]
    assert _n2o(_model(), False) == pytest.approx((direct + _indirect_n(0.014)) * N_TO_N2O_FACTOR, rel=1e-9)


def test_rice_factor_applies_to_direct_term_only():
    direct = 0.004 * (REF["n_synthetic"] + REF["n_other"])
    assert _n2o(_model(), True) == pytest.approx((direct + _indirect_n(0.014)) * N_TO_N2O_FACTOR, rel=1e-9)


def test_volatilised_n_is_not_in_the_direct_term():
    assert _model()._compute_direct_n2o_as_n(100.0, 0.0, False) == pytest.approx(1.6)


def test_nsom_only_from_soc_loss_with_cn_ratio():
    assert _model(soc_change_kg_c=-1100.0)._compute_n_som() == pytest.approx(100.0)
    assert _model(soc_change_kg_c=500.0)._compute_n_som() == 0.0
    assert _model(soc_change_kg_c=-1500.0, luc_from_forest_or_grassland="yes")._compute_n_som() \
        == pytest.approx(100.0)


def test_crop_rice_is_treated_as_flooded():
    assert _model(crop="rice")._is_flooded_rice() is True
    assert _model(crop="wheat")._is_flooded_rice() is False

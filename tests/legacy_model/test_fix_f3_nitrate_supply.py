"""Fix F3: N supply to the SQCB-NO3 regression.

S = N_mineral + soluble N_organic - (NH3-N + NOx-N + direct N2O-N), no 0.99 factor, S >= 0;
clay enters the regression as % (fraction x 100) and fractions >= 1 are rejected.
"""
import pytest

from models.atomicmass import NH3_TO_N_FACTOR, NO2_TO_N_FACTOR
from models.manuremodel import LiquidManureType, ManureModel, SolidManureType
from models.nmodel import NModel
from models.otherorganicfertilisermodel import CompostType, OtherOrganicFertModel, SludgeType

BASE_INPUTS = {
    "crop": "wheat", "soc_change_kg_c": 0.0, "luc_from_forest_or_grassland": "no",
    "ammonia_due_to_manure": 0.0, "ammonia_due_to_mineral_fert": 0.0,
    "ammonia_due_to_other_orga_fert": 0.0, "bulk_density_of_soil": 1300.0,
    "c_per_n_ratio": 11.0, "clay_content": 0.30108, "considered_soil_volume": 5000.0,
    "drained_part": 0.0, "nitrogen_from_all_manure": 0.0, "nitrogen_from_crop_residues": 0.0,
    "nitrogen_from_mineral_fert": 0.0, "nitrogen_from_other_orga_fert": 0.0,
    "soluble_nitrogen_from_organic_fert": 0.0,
    "nitrogen_uptake_by_crop": 150.0, "norg_per_ntotal_ratio": 0.85,
    "organic_carbon_content": 0.011, "average_annual_precipitation": 800.0, "crop_cycle_per_year": 1.0,
    "rooting_depth": 0.7, "water_use_total": 0.0,
}


def _model(**overrides):
    inputs = dict(BASE_INPUTS)
    inputs.update(overrides)
    return NModel(inputs)


def test_supply_subtracts_all_gaseous_losses_without_0_99():
    # reference test case: 120 mineral + 20 soluble organic - (5 + 2 + 1.5) = 131.5 kg N
    model = _model(nitrogen_from_mineral_fert=120.0, nitrogen_from_all_manure=40.0,
                   soluble_nitrogen_from_organic_fert=20.0)
    s = model._compute_nitrogen_supply(nh3_as_n=5.0, nox_as_n=2.0, n2o_as_n=1.5)
    assert s == pytest.approx(131.5)


def test_supply_is_never_negative():
    model = _model(nitrogen_from_mineral_fert=10.0)
    assert model._compute_nitrogen_supply(nh3_as_n=8.0, nox_as_n=3.0, n2o_as_n=1.0) == 0.0


def test_leaching_reference_case_annual():
    # reference_models test_nitrate_leaching_annual_and_half_cycle, duration 1 year:
    # N = 21.37 + 800/(30.108*0.7) * (0.0037*131.5 + 0.0000601*5525 - 0.00362*150) = 31.831482
    model = _model()
    norg = model._compute_nitrogen_in_soil_orga_matter(model._compute_carbon_in_soil_orga_matter())
    assert norg == pytest.approx(5525.0)
    assert model._compute_nitrogen_leaching(131.5, norg) == pytest.approx(31.831482, rel=1e-6)


def test_compute_uses_direct_n2o_n_from_applied_n_in_the_supply():
    # 100 kg mineral N, no NH3: NOx-N = 1.2174, N2O-N direct = 1.0 -> S = 97.7826
    model = _model(nitrogen_from_mineral_fert=100.0)
    out = model.compute()
    nox_as_n = out["m_N_Nox_as_n2o_air"] * NO2_TO_N_FACTOR
    expected_s = 100.0 - nox_as_n - 0.01 * 100.0
    assert model.last_nitrogen_supply == pytest.approx(expected_s, rel=1e-9)
    assert nox_as_n == pytest.approx(1.2173913, rel=1e-6)


def test_clay_given_as_percent_is_rejected():
    with pytest.raises(ValueError):
        _model(clay_content=30.1).compute()


def test_manure_soluble_n_is_tan():
    quantities = {k: 0.0 for k in LiquidManureType}
    quantities[LiquidManureType.cattle] = 20.0  # m3, 50 % undiluted -> 10 m3 x 2.75 kg TAN/m3
    solid = {k: 0.0 for k in SolidManureType}
    solid[SolidManureType.cattle] = 10_000.0  # kg -> 10 t x 1.05 kg TAN/t
    model = ManureModel({"liquid_manure_part_before_dilution": 0.5,
                         "liquid_manure_quantities": quantities, "solid_manure_quantities": solid})
    assert model.computeSolubleN() == pytest.approx(10 * 2.75 + 10 * 1.05)
    # NH3 unchanged: TAN x EF products as before, converted to NH3
    nh3_as_n = 10 * 2.75 * 0.55 + 10 * 1.05 * 0.79
    assert model.computeNH3() * NH3_TO_N_FACTOR == pytest.approx(nh3_as_n)


def test_manure_other_without_tan_falls_back_to_total_n():
    quantities = {k: 0.0 for k in LiquidManureType}
    quantities[LiquidManureType.other] = 10.0
    solid = {k: 0.0 for k in SolidManureType}
    model = ManureModel({"liquid_manure_part_before_dilution": 1.0,
                         "liquid_manure_quantities": quantities, "solid_manure_quantities": solid})
    assert model.computeSolubleN() == pytest.approx(model.computeN())


def test_compost_soluble_n_is_tan():
    compost = {k: 0.0 for k in CompostType}
    compost[CompostType.compost] = 10_000.0  # 10 t x 0.83 kg TAN/t
    sludge = {k: 0.0 for k in SludgeType}
    model = OtherOrganicFertModel({"compost_quantities": compost, "sludge_quantities": sludge})
    assert model.computeSolubleN() == pytest.approx(8.3)

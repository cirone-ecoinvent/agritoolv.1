"""Fix F5 / decision L15: NH3 from compost and sewage sludge in kg NH3, EMEP/EEA 2023 3.D Tier 1:
N applied x EF of Table 3-1 (sewage sludge 3Da2b 0.13, other organic wastes 3Da2c 0.08 kg NH3/kg N).
Contents of sludge, feather meal and dried poultry manure from Agribalyse 3.1 (decision L20)."""
import pytest

from models.atomicmass import N_TO_NH3_FACTOR as N_TO_NH3
from models.otherorganicfertilisermodel import CompostType, OtherOrganicFertModel, SludgeType


def _model(compost=None, sludge=None):
    c = {k: 0.0 for k in CompostType}
    c.update(compost or {})
    s = {k: 0.0 for k in SludgeType}
    s.update(sludge or {})
    return OtherOrganicFertModel({"compost_quantities": c, "sludge_quantities": s})


def test_compost_nh3_is_n_times_other_organic_waste_ef():
    # 10 t green-waste compost: 7.0 kg N/t (GRUDAF 2009 Table 42) x 0.08 kg NH3/kg N
    assert _model(compost={CompostType.compost: 10_000}).computeNH3() == pytest.approx(10 * 7.0 * 0.08)


def test_sludge_nh3_uses_sewage_sludge_ef():
    # 1 t liquid sludge: 3 kg N/t (Agribalyse 3.1 Table 142) x 0.13 kg NH3/kg N
    assert _model(sludge={SludgeType.sewagesludge_liquid: 1_000}).computeNH3() == pytest.approx(3.0 * 0.13)


def test_dried_poultry_manure_is_other_organic_waste():
    # 1 t dry poultry droppings: 38.2 kg N/t (Agribalyse 3.1 Table 142) x 0.08 kg NH3/kg N
    assert _model(compost={CompostType.dried_poultry_manure: 1_000}).computeNH3() == pytest.approx(38.2 * 0.08)


def test_agribalyse_contents_of_sludge_and_dried_poultry_manure():
    # decision L20: N and TAN per t FM from Agribalyse 3.1 Table 142 and Table 59, P2O5 of liquid sludge
    dried = _model(sludge={SludgeType.sewagesludge_dried: 1_000})
    assert dried.computeN() == pytest.approx(40.0)
    assert dried.computeSolubleN() == pytest.approx(1.80)
    poultry = _model(compost={CompostType.dried_poultry_manure: 1_000})
    assert poultry.computeSolubleN() == pytest.approx(4.0)
    assert _model(sludge={SludgeType.sewagesludge_liquid: 1_000}).computeP2O5() == pytest.approx(2.5)


def test_stone_meal_without_n_emits_no_nh3():
    model = _model(compost={CompostType.stone_meal: 5_000})
    assert model.computeNH3() == 0.0
    assert model.computeSolubleN() == 0.0


def test_conversion_factor_matches_reference_within_rounding():
    # reference_models.nh3_from_nh3_n(14) == 17 uses 17/14; the model layer uses exact atomic
    # masses (17.0306/14.0067), i.e. +0.13 %. Both are the same stoichiometric conversion.
    assert 14 * N_TO_NH3 == pytest.approx(17, rel=2e-3)

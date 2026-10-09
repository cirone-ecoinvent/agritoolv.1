"""Fix F5: NH3 from compost and sewage sludge is reported as kg NH3 (x 17/14), not kg NH3-N."""
import pytest

from models.atomicmass import N_TO_NH3_FACTOR as N_TO_NH3
from models.otherorganicfertilisermodel import CompostType, OtherOrganicFertModel, SludgeType


def _model(compost_kg=0.0, sludge_kg=0.0):
    compost = {k: 0.0 for k in CompostType}
    sludge = {k: 0.0 for k in SludgeType}
    compost[CompostType.compost] = compost_kg
    sludge[SludgeType.sewagesludge_liquid] = sludge_kg
    return OtherOrganicFertModel({"compost_quantities": compost, "sludge_quantities": sludge})


def test_nh3_is_tan_times_ef_converted_to_nh3():
    # 10 t green-waste compost: 0.83 kg TAN/t * 0.71 = 0.5893 kg NH3-N/t -> 5.893 kg N -> 7.156 kg NH3
    assert _model(compost_kg=10_000).computeNH3() == pytest.approx(5.893 * N_TO_NH3, rel=1e-9)


def test_sludge_uses_its_own_tan_and_ef():
    # 1 t liquid sludge: 2.13 * 0.4 = 0.852 kg NH3-N -> 1.0346 kg NH3
    assert _model(sludge_kg=1_000).computeNH3() == pytest.approx(0.852 * N_TO_NH3, rel=1e-9)


def test_conversion_factor_matches_reference_within_rounding():
    # reference_models.nh3_from_nh3_n(14) == 17 uses 17/14; the model layer uses exact atomic
    # masses (17.0306/14.0067), i.e. +0.13 %. Both are the same stoichiometric conversion.
    assert 14 * N_TO_NH3 == pytest.approx(17, rel=2e-3)

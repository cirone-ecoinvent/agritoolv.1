"""Decision L17: CO2 from seaweed lime ("limestone, from algae") is non-fossil; the CO2 of urea,
limestone, carbonation lime and dolomite stays fossil. kg Ca -> CaCO3 -> CO2 is 1 mol CO2 per mol Ca."""
import pytest

from models.atomicmass import MA_C, MA_Ca, MA_O
from models.co2model import Co2Model
from models.fertilisermodel import CaFertiliserType, NFertiliserType

CO2_PER_KG_CA = (MA_C + 2 * MA_O) / MA_Ca


def _co2(**ca_quantities):
    ca = {k: 0.0 for k in CaFertiliserType}
    ca.update({CaFertiliserType[k]: v for k, v in ca_quantities.items()})
    return Co2Model({"n_fertiliser_quantities": {k: 0.0 for k in NFertiliserType},
                     "part_of_urea_in_UAN": 0.5, "ca_fertiliser_quantities": ca,
                     "magnesium_from_fertilizer": 0.0, "magnesium_as_dolomite": 0.0}).compute()


def test_seaweed_lime_is_non_fossil():
    co2 = _co2(ca_seaweed_limestone=100.0)
    assert co2["m_co2_CO2_from_fertilisers"] == 0.0
    assert co2["m_co2_CO2_non_fossil_from_fertilisers"] == pytest.approx(100.0 * CO2_PER_KG_CA)


def test_limestone_and_carbonation_lime_stay_fossil():
    co2 = _co2(ca_limestone=60.0, ca_carbonation_limestone=40.0)
    assert co2["m_co2_CO2_from_fertilisers"] == pytest.approx(100.0 * CO2_PER_KG_CA)
    assert co2["m_co2_CO2_non_fossil_from_fertilisers"] == 0.0


def test_total_co2_is_unchanged_by_the_split():
    co2 = _co2(ca_limestone=50.0, ca_seaweed_limestone=50.0)
    total = co2["m_co2_CO2_from_fertilisers"] + co2["m_co2_CO2_non_fossil_from_fertilisers"]
    assert total == pytest.approx(100.0 * CO2_PER_KG_CA)

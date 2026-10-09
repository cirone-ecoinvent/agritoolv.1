"""Fix F4c: heavy metals of mineral fertilisers from Freiermuth 2006 Tab. 6 (CSV), keyed by metal
name; compound fertilisers via the generic means; Zn fertilisers no longer counted as Pb.
Reference: reference_models.hm_input_mineral / hm_input_compound."""
import pytest

from models.fertilisermodel import (CaFertiliserType, FertModel, KFertiliserType, NFertiliserType,
                                    PFertiliserType, ZnFertiliserType)
from models.modelEnums import HeavyMetalType


def _model(n=None, p=None, k=None, ca=None, zn=None):
    def quantities(enum, values):
        q = {member: 0.0 for member in enum}
        q.update(values or {})
        return q
    return FertModel({
        "n_fertiliser_quantities": quantities(NFertiliserType, n),
        "p_fertiliser_quantities": quantities(PFertiliserType, p),
        "k_fertiliser_quantities": quantities(KFertiliserType, k),
        "ca_fertiliser_quantities": quantities(CaFertiliserType, ca),
        "zn_fertiliser_quantities": quantities(ZnFertiliserType, zn),
        "soil_with_ph_under_or_7": 1.0, "climate_zone_1": "temperate_climate",
        "cultivation_type": "open_ground",
    })


def test_compound_fertiliser_zinc_is_not_lead():
    # reference: hm_input_compound(n_kg=1) -> Zn 121.43, Pb 5.37 (generic mean N)
    hm = _model(n={NFertiliserType.mono_ammonium_phosphate: 1.0}).computeHeavyMetal()
    assert hm[HeavyMetalType.zn] == pytest.approx(121.43)
    assert hm[HeavyMetalType.pb] == pytest.approx(5.37)
    assert hm[HeavyMetalType.hg] == 0.0  # no Hg data in Tab. 6


def test_other_zinc_fertiliser_is_zinc():
    hm = _model(zn={ZnFertiliserType.zn_other: 2.0}).computeHeavyMetal()
    assert hm[HeavyMetalType.zn] == pytest.approx(2.0e6)
    assert hm[HeavyMetalType.pb] == 0.0


def test_explicit_rows():
    hm = _model(n={NFertiliserType.urea: 100.0}, p={PFertiliserType.superphosphate: 10.0},
                k={KFertiliserType.potassium_salt: 50.0}).computeHeavyMetal()
    assert hm[HeavyMetalType.cd] == pytest.approx(100 * 0.11 + 10 * 52.63 + 50 * 0.10)
    assert hm[HeavyMetalType.cr] == pytest.approx(100 * 4.35 + 10 * 342.11 + 50 * 3.33)


def test_calcium_converted_to_cao_for_the_lime_row():
    hm = _model(ca={CaFertiliserType.ca_limestone: 10.0}).computeHeavyMetal()
    assert hm[HeavyMetalType.cr] == pytest.approx(10.0 * 1.39919 * 314.0, rel=1e-5)

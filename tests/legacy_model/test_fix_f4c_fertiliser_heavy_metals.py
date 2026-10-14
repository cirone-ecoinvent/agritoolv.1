"""Heavy metals of mineral fertilisers from SALCAheavymetal 2023 Table 1 (decision L10), keyed by
metal name; compound fertilisers through the unspecified N row (recommendation 4); Zn fertilisers
counted as Zn (fix F4c); Ca rows per kg Ca and Mg fertilisers included (recommendation 7).
Expected values are the numbers of Table 1 (Desaules and Studer 1993)."""
import pytest

from models.fertilisermodel import (CaFertiliserType, FertModel, KFertiliserType, NFertiliserType,
                                    PFertiliserType, ZnFertiliserType)
from models.modelEnums import HeavyMetalType


def _model(n=None, p=None, k=None, ca=None, zn=None, mg=0.0):
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
        "magnesium_from_fertilizer": mg,
        "soil_with_ph_under_or_7": 1.0,
        "cultivation_type": "open_ground",
    })


def test_compound_fertiliser_n_part_uses_the_unspecified_n_row():
    hm = _model(n={NFertiliserType.mono_ammonium_phosphate: 1.0}).computeHeavyMetal()
    assert hm[HeavyMetalType.zn] == pytest.approx(121)
    assert hm[HeavyMetalType.pb] == pytest.approx(5.37)
    assert hm[HeavyMetalType.hg] == pytest.approx(0.403)  # Hg now available in Table 1


def test_other_zinc_fertiliser_is_zinc():
    hm = _model(zn={ZnFertiliserType.zn_other: 2.0}).computeHeavyMetal()
    assert hm[HeavyMetalType.zn] == pytest.approx(2.0e6)
    assert hm[HeavyMetalType.pb] == 0.0


def test_explicit_rows():
    hm = _model(n={NFertiliserType.urea: 100.0}, p={PFertiliserType.superphosphate: 10.0},
                k={KFertiliserType.potassium_salt: 50.0}).computeHeavyMetal()
    assert hm[HeavyMetalType.cd] == pytest.approx(100 * 0.109 + 10 * 52.6 + 50 * 0.1)
    assert hm[HeavyMetalType.cr] == pytest.approx(100 * 4.35 + 10 * 342 + 50 * 3.33)
    assert hm[HeavyMetalType.hg] == pytest.approx(100 * 0.435 + 10 * 0.579 + 50 * 0.0833)


def test_calcium_per_kg_ca_without_conversion():
    hm = _model(ca={CaFertiliserType.ca_limestone: 10.0}).computeHeavyMetal()
    assert hm[HeavyMetalType.cr] == pytest.approx(10.0 * 314)


def test_magnesium_fertilisers_are_counted():
    hm = _model(mg=20.0).computeHeavyMetal()
    assert hm[HeavyMetalType.ni] == pytest.approx(20.0 * 12.2)
    assert hm[HeavyMetalType.hg] == pytest.approx(20.0 * 0.446)

"""Heavy metals of compost and sewage sludge from SALCAheavymetal 2023 Table 1 (decision L10).
Sewage sludge values are used per kg fresh matter (recommendation 5). Expected values use the
numbers of Table 1."""
import pytest

from models.modelEnums import HeavyMetalType
from models.otherorganicfertilisermodel import CompostType, OtherOrganicFertModel, SludgeType


def _model(compost=None, sludge=None):
    c = {k: 0.0 for k in CompostType}
    c.update(compost or {})
    s = {k: 0.0 for k in SludgeType}
    s.update(sludge or {})
    return OtherOrganicFertModel({"compost_quantities": c, "sludge_quantities": s})


def test_sewage_sludge_per_kg_fresh_matter():
    hm = _model(sludge={SludgeType.sewagesludge_dehydrated: 1000.0}).computeHeavyMetal()
    assert hm[HeavyMetalType.cd] == pytest.approx(1000 * 0.64)  # no further DM factor
    assert hm[HeavyMetalType.hg] == pytest.approx(1000 * 0.72)


def test_vinasse_with_table_dm():
    hm = _model(compost={CompostType.vinasse: 1000.0}).computeHeavyMetal()
    assert hm[HeavyMetalType.zn] == pytest.approx(1000 * 0.55 * 52.9)


def test_stone_meal_has_no_heavy_metals():
    hm = _model(compost={CompostType.stone_meal: 5000.0}).computeHeavyMetal()
    assert all(v == 0.0 for v in hm.values())

"""Heavy metals of manure in mg: kg FM x DM x mg/kg DM, with the farmyard-manure rows of
SALCAheavymetal 2023 Table 1 (decision L10). Expected values use the numbers of Table 1."""
import pytest

from models.manuremodel import LiquidManureType, ManureModel, SolidManureType
from models.modelEnums import HeavyMetalType


def _model(liquid=None, solid=None, dilution=1.0):
    lq = {k: 0.0 for k in LiquidManureType}
    lq.update(liquid or {})
    so = {k: 0.0 for k in SolidManureType}
    so.update(solid or {})
    return ManureModel({"liquid_manure_part_before_dilution": dilution,
                        "liquid_manure_quantities": lq, "solid_manure_quantities": so})


def test_solid_pig_manure_in_mg():
    # 10 000 kg FM x 0.27 DM x 1370 mg Zn/kg DM ("pigs, solid manure")
    hm = _model(solid={SolidManureType.pigs: 10_000.0}).computeHeavyMetal()
    assert hm[HeavyMetalType.zn] == pytest.approx(10_000 * 0.27 * 1370)
    assert hm[HeavyMetalType.hg] == pytest.approx(10_000 * 0.27 * 0.8)


def test_liquid_cattle_manure_split_between_two_rows():
    # 10 m3 undiluted x 1020 kg/m3 (decision L18) = 10 200 kg FM; 50 % liquid manure (9 % DM, 162) + 50 % slurry (7.5 % DM, 123)
    hm = _model(liquid={LiquidManureType.cattle: 10.0}).computeHeavyMetal()
    assert hm[HeavyMetalType.zn] == pytest.approx(10_200 * (0.5 * 0.09 * 162 + 0.5 * 0.075 * 123), rel=1e-9)


def test_other_manure_uses_the_unspecified_rows():
    hm = _model(solid={SolidManureType.other: 1000.0}).computeHeavyMetal()
    assert hm[HeavyMetalType.cu] == pytest.approx(1000 * 0.33 * 61)
    hm = _model(liquid={LiquidManureType.other: 1000 / 1020}).computeHeavyMetal()
    assert hm[HeavyMetalType.zn] == pytest.approx(1000 * 0.07 * 766)


def test_dilution_share_reduces_the_fresh_matter():
    full = _model(liquid={LiquidManureType.pig: 5.0}, dilution=1.0).computeHeavyMetal()
    half = _model(liquid={LiquidManureType.pig: 5.0}, dilution=0.5).computeHeavyMetal()
    assert half[HeavyMetalType.cu] == pytest.approx(full[HeavyMetalType.cu] / 2)


def test_hens_and_poultry_litter_is_the_mean_of_broiler_and_laying_hen_litter():
    hm = _model(solid={SolidManureType.laying_hen_litter: 1000.0}).computeHeavyMetal()
    assert hm[HeavyMetalType.ni] == pytest.approx(1000 * (0.5 * 0.65 * 40.0 + 0.5 * 0.45 * 7.9))

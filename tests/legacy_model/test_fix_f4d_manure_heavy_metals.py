"""Fix F4d: heavy metals of manure in mg: kg FM x DM x mg/kg DM (Freiermuth 2006 Tab. 7, CSV).
Reference: reference_models.hm_input_manure (10 t cattle slurry -> 92 475 mg Zn)."""
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
    # 10 000 kg FM x 0.27 DM x 746.5 mg Zn/kg DM
    hm = _model(solid={SolidManureType.pigs: 10_000.0}).computeHeavyMetal()
    assert hm[HeavyMetalType.zn] == pytest.approx(10_000 * 0.27 * 746.5)
    assert hm[HeavyMetalType.hg] == pytest.approx(10_000 * 0.27 * 0.8)


def test_liquid_cattle_manure_split_between_two_classes():
    # 10 m3 undiluted x 1006 kg/m3 = 10 060 kg FM; 50 % liquid manure (9 % DM, 162.2) + 50 % slurry (7.5 % DM, 123.3)
    hm = _model(liquid={LiquidManureType.cattle: 10.0}).computeHeavyMetal()
    expected = 10_060 * (0.5 * 0.09 * 162.2 + 0.5 * 0.075 * 123.3)
    assert hm[HeavyMetalType.zn] == pytest.approx(expected, rel=1e-9)


def test_reference_slurry_value_through_the_slurry_class():
    # reference: 10 t fresh cattle slurry, 7.5 % DM, 123.3 mg Zn/kg DM -> 92 475 mg.
    # 20 m3 cattle liquid manure (50 % of it is the slurry class) at 1 t/m3 -> 10 t slurry share
    hm = _model(liquid={LiquidManureType.cattle: 20.0 * 1000 / 1006}).computeHeavyMetal()
    slurry_part = 10_000 * 0.075 * 123.3
    liquid_part = 10_000 * 0.09 * 162.2
    assert hm[HeavyMetalType.zn] == pytest.approx(slurry_part + liquid_part, rel=1e-9)
    assert slurry_part == pytest.approx(92_475)


def test_dilution_share_reduces_the_fresh_matter():
    full = _model(liquid={LiquidManureType.pig: 5.0}, dilution=1.0).computeHeavyMetal()
    half = _model(liquid={LiquidManureType.pig: 5.0}, dilution=0.5).computeHeavyMetal()
    assert half[HeavyMetalType.cu] == pytest.approx(full[HeavyMetalType.cu] / 2)


def test_laying_hen_litter_is_the_mean_of_broiler_and_deep_pit_classes():
    hm = _model(solid={SolidManureType.laying_hen_litter: 1000.0}).computeHeavyMetal()
    expected_ni = 1000 * (0.5 * 0.65 * 40.0 + 0.5 * 0.45 * 7.9)
    assert hm[HeavyMetalType.ni] == pytest.approx(expected_ni)

"""Heavy-metal balance (SALCAheavymetal, Nemecek et al. 2023, Appendix 7, Eq. 3-7): allocation
factor applied once to each output, accumulation factor 1.86, deposition and leaching scaled by the
occupation period. Since decision L10 the deposition, leaching and soil values come from Table 1 of
the 2023 document (expected values below use the numbers of that table: deposition Zn 54 800,
leaching Zn 33 000 mg/(ha*yr), arable soil Zn 58 mg/kg)."""
import pytest

import dataloader
from defaultGeneration import HeavyMetalExportWithHarvestGenerator
from models.hmmodel import HmModel, PesticideType
from models.pmodel import LandUseCategory
from models.modelEnums import HeavyMetalType

ZERO = {m: 0.0 for m in HeavyMetalType}


def _inputs(**overrides):
    inputs = {
        "crop_cycle_per_year": 1.0, "hm_from_manure": dict(ZERO), "hm_from_mineral_fert": dict(ZERO),
        "hm_from_other_organic_fert": dict(ZERO), "hm_from_seed": dict(ZERO),
        "hm_pesticides_quantities": {p: 0.0 for p in PesticideType},
        "hm_export_with_harvest": dict(ZERO), "drained_part": 0.0, "eroded_soil": 0.0,
        "land_use_category": LandUseCategory.arable_land,
    }
    inputs.update(overrides)
    return inputs


def _reference_case(**overrides):
    # reference test: hm_input_compound(n_kg=100) -> Zn 12143 mg; wheat_grains 8000 kg DM -> 168800 mg Zn
    mineral = dict(ZERO)
    mineral[HeavyMetalType.zn] = 100 * 121.43
    export = dict(ZERO)
    export[HeavyMetalType.zn] = 8000 * 21.1
    case = dict(hm_from_mineral_fert=mineral, hm_export_with_harvest=export, eroded_soil=10_000.0)
    case.update(overrides)
    return _inputs(**case)


A_ZN = 12143 / (12143 + 54800)
EROSION_ZN = 58 * 10_000 * 1.86 * 0.2


def test_zinc_balance_with_2023_table():
    model = HmModel(_reference_case())
    out = model.compute()
    assert model.last_allocation[HeavyMetalType.zn] == pytest.approx(A_ZN, rel=1e-12)
    assert out["m_hm_heavymetal_to_ground_water"][HeavyMetalType.zn] == pytest.approx(33000 * A_ZN * 1e-6)
    assert out["m_hm_heavymetal_to_surface_water"][HeavyMetalType.zn] == pytest.approx(EROSION_ZN * A_ZN * 1e-6)
    assert out["m_hm_heavymetal_to_soil_minus_uptake"][HeavyMetalType.zn] == pytest.approx(
        (12143 - (168800 + 33000 + EROSION_ZN) * A_ZN) * 1e-6)


def test_soil_row_follows_the_seven_land_use_classes():
    copper = dict(ZERO)
    copper[HeavyMetalType.cu] = 1000.0
    fruit = HmModel(_inputs(hm_from_mineral_fert=copper, eroded_soil=10_000.0,
                            land_use_category=LandUseCategory.fruit_trees))
    out = fruit.compute()
    a = fruit.last_allocation[HeavyMetalType.cu]
    assert a == pytest.approx(1000.0 / (1000.0 + 23800))
    assert out["m_hm_heavymetal_to_surface_water"][HeavyMetalType.cu] == pytest.approx(126 * 10_000 * 0.372 * a * 1e-6)


def test_balance_equals_freiermuth_form():
    # (inputs + deposition - raw outputs) * A == M_agro - allocated outputs
    model = HmModel(_reference_case())
    out = model.compute()
    a = model.last_allocation[HeavyMetalType.zn]
    old = (12143 + 54800 - 168800 - 33000 - EROSION_ZN) * a * 1e-6
    assert out["m_hm_heavymetal_to_soil_minus_uptake"][HeavyMetalType.zn] == pytest.approx(old, rel=1e-9)


def test_no_agro_input_means_zero_allocation_and_zero_outputs():
    out = HmModel(_inputs(eroded_soil=1000.0)).compute()
    for key in out:
        assert all(v == 0.0 for v in out[key].values()), key


def test_leaching_split_by_drained_fraction():
    out = HmModel(_reference_case(drained_part=0.4, eroded_soil=0.0)).compute()
    gw = out["m_hm_heavymetal_to_ground_water"][HeavyMetalType.zn]
    sw = out["m_hm_heavymetal_to_surface_water"][HeavyMetalType.zn]
    assert sw == pytest.approx(0.4 * (gw + sw))


def test_deposition_and_leaching_scale_with_occupation_period():
    half = HmModel(_reference_case(crop_cycle_per_year=2.0, eroded_soil=0.0))
    out = half.compute()
    assert half.last_allocation[HeavyMetalType.zn] == pytest.approx(12143 / (12143 + 54800 * 0.5))
    assert out["m_hm_heavymetal_to_ground_water"][HeavyMetalType.zn] == pytest.approx(
        33000 * 0.5 * half.last_allocation[HeavyMetalType.zn] * 1e-6)


def test_nickel_leaching_na_is_zero():
    mineral = dict(ZERO)
    mineral[HeavyMetalType.ni] = 1000.0
    out = HmModel(_inputs(hm_from_mineral_fert=mineral)).compute()
    assert out["m_hm_heavymetal_to_ground_water"][HeavyMetalType.ni] == 0.0


def test_zinc_fungicide_share_from_csv():
    pest = {p: 0.0 for p in PesticideType}
    pest[PesticideType.mancozeb] = 1000.0  # g
    pest[PesticideType.cu] = 100.0  # g Cu
    model = HmModel(_inputs(hm_pesticides_quantities=pest))
    values = model._compute_pesticides()
    assert values[HeavyMetalType.zn] == pytest.approx(1000.0 * 65.39 / 541.07 * 0.95 * 1000.0, rel=1e-6)
    assert values[HeavyMetalType.cu] == pytest.approx(100.0 * 0.95 * 1000.0)


def test_harvest_export_generator_uses_2023_products_and_coproducts():
    gen = HeavyMetalExportWithHarvestGenerator()
    base = {"yield_BP1_per_crop_cycle": "", "yield_BP2_per_crop_cycle": "", "yield_BP3_per_crop_cycle": ""}
    wheat = gen.generateDefault("", dict(base, crop="wheat", yield_main_product_dry_per_crop_cycle=8000.0))
    assert wheat[HeavyMetalType.zn] == pytest.approx(8000 * 17.2)      # wheat grains, Table 1
    assert wheat[HeavyMetalType.cd] == pytest.approx(8000 * 0.048)
    apple = gen.generateDefault("", dict(base, crop="apple", yield_main_product_dry_per_crop_cycle=1000.0))
    assert apple[HeavyMetalType.cu] == pytest.approx(1000 * 6.48)      # main product, mean
    straw = gen.generateDefault("", dict(base, crop="wheat", yield_main_product_dry_per_crop_cycle=0.0,
                                         yield_BP1_per_crop_cycle=5000.0))
    assert straw[HeavyMetalType.zn] == pytest.approx(5000 * 0.6 * 20.6)  # co-product, mean, DM 0.6


def test_pesticide_metals_exported_with_the_harvest():
    pest = {p: 0.0 for p in PesticideType}
    pest[PesticideType.cu] = 1000.0  # g Cu
    model = HmModel(_inputs(hm_pesticides_quantities=pest))
    out = model.compute()
    cu_to_field = 1000.0 * 0.95 * 1000.0
    a = model.last_allocation[HeavyMetalType.cu]
    assert out["m_hm_heavymetal_to_soil_minus_uptake"][HeavyMetalType.cu] == pytest.approx(
        (cu_to_field - 0.05 * cu_to_field - 3600 * a) * 1e-6)

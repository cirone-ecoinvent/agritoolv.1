"""Fix F4 (part a/b): heavy-metal balance with accumulation factor 1.86, allocation factor applied
once to each output, deposition and leaching scaled by the occupation period, harvest export from
Freiermuth 2006 Tab. 5. Reference: reference_models.heavy_metals / hm_biomass."""
import pytest

import dataloader
from defaultGeneration import HeavyMetalExportWithHarvestGenerator
from models.hmmodel import HmModel, LandUseCategoryForHM, PesticideType
from models.modelEnums import HeavyMetalType

ZERO = {m: 0.0 for m in HeavyMetalType}


def _inputs(**overrides):
    inputs = {
        "crop_cycle_per_year": 1.0, "hm_from_manure": dict(ZERO), "hm_from_mineral_fert": dict(ZERO),
        "hm_from_other_organic_fert": dict(ZERO), "hm_from_seed": dict(ZERO),
        "hm_pesticides_quantities": {p: 0.0 for p in PesticideType},
        "hm_export_with_harvest": dict(ZERO), "drained_part": 0.0, "eroded_soil": 0.0,
        "hm_land_use_category": LandUseCategoryForHM.arable_land,
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


def test_zinc_balance_matches_reference():
    model = HmModel(_reference_case())
    out = model.compute()
    assert model.last_allocation[HeavyMetalType.zn] == pytest.approx(0.1184186, rel=1e-6)
    assert out["m_hm_heavymetal_to_ground_water"][HeavyMetalType.zn] == pytest.approx(0.0039078, rel=1e-4)
    assert out["m_hm_heavymetal_to_surface_water"][HeavyMetalType.zn] == pytest.approx(0.0218497, rel=1e-4)  # a = 1.86
    assert out["m_hm_heavymetal_to_soil_minus_uptake"][HeavyMetalType.zn] == pytest.approx(-0.0336035, rel=1e-4)


def test_balance_equals_freiermuth_form():
    # (inputs + deposition - raw outputs) * A == M_agro - allocated outputs
    model = HmModel(_reference_case())
    out = model.compute()
    a = model.last_allocation[HeavyMetalType.zn]
    old = (12143 + 90400 - 168800 - 33000 - 49.6 * 10_000 * 1.86 * 0.2) * a * 1e-6
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
    assert half.last_allocation[HeavyMetalType.zn] == pytest.approx(12143 / (12143 + 90400 * 0.5))
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


def test_harvest_export_generator_uses_tab5_product():
    gen = HeavyMetalExportWithHarvestGenerator()
    export = gen.generateDefault("", {"crop": "wheat", "yield_main_product_dry_per_crop_cycle": 8000.0})
    assert export[HeavyMetalType.zn] == pytest.approx(8000 * 21.1)
    assert export[HeavyMetalType.hg] == pytest.approx(8000 * 0.01)
    generic = gen.generateDefault("", {"crop": "apple", "yield_main_product_dry_per_crop_cycle": 1000.0})
    assert generic[HeavyMetalType.cu] == pytest.approx(1000 * 6.6)
    rice = gen.generateDefault("", {"crop": "rice", "yield_main_product_dry_per_crop_cycle": 1000.0})
    assert rice[HeavyMetalType.hg] == 0.0  # NA -> 0

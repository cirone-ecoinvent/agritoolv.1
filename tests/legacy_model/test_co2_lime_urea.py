"""Decision L67 (issue #52): CO2 of lime and urea, IPCC 2006 Vol. 4 ch. 11 Eq. 11.12 and 11.13 (no refinement in
2019), stoichiometric factors.

- UAN: default urea share 1.0 (IPCC 2006 p. 11.32, Step 3), a given share overrides it.
- Calcium ammonium nitrate: the carbonate of its dolomite filler counts (p. 11.27, Step 1); composition per kg of
  product from the ecoinvent technical correction CPSTC-520 (data/can_composition.csv).
- Dolomite as product (kg CaMg(CO3)2 per ha), also for the split of the Mg fertiliser into MgSO4 and dolomite.

Expected values computed by hand with the atomic masses of models/atomicmass.py (C 12.0107, O 15.9994,
N 14.00674, Mg 24.3050, Ca 40.078, S 32.066; CO2 44.0095, CaMg(CO3)2 184.4008, MgSO4 120.3686)."""
import warnings

import pytest

import dataloader
import regression_support as rs
from defaultGeneration import DEFAULTS_VALUES_GENERATORS
from excelInputMappingRules import EXCEL_INPUT_MAPPING_RULES
from models.co2model import Co2Model, can_co2_per_kg_n
from models.fertilisermodel import CaFertiliserType, NFertiliserType
from outputMapping import magnesium_fertiliser_split

FOSSIL = "m_co2_CO2_from_fertilisers"
NON_FOSSIL = "m_co2_CO2_non_fossil_from_fertilisers"


def _co2(n=None, ca=None, part_of_urea_in_UAN=None, dolomite_applied=0.0):
    n_quantities = {k: 0.0 for k in NFertiliserType}
    n_quantities.update(n or {})
    ca_quantities = {k: 0.0 for k in CaFertiliserType}
    ca_quantities.update(ca or {})
    if part_of_urea_in_UAN is None:
        part_of_urea_in_UAN = dataloader.param("part_of_urea_in_UAN_default")
    return Co2Model({"n_fertiliser_quantities": n_quantities, "part_of_urea_in_UAN": part_of_urea_in_UAN,
                     "ca_fertiliser_quantities": ca_quantities, "dolomite_applied": dolomite_applied}).compute()


# --- urea and UAN (Eq. 11.13) ---

def test_urea_100_kg_n():
    # 44.0095 / (2 x 14.00674) = 1.571012 kg CO2 / kg N (IPCC default path 0.20 x 60.055/28.013 x 44/12: 157.21)
    assert _co2(n={NFertiliserType.urea: 100.0})[FOSSIL] == pytest.approx(157.10, abs=0.005)


def test_default_urea_share_of_uan_is_one():
    assert dataloader.param("part_of_urea_in_UAN_default") == 1.0
    assert DEFAULTS_VALUES_GENERATORS["part_of_urea_in_UAN"].generateDefault("part_of_urea_in_UAN", {}) == 1.0


def test_uan_100_kg_n_without_given_share():
    # was 78.55 with the legacy share 0.5
    assert _co2(n={NFertiliserType.ureaAN: 100.0})[FOSSIL] == pytest.approx(157.10, abs=0.005)


def test_uan_100_kg_n_with_given_share():
    co2 = _co2(n={NFertiliserType.ureaAN: 100.0}, part_of_urea_in_UAN=0.5)
    assert co2[FOSSIL] == pytest.approx(78.55, abs=0.005)


# --- calcium ammonium nitrate (Eq. 11.12, lime in mixture with fertilisers) ---

def test_can_composition_table():
    composition = dataloader.table("can_composition.csv")
    assert composition["ammonium nitrate"]["kg_per_kg_product"] == 0.771
    assert composition["dolomite"]["kg_per_kg_product"] == 0.229
    assert composition["nitrogen"]["kg_per_kg_product"] == 0.2699


def test_can_carbon_matches_the_ecoinvent_production_dataset():
    # CPSTC-520: 0.229 kg dolomite x 2 x 12.0107 / 184.4008 = 0.029831 kg C per kg CAN, the carbon input of the
    # ecoinvent 3.12 dataset 'calcium ammonium nitrate production' (0.229 kg dolomite per kg)
    from models.atomicmass import MA_C, MA_DOLOMITE
    composition = dataloader.table("can_composition.csv")
    carbon = composition["dolomite"]["kg_per_kg_product"] * 2 * MA_C / MA_DOLOMITE
    assert carbon == pytest.approx(0.029831, abs=5e-7)


def test_can_100_kg_n():
    # 0.229 x 2 x 44.0095 / 184.4008 / 0.2699 = 0.40499 kg CO2 / kg N -> 40.50 kg CO2
    assert can_co2_per_kg_n() == pytest.approx(0.4050, abs=5e-5)
    co2 = _co2(n={NFertiliserType.lime_ammonium_nitrate: 100.0})
    assert co2[FOSSIL] == pytest.approx(40.50, abs=0.005)
    assert co2[NON_FOSSIL] == 0.0


def test_other_n_fertilisers_give_no_co2():
    others = {k: 100.0 for k in NFertiliserType
              if k not in (NFertiliserType.urea, NFertiliserType.ureaAN, NFertiliserType.lime_ammonium_nitrate)}
    assert _co2(n=others)[FOSSIL] == 0.0


# --- dolomite as product (Eq. 11.12) ---

def test_dolomite_100_kg_product():
    # 2 x 44.0095 / 184.4008 = 0.477324 kg CO2 / kg dolomite (IPCC default 0.13 x 44/12 = 0.4767)
    co2 = _co2(dolomite_applied=100.0)
    assert co2[FOSSIL] == pytest.approx(47.73, abs=0.005)
    assert co2[NON_FOSSIL] == 0.0


def test_magnesium_as_dolomite_is_removed():
    assert "magnesium_as_dolomite" not in DEFAULTS_VALUES_GENERATORS
    assert "magnesium_as_dolomite" not in EXCEL_INPUT_MAPPING_RULES
    assert "magnesium_as_dolomite" not in Co2Model._input_variables
    assert "magnesium_from_fertilizer" not in Co2Model._input_variables
    assert DEFAULTS_VALUES_GENERATORS["dolomite_applied"].generateDefault("dolomite_applied", {}) == 0.0


def test_magnesium_split_rest_is_magnesium_sulfate():
    # 100 kg dolomite carry 100 x 24.305 / 184.4008 = 13.18053 kg Mg; (30 - 13.18053) x 120.3686 / 24.305 = 83.2971
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        mgso4, dolomite = magnesium_fertiliser_split(30.0, 100.0)
    assert dolomite == 100.0
    assert mgso4 == pytest.approx(83.2971, abs=5e-4)


def test_magnesium_split_without_dolomite():
    # 30 x 120.3686 / 24.305 = 148.5726 kg MgSO4 (the legacy default sent all Mg to dolomite)
    mgso4, dolomite = magnesium_fertiliser_split(30.0, 0.0)
    assert dolomite == 0.0
    assert mgso4 == pytest.approx(148.5726, abs=5e-4)


def test_magnesium_split_dolomite_above_total_warns():
    with pytest.warns(UserWarning, match="exceeds magnesium_from_fertilizer"):
        mgso4, dolomite = magnesium_fertiliser_split(10.0, 100.0)
    assert mgso4 == 0.0
    assert dolomite == 100.0


# --- unchanged: limestone, carbonation lime (fossil), seaweed lime (non-fossil, L17) ---

def test_limestone_carbonation_and_seaweed_lime_unchanged():
    # 44.0095 / 40.078 = 1.098096 kg CO2 / kg Ca
    co2 = _co2(ca={CaFertiliserType.ca_limestone: 60.0, CaFertiliserType.ca_carbonation_limestone: 40.0,
                   CaFertiliserType.ca_seaweed_limestone: 50.0})
    assert co2[FOSSIL] == pytest.approx(109.8096, abs=5e-4)
    assert co2[NON_FOSSIL] == pytest.approx(54.9048, abs=5e-4)


# --- whole model sequence ---

def test_model_sequence_dolomite_and_mg_exchanges():
    """wheat_IT with 30 kg Mg of which 100 kg dolomite: +47.73 kg fossil CO2, exchanges 100 kg dolomite and
    83.2971 kg MgSO4."""
    base_inputs = rs.load_inputs("wheat_IT")
    from modelsSequence import ModelsSequence
    import config
    original = config.master_data_path
    config.master_data_path = lambda: None
    try:
        base = ModelsSequence(dict(base_inputs)).executeSequence()
        inputs = dict(base_inputs, fert_other_total_mg=30.0, dolomite_applied=100.0)
        out = ModelsSequence(inputs).executeSequence()
    finally:
        config.master_data_path = original
    assert out["CO2_from_fertilisers"] - base["CO2_from_fertilisers"] == pytest.approx(47.7324, abs=5e-4)
    assert out["magnesium_from_fertilizer_as_dolomite"] == 100.0
    assert out["magnesium_from_fertilizer_as_mgso4"] == pytest.approx(83.2971, abs=5e-4)

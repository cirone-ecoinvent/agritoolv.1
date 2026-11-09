"""Decision L66 (issue #47): methane of flooded rice with the Tier 1 method of the IPCC 2019 Refinement, Vol. 4 ch. 5.5
(ipcc2019_rice_ch4_factors.csv), and the direct N2O factor of flooded rice selected by the same water regime.

Tests 1-12 are the cases of the issue, with expected values computed independently (kg CH4 per ha and crop cycle,
relative tolerance 1e-6)."""
import pytest

import dataloader
import regression_support as rs
from defaultGeneration import DEFAULTS_VALUES_GENERATORS
from models.manuremodel import LiquidManureType, SolidManureType
from models.nmodel import NModel
from models.otherorganicfertilisermodel import CompostType, SludgeType
from models.ricech4model import RiceCh4Model, factor, rice_region, sf_o
from test_fix_f2_n2o import BASE_INPUTS

REL = 1e-6
FACTORS = "ipcc2019_rice_ch4_factors.csv"

# IPCC 2019 Vol. 4 ch. 5, checked against the rendered pages: (parameter, case) -> value, uncertainty range
PUBLISHED = {
    ("ef_c", "World"): (1.19, 0.80, 1.76), ("ef_c", "Africa"): (1.19, 0.80, 1.76),
    ("ef_c", "East Asia"): (1.32, 0.89, 1.96), ("ef_c", "Southeast Asia"): (1.22, 0.83, 1.81),
    ("ef_c", "South Asia"): (0.85, 0.58, 1.26), ("ef_c", "Europe"): (1.56, 1.06, 2.31),
    ("ef_c", "North America"): (0.65, 0.44, 0.96), ("ef_c", "South America"): (1.27, 0.86, 1.88),
    ("cultivation_period", "World"): (113, 74, 152), ("cultivation_period", "Africa"): (113, 74, 152),
    ("cultivation_period", "East Asia"): (112, 73, 147), ("cultivation_period", "Southeast Asia"): (102, 78, 150),
    ("cultivation_period", "South Asia"): (112, 90, 140), ("cultivation_period", "Europe"): (123, 111, 153),
    ("cultivation_period", "North America"): (139, 110, 165), ("cultivation_period", "South America"): (124, 110, 146),
    ("sf_w", "aggregated_upland"): (0.0, None, None), ("sf_w", "aggregated_irrigated"): (0.60, 0.44, 0.78),
    ("sf_w", "aggregated_rainfed"): (0.45, 0.32, 0.62), ("sf_w", "aggregated_deep_water"): (0.06, 0.03, 0.12),
    ("sf_w", "disaggregated_upland"): (0.0, None, None),
    ("sf_w", "disaggregated_continuously_flooded"): (1.00, 0.73, 1.27),
    ("sf_w", "disaggregated_single_drainage"): (0.71, 0.53, 0.94),
    ("sf_w", "disaggregated_multiple_drainage"): (0.55, 0.41, 0.72),
    ("sf_w", "disaggregated_regular_rainfed"): (0.54, 0.39, 0.74),
    ("sf_w", "disaggregated_drought_prone"): (0.16, 0.11, 0.24),
    ("sf_w", "disaggregated_deep_water"): (0.06, 0.03, 0.12),
    ("sf_p", "aggregated"): (1.22, 1.08, 1.37),
    ("sf_p", "disaggregated_non_flooded_lt180"): (1.00, 0.88, 1.12),
    ("sf_p", "disaggregated_non_flooded_gt180"): (0.89, 0.80, 0.99),
    ("sf_p", "disaggregated_flooded_gt30"): (2.41, 2.13, 2.73),
    ("sf_p", "disaggregated_non_flooded_gt365"): (0.59, 0.41, 0.84),
    ("cfoa", "straw_incorporated_short"): (1.00, 0.85, 1.17), ("cfoa", "straw_incorporated_long"): (0.19, 0.11, 0.28),
    ("cfoa", "compost"): (0.17, 0.09, 0.29), ("cfoa", "farm_yard_manure"): (0.21, 0.15, 0.28),
    ("cfoa", "green_manure"): (0.45, 0.36, 0.57),
    ("sf_o_exponent", "none"): (0.59, 0.54, 0.64),
}


def _ch4(country, irrigated="yes", regime=None, preseason=None, days=None, solid=None, liquid=None, compost=None,
         sludge=None, crop="rice"):
    def quantities(enum, given):
        out = dict.fromkeys(enum, 0.0)
        out.update(given or {})
        return out
    return RiceCh4Model({
        "crop": crop, "country": country, "irrigated": irrigated, "rice_water_regime": regime,
        "rice_preseason_water_regime": preseason, "rice_cultivation_period_days": days,
        "solid_manure_quantities": quantities(SolidManureType, solid),
        "liquid_manure_quantities": quantities(LiquidManureType, liquid),
        "compost_quantities": quantities(CompostType, compost),
        "sludge_quantities": quantities(SludgeType, sludge),
    }).ch4()


def _n_model(regime, crop="rice", wet_climate_share=1.0):
    inputs = dict(BASE_INPUTS)
    inputs.update(crop=crop, rice_water_regime=regime, wet_climate_share=wet_climate_share)
    return NModel(inputs)


def _sequence(name, **overrides):
    import config
    from modelsSequence import ModelsSequence
    inputs = rs.load_inputs(name)
    inputs.update(overrides)
    original = config.master_data_path
    config.master_data_path = lambda: None
    try:
        return ModelsSequence(inputs).executeSequence()
    finally:
        config.master_data_path = original


# --- tables -----------------------------------------------------------------------------------------------------

def test_factor_table_is_the_published_one():
    def num(text):
        return float(text) if text else None
    rows = {(r["parameter"], r["case"]): (float(r["value"]), num(r["uncertainty_low"]), num(r["uncertainty_high"]))
            for r in dataloader.rows(FACTORS)}
    assert rows == PUBLISHED


def test_tool_countries_get_the_rice_region_of_decision_5():
    expected = {
        "South Asia": "IN LK", "Southeast Asia": "ID PH TH VN", "East Asia": "CN", "North America": "CA US",
        "South America": "AR BR CL CO CR EC MX PE", "Europe": "BE FI FR DE HU IT NL PL RU CS ES CH UA",
        "Africa": "CI GH KE MA ZA", "World": "AU IL NZ TR GLO"}
    for region, countries in expected.items():
        for country in countries.split():
            assert rice_region(country) == region, country


def test_every_organic_input_of_the_tool_is_in_the_amendment_mapping():
    mapping = dataloader.table("ipcc2019_rice_organic_amendment_mapping.csv", "tool_variable", numeric=False)
    variables = {e.value for enum in (SolidManureType, LiquidManureType, CompostType, SludgeType) for e in enum}
    assert set(mapping) == variables
    counted = {v: r["cfoa_class"] for v, r in mapping.items() if r["cfoa_class"] != "none"}
    assert counted == {**{e.value: "farm_yard_manure" for e in SolidManureType},
                       "composttype_dried_poultry_manure": "farm_yard_manure", "composttype_compost": "compost"}


# --- tests 1-12 of the issue -------------------------------------------------------------------------------------

def test_01_regression_rice_in():
    """IN (South Asia), irrigated, regimes N/A, default manure: 0.85 x 0.60 x 1.22 x SF_o x 112."""
    output = rs.run_case("rice_IN")
    solid_t = sum(output[e.value] for e in SolidManureType) / 1000.0
    assert solid_t == pytest.approx(8.589269, rel=REL)
    assert output["liquid_manure_pig"] > 0  # liquid manure excluded from SF_o
    assert sf_o({e.value: output[e.value] for e in SolidManureType}) == pytest.approx(1.8372398, rel=REL)
    assert output["ch4_rice_air"] == pytest.approx(128.03063, rel=REL)
    assert output["N2o_air"] == pytest.approx(2.637089, rel=REL)  # water regime N/A: aggregated EF1FR 0.004


def test_02_italy_irrigated_without_organic_inputs():
    assert _ch4("IT") == pytest.approx(1.56 * 0.60 * 1.22 * 123, rel=REL)
    assert _ch4("IT") == pytest.approx(140.45616, rel=REL)


@pytest.mark.parametrize("country", ["TH", "VN"])
def test_03_southeast_asia_continuously_flooded_with_compost(country):
    ch4 = _ch4(country, regime="continuously_flooded", preseason="non_flooded_lt180",
               compost={CompostType.compost: 2000.0})
    assert sf_o({"composttype_compost": 2000.0}) == pytest.approx(1.1884799, rel=REL)
    assert ch4 == pytest.approx(147.89444, rel=REL)
    model = _n_model("continuously_flooded")
    assert model._ef1fr() == "ef1fr_continuous_flooding"
    assert model._compute_direct_n2o_as_n(100.0, 0.0, model._ef1fr()) == pytest.approx(0.3)


def test_04_us_multiple_drainage_with_solid_cattle_manure():
    ch4 = _ch4("US", regime="multiple_drainage", preseason="non_flooded_gt180",
               solid={SolidManureType.cattle: 10000.0})
    assert sf_o({"solid_manure_cattle": 10000.0}) == pytest.approx(1.9494109, rel=REL)
    assert ch4 == pytest.approx(86.215282, rel=REL)
    model = _n_model("multiple_drainage")
    assert model._ef1fr() == "ef1fr_drainage"
    assert model._compute_direct_n2o_as_n(100.0, 0.0, model._ef1fr()) == pytest.approx(0.5)
    assert _n_model("single_drainage")._ef1fr() == "ef1fr_drainage"


def test_05_india_not_irrigated():
    assert _ch4("IN", irrigated="no") == pytest.approx(52.2648, rel=REL)


@pytest.mark.parametrize("country", ["IN", "IT", "US", "TR", "GLO"])
def test_06_upland_rice_has_no_methane_and_takes_ef1(country):
    assert _ch4(country, regime="upland", solid={SolidManureType.cattle: 10000.0}) == 0.0
    for share in (1.0, 0.0):
        model = _n_model("upland", wet_climate_share=share)
        assert model._ef1fr() is None
        expected = share * (0.016 * 100.0 + 0.006 * 50.0) + (1.0 - share) * 0.005 * 150.0
        assert model._compute_direct_n2o_as_n(100.0, 50.0, model._ef1fr()) == pytest.approx(expected)
    assert _sequence("rice_IN", rice_water_regime="upland")["ch4_rice_air"] == 0.0


def test_07_turkey_takes_the_world_values():
    assert _ch4("TR") == pytest.approx(98.43204, rel=REL)


def test_08_brazil_takes_south_america():
    assert _ch4("BR") == pytest.approx(115.27536, rel=REL)


@pytest.mark.parametrize("name", ["wheat_IT", "apple_FR"])
def test_09_crops_that_are_not_flooded(name):
    output = rs.run_case(name)
    assert output.get("ch4_rice_air", 0.0) == 0.0
    assert not rs.differences(rs.load_expected(name), output)
    crop = rs.load_inputs(name)["crop"]
    assert _ch4(rs.load_inputs(name)["country"], crop=crop) == 0.0
    assert _n_model("continuously_flooded", crop=crop)._ef1fr() is None


def test_10_equation_5_2_against_the_worked_example_table_5_14b():
    """Products of Eq. 5.2 with the SF values of Table 5.14b (p. 5.59). SF_o of the example (1.21) is not tested:
    it is the factor of straw incorporated long before cultivation, the text says shortly."""
    ef_c = factor("ef_c", "Southeast Asia")
    cases = [(factor("sf_w", "disaggregated_continuously_flooded"), factor("sf_p", "disaggregated_non_flooded_lt180"),
              1.21, 1.4762, 1.48),
             (factor("sf_w", "disaggregated_regular_rainfed"), factor("sf_p", "disaggregated_non_flooded_gt180"),
              1.00, 0.586332, 0.59),
             (factor("sf_w", "disaggregated_deep_water"), factor("sf_p", "disaggregated_flooded_gt30"),
              1.00, 0.176412, 0.18)]
    for sfw, sfp, sfo, expected, printed in cases:
        assert ef_c * sfw * sfp * sfo == pytest.approx(expected, rel=REL)
        assert round(ef_c * sfw * sfp * sfo, 2) == printed


@pytest.mark.parametrize("inputs", [{"liquid": {LiquidManureType.cattle: 30.0, LiquidManureType.pig: 20.0}},
                                    {"sludge": {SludgeType.sewagesludge_dehydrated: 5000.0}},
                                    {"compost": {CompostType.vinasse: 3000.0}}])
def test_11_inputs_without_a_table_5_14_factor_are_not_counted(inputs):
    assert _ch4("IT", **inputs) == pytest.approx(_ch4("IT"), rel=1e-12)
    assert _ch4("IT", **inputs) == pytest.approx(140.45616, rel=REL)


def test_12_given_cultivation_period():
    assert _ch4("IT", days=150) == pytest.approx(171.288, rel=REL)


# --- inputs and defaults -----------------------------------------------------------------------------------------

def test_regime_inputs_flow_through_the_sequence():
    output = _sequence("rice_IN", rice_water_regime="continuously_flooded", rice_preseason_water_regime="flooded_gt30",
                       rice_cultivation_period_days=100)
    baseline = rs.run_case("rice_IN")
    assert output["ch4_rice_air"] == pytest.approx(128.03063 / (0.60 * 1.22 * 112) * (1.00 * 2.41 * 100), rel=REL)
    assert output["N2o_air"] < baseline["N2o_air"]  # EF1FR 0.003 instead of 0.004


@pytest.mark.parametrize("kwargs, message", [({"regime": "flooded"}, "rice_water_regime"),
                                             ({"preseason": "dry"}, "rice_preseason_water_regime"),
                                             ({"days": 0}, "rice_cultivation_period_days"),
                                             ({"irrigated": "unknown"}, "irrigated")])
def test_invalid_inputs_are_rejected(kwargs, message):
    with pytest.raises(ValueError, match=message):
        _ch4("IT", **kwargs)


@pytest.mark.parametrize("value", [None, "", "N/A"])
def test_not_given_means_the_default(value):
    assert _ch4("IT", regime=value, preseason=value, days=value) == pytest.approx(140.45616, rel=REL)


@pytest.mark.parametrize("water, irrigated", [(8000.0, "yes"), (0.0, "no")])
def test_irrigated_default_follows_the_irrigation_water(water, irrigated):
    assert DEFAULTS_VALUES_GENERATORS["irrigated"].generateDefault("irrigated", {"water_use_total": water}) \
        == irrigated

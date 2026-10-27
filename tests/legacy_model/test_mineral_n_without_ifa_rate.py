"""Decision L57: default mineral N of the crops without WFLDB level 1 coefficients where IFA gives no rate for the
country (column mineral_n_without_ifa_rate of n_uptake_other_crop_parameters.csv). ifa_crop_median: median over the
countries with an IFA N rate of the rate / default yield, x yield; n_uptake: mineral share x N uptake (WFLDB L1 split,
N uptake of decision L41); mulberry (not listed): 0. The default manure follows this mineral N (decision L40)."""
import statistics

import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS
from defaultTables import IFA_MINERAL_FERTILISER_PER_CROP_PER_COUNTRY as IFA, \
    N_UPTAKE_PER_KG_MAIN_PRODUCT_PER_CROP, MINERAL_N_RULE_WITHOUT_IFA_RATE as RULE

N_UPTAKE_RULE = {"flax", "hemp", "ginger", "turmeric", "coriander", "mint", "guar", "pomegranate"}
OTHER_CROPS = sorted({r["crop"] for r in dataloader.rows("crop_types.csv")} - set(N_UPTAKE_PER_KG_MAIN_PRODUCT_PER_CROP))
COUNTRIES = sorted({r["country"] for r in dataloader.rows("faostat_country_mapping.csv")} - {"GLO"})


def _defaults(**inputs):
    return DefaultValuesWrapper(inputs, DEFAULTS_VALUES_GENERATORS)


def _crop_median(crop):
    ratios = []
    for country, rates in IFA[crop].items():
        default_yield = _defaults(crop=crop, country=country)["yield_main_product_per_crop_cycle"]
        if rates["n"] is not None and default_yield:
            ratios.append(rates["n"] / default_yield)
    return statistics.median(ratios)


def test_rules():
    assert {crop for crop, rule in RULE.items() if rule == "n_uptake"} == N_UPTAKE_RULE
    assert set(RULE.values()) == {"n_uptake", "ifa_crop_median"}
    assert set(RULE) == set(OTHER_CROPS) - {"mulberry"}


@pytest.mark.parametrize("crop, country", [
    ("cotton", "ES"), ("cotton", "RU"), ("chick_pea", "AU"), ("lentil", "CN"), ("cassava", "CI"), ("grape", "CO"),
    ("sesame_seed", "KE"), ("bellpepper", "AU"), ("pineapple", "CN"), ("chilli", "AU")])
def test_ifa_crop_median(crop, country):
    assert RULE[crop] == "ifa_crop_median" and IFA[crop].get(country) is None
    defaults = _defaults(crop=crop, country=country)
    expected = _crop_median(crop) * defaults["yield_main_product_per_crop_cycle"]
    assert expected > 0.0
    assert defaults["nitrogen_from_mineral_fert"] == pytest.approx(expected)
    doubled = _defaults(crop=crop, country=country,
                        yield_main_product_per_crop_cycle=2.0 * defaults["yield_main_product_per_crop_cycle"])
    assert doubled["nitrogen_from_mineral_fert"] == pytest.approx(2.0 * expected)


@pytest.mark.parametrize("crop, country", [
    ("flax", "FR"), ("hemp", "FR"), ("ginger", "IN"), ("turmeric", "IN"), ("coriander", "IN"), ("mint", "MX"),
    ("mint", "US")])
def test_n_uptake_level1(crop, country):
    defaults = _defaults(crop=crop, country=country)
    expected = dataloader.param("mineral_n_share_of_n_uptake") * defaults["nitrogen_uptake_by_crop"]
    assert expected > 0.0
    assert defaults["nitrogen_from_mineral_fert"] == pytest.approx(expected)


def test_ifa_rate_first():
    # where IFA gives a rate the rule is not used: coriander and mint IL (fresh herbs), cotton IN
    for crop, country in (("coriander", "IL"), ("mint", "IL"), ("cotton", "IN")):
        assert _defaults(crop=crop, country=country)["nitrogen_from_mineral_fert"] == pytest.approx(
            IFA[crop][country]["n"])


def test_remaining_zeros():
    zeros = set()
    for crop in OTHER_CROPS:
        for country in COUNTRIES:
            if _defaults(crop=crop, country=country)["nitrogen_from_mineral_fert"] == 0.0:
                zeros.add((crop, country))
    no_yield = {(crop, country) for crop in ("guar", "mulberry", "pomegranate") for country in COUNTRIES}
    # IFA pulses rate of 0 kg N/ha in FR and IT
    ifa_zero = {(crop, country) for crop in ("chick_pea", "lentil") for country in ("FR", "IT")}
    assert zeros == no_yield | ifa_zero
    for crop, country in ifa_zero:
        assert IFA[crop][country]["n"] == 0.0

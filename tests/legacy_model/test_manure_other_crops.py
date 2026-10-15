"""Decision L40: default manure of the crops without WFLDB level 1 coefficients (L34) where IFA gives a mineral N rate:
the available N of the manure is (1 - mineral share) / mineral share x the level 2 mineral N (IFA rate x yield /
default yield), the WFLDB L1 split of the N input (Guidelines v3.0 section 3.6.2); split and converted as in L29.
The mineral N, P2O5 and K2O at the default yield stay the IFA rates; without an IFA N rate the legacy matrix stays."""
import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS
from defaultMatrixTotalManure import TOTAL_MANURE_LIQUID_PER_CROP_PER_COUNTRY, TOTAL_MANURE_SOLID_PER_CROP_PER_COUNTRY
from defaultTables import IFA_MINERAL_FERTILISER_PER_CROP_PER_COUNTRY as IFA, MANURE_LIQUID_N_FRACTION_PER_COUNTRY
from models.manuremodel import ManureModel, LiquidManureType

FIELDS = {"n": "nitrogen_from_mineral_fert", "p2o5": "p2O5_from_mineral_fert", "k2o": "k2O_from_mineral_fert"}
CASES = [("cotton", "IN"), ("grape", "FR"), ("cassava", "TH"), ("chilli", "CN"), ("blueberry", "US"),
         ("raspberry", "CS")]


def _defaults(**inputs):
    return DefaultValuesWrapper(inputs, DEFAULTS_VALUES_GENERATORS)


def _available_n(defaults):
    """Available N (GRUDAF Nverf) of the default manure [kg N/ha]: (liquid, solid)."""
    liquid = ManureModel.mix_content(defaults["liquid_manure_quantities"], "n_available")
    solid = ManureModel.mix_content(defaults["solid_manure_quantities"], "n_available")
    return liquid * defaults["liquid_manure_part_before_dilution"], solid / 1000.0


def _organic_per_mineral_n():
    mineral_share = dataloader.param("mineral_n_share_of_n_uptake")
    return (1.0 - mineral_share) / mineral_share


@pytest.mark.parametrize("crop, country", CASES)
def test_available_n_is_the_wfldb_organic_share_of_the_mineral_n(crop, country):
    defaults = _defaults(crop=crop, country=country)
    liquid, solid = _available_n(defaults)
    assert _organic_per_mineral_n() == pytest.approx(0.25)
    assert liquid + solid == pytest.approx(0.25 * defaults["nitrogen_from_mineral_fert"])
    assert liquid / (liquid + solid) == pytest.approx(MANURE_LIQUID_N_FRACTION_PER_COUNTRY[country])


@pytest.mark.parametrize("crop, country", CASES)
def test_mineral_fertilisers_at_the_default_yield_stay_the_ifa_rates(crop, country):
    # k = (IFA rate + default manure) / default yield (L33, L34): the manure comes on top of the IFA rate
    defaults = _defaults(crop=crop, country=country)
    for nutrient, field in FIELDS.items():
        assert defaults[field] == pytest.approx(IFA[crop][country][nutrient])


def test_manure_and_mineral_fertilisers_follow_the_yield():
    reference = _defaults(crop="cotton", country="IN")
    defaults = _defaults(crop="cotton", country="IN",
                         yield_main_product_per_crop_cycle=1.5 * reference["yield_main_product_per_crop_cycle"])
    for field in ("total_manureliquid", "total_manuresolid"):
        assert defaults[field] == pytest.approx(1.5 * reference[field])
    for nutrient, field in FIELDS.items():
        assert defaults[field] == pytest.approx(1.5 * IFA["cotton"]["IN"][nutrient])


def test_default_manure_follows_the_default_mineral_n_not_the_template():
    reference = _defaults(crop="grape", country="FR")
    defaults = _defaults(crop="grape", country="FR", nitrogen_from_mineral_fert=10.0)
    for field in ("total_manureliquid", "total_manuresolid"):
        assert defaults[field] == pytest.approx(reference[field])


def test_dilution_and_manure_mix_of_the_template_keep_the_available_n():
    base = _defaults(crop="cotton", country="IN")
    diluted = _defaults(crop="cotton", country="IN", liquid_manure_part_before_dilution=0.25)
    assert diluted["total_manureliquid"] == pytest.approx(2.0 * base["total_manureliquid"])
    pig_only = dict.fromkeys(LiquidManureType, 0.0)
    pig_only[LiquidManureType.pig] = 1.0
    pigs = _defaults(crop="cotton", country="IN", liquid_manure_proportions=pig_only)
    assert _available_n(pigs)[0] == pytest.approx(_available_n(base)[0])


@pytest.mark.parametrize("crop", ["blueberry", "cranberry", "raspberry"])
def test_berries_no_longer_use_the_legacy_manure(crop):
    # legacy GD_crop values of Quantis 2017 without source, e.g. raspberry CS 0 m3 and 20 t
    for country in ("US", "CS", "IN"):
        defaults = _defaults(crop=crop, country=country)
        liquid, solid = _available_n(defaults)
        assert liquid + solid == pytest.approx(0.25 * IFA[crop][country]["n"])
    legacy = TOTAL_MANURE_SOLID_PER_CROP_PER_COUNTRY["raspberry"]["CS"]
    assert legacy == 20000.0 and _defaults(crop="raspberry", country="CS")["total_manuresolid"] < 3000.0


@pytest.mark.parametrize("crop, country", [
    ("coriander", "IN"), ("mint", "MX"), ("lentil", "NZ"), ("cassava", "CI"),  # no IFA N rate
    ("guar", "IN")])  # IFA rate, but no default yield (no reference for the factor)
def test_without_level2_mineral_n_the_legacy_matrix_stays(crop, country):
    defaults = _defaults(crop=crop, country=country, yield_main_product_per_crop_cycle=1000.0)
    for field, legacy in (("total_manureliquid", TOTAL_MANURE_LIQUID_PER_CROP_PER_COUNTRY[crop]),
                          ("total_manuresolid", TOTAL_MANURE_SOLID_PER_CROP_PER_COUNTRY[crop])):
        assert defaults[field] == legacy.get(country, legacy["GLO"]) == 0.0

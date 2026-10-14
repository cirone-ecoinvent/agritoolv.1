"""Decision L34: default mineral N, P2O5 and K2O of the crops without WFLDB level 1 coefficients from the IFA
Fertilizer Use by Crop rates (L33), the nutrient need being taken proportional to the yield: N = IFA rate x yield /
default yield, P2O5 and K2O = max(0, k x yield - manure in use) with k = (IFA rate + default manure) / default yield.
Without an IFA rate the defaults are unchanged (legacy matrix for N, 0 for P and K)."""
import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS, \
    MineralPhosphorusPotassiumDefaultGenerator as PK
from defaultMatrixTotalManure import TOTAL_MANURE_LIQUID_PER_CROP_PER_COUNTRY
from defaultMatrixTotalMineralFert import NITROGEN_FROM_MINERAL_FERT_PER_CROP_PER_COUNTRY
from defaultTables import IFA_MINERAL_FERTILISER_PER_CROP_PER_COUNTRY as IFA, \
    N_UPTAKE_PER_KG_MAIN_PRODUCT_PER_CROP, PK_PER_KG_MAIN_PRODUCT_PER_CROP
from models.manuremodel import LiquidManureType

FIELDS = {"n": "nitrogen_from_mineral_fert", "p2o5": "p2O5_from_mineral_fert", "k2o": "k2O_from_mineral_fert"}
OTHER_CROPS = sorted({r["crop"] for r in dataloader.rows("crop_types.csv")}
                     - set(N_UPTAKE_PER_KG_MAIN_PRODUCT_PER_CROP))


def _defaults(**inputs):
    return DefaultValuesWrapper(inputs, DEFAULTS_VALUES_GENERATORS)


def _manure(defaults, nutrient):
    return PK.balance(defaults, nutrient)[1]


def _scale(country, nutrient):
    row = next(r for r in dataloader.rows("faostat_fertiliser_use_country.csv")
               if r["country"] == country and r["nutrient"] == nutrient)
    return float(row["target_kg_per_ha_cropland"]) / float(row["base_kg_per_ha_cropland"])


def test_the_28_crops_without_level1_coefficients():
    assert len(OTHER_CROPS) == 28
    assert set(PK_PER_KG_MAIN_PRODUCT_PER_CROP) - set(N_UPTAKE_PER_KG_MAIN_PRODUCT_PER_CROP) == {"mint"}


@pytest.mark.parametrize("crop, country", [
    ("cotton", "IN"), ("cotton", "GH"), ("cassava", "TH"), ("chick_pea", "IN"), ("pearl_millet", "GH"),
    ("grape", "ZA"), ("mango", "IN"), ("bellpepper", "ES"), ("blueberry", "US"), ("raspberry", "DE"),
    ("cranberry", "CA")])
def test_default_at_the_default_yield_is_the_ifa_rate(crop, country):
    defaults = _defaults(crop=crop, country=country)
    for nutrient, field in FIELDS.items():
        assert IFA[crop][country][nutrient] is not None
        assert defaults[field] == pytest.approx(IFA[crop][country][nutrient])


def test_exact_crop_before_group():
    cotton = next(r for r in dataloader.rows("ifa_fubc_rates.csv")
                  if r["fubc_country"] == "India" and r["fubc_crop"] == "Cotton")
    assert IFA["cotton"]["IN"]["n"] == pytest.approx(float(cotton["n_kg_per_ha"]) * _scale("IN", "N"))
    # grape: Vineyards in ZA, the fruit group elsewhere; cassava: Cassava in TH, Roots & Tubers in BR (potato only)
    rows = {(r["fubc_country"], r["fubc_crop"]): r for r in dataloader.rows("ifa_fubc_rates.csv")}
    for crop, country, fubc_country, fubc_crop in (("grape", "ZA", "South Africa", "Vineyards"),
                                                   ("grape", "FR", "France", "Fruits & Treenuts"),
                                                   ("cassava", "TH", "Thailand", "Cassava"),
                                                   ("cassava", "BR", "Brazil", "Roots & Tubers")):
        expected = float(rows[(fubc_country, fubc_crop)]["p2o5_kg_per_ha"]) * _scale(country, "P2O5")
        assert IFA[crop][country]["p2o5"] == pytest.approx(expected)


def test_level2_follows_the_yield_and_the_manure_in_use():
    reference = _defaults(crop="cotton", country="IN")
    yield_ref = reference["yield_main_product_per_crop_cycle"]
    assert _manure(reference, "p2o5") == _manure(reference, "k2o") == 0.0  # no default manure
    pig = dict.fromkeys(LiquidManureType, 0.0)
    pig[LiquidManureType.pig] = 1.0
    defaults = _defaults(crop="cotton", country="IN", yield_main_product_per_crop_cycle=1.5 * yield_ref,
                         total_manureliquid=20.0, liquid_manure_proportions=pig, total_manuresolid=0.0)
    # N: the template manure is not used (as for the crops with an N uptake, L28 and L33)
    assert defaults["nitrogen_from_mineral_fert"] == pytest.approx(1.5 * IFA["cotton"]["IN"]["n"])
    assert _manure(defaults, "p2o5") == pytest.approx(35.0)  # 10 m3 undiluted pig slurry (GRUDAF Table 39)
    for nutrient in ("p2o5", "k2o"):
        expected = max(0.0, 1.5 * IFA["cotton"]["IN"][nutrient] - _manure(defaults, nutrient))
        assert defaults[FIELDS[nutrient]] == pytest.approx(expected)


def test_berries_keep_the_legacy_manure():
    reference = _defaults(crop="blueberry", country="US")
    legacy = TOTAL_MANURE_LIQUID_PER_CROP_PER_COUNTRY["blueberry"]
    assert reference["total_manureliquid"] == legacy.get("US", legacy["GLO"])
    manure = _manure(reference, "p2o5")
    assert manure > 0.0
    defaults = _defaults(crop="blueberry", country="US",
                         yield_main_product_per_crop_cycle=2.0 * reference["yield_main_product_per_crop_cycle"])
    # k x 2 x default yield - manure, with k = (IFA rate + manure) / default yield
    assert defaults["p2O5_from_mineral_fert"] == pytest.approx(2.0 * IFA["blueberry"]["US"]["p2o5"] + manure)


@pytest.mark.parametrize("crop, country", [
    ("coriander", "IN"), ("turmeric", "IN"), ("flax", "FR"), ("hemp", "FR"), ("cassava", "CI"), ("mint", "MX"),
    ("lentil", "NZ")])
def test_without_ifa_rate_unchanged(crop, country):
    assert IFA.get(crop, {}).get(country) is None
    defaults = _defaults(crop=crop, country=country)
    legacy = NITROGEN_FROM_MINERAL_FERT_PER_CROP_PER_COUNTRY[crop]
    assert defaults["nitrogen_from_mineral_fert"] == legacy.get(country, legacy["GLO"])
    for nutrient in ("p2o5", "k2o"):
        expected = PK.level1(defaults, nutrient) if crop in PK_PER_KG_MAIN_PRODUCT_PER_CROP else 0.0
        assert defaults[FIELDS[nutrient]] == pytest.approx(expected)


@pytest.mark.parametrize("crop", ["guar", "mulberry", "pomegranate"])
def test_crops_without_default_yield_unchanged(crop):
    # no default yield (0, default_yield.csv), so no reference for the factor, even with an IFA rate (guar: pulses)
    assert _defaults(crop=crop, country="IN")["yield_main_product_per_crop_cycle"] == 0.0
    defaults = _defaults(crop=crop, country="IN", yield_main_product_per_crop_cycle=1000.0)
    assert defaults["nitrogen_from_mineral_fert"] == NITROGEN_FROM_MINERAL_FERT_PER_CROP_PER_COUNTRY[crop]["GLO"]
    assert defaults["p2O5_from_mineral_fert"] == defaults["k2O_from_mineral_fert"] == 0.0
    if crop == "guar":
        assert IFA["guar"]["IN"]["n"] is not None


def test_pulses_only_from_the_pulse_rows():
    names = {r["fubc_crop"] for r in dataloader.rows("ifa_fubc_crop_mapping.csv")
             if {"chick_pea", "lentil", "guar"} & set(r["crops"].split())}
    assert names == {"Pulses", "Pulses (pea, bean)", "Pulses (peas, beans)"}
    assert IFA["lentil"].get("NZ") is None  # UA: pulses of its IFA region (decision L37)
    assert not {"flax", "hemp", "turmeric"} & set(IFA)

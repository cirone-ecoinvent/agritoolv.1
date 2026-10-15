"""Decision L30: the default N uptake of legumes counts only legume_uptake_share (40 %) of the uptake, the rest is
fixed from the air (WFLDB Guidelines v3.0 section 3.9.7.2, Schmid et al. 2000); the default mineral N and manure
follow from it (WFLDB L1: N input = N uptake)."""
import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS, MineralNitrogenDefaultGenerator
from defaultMatrixTotalMineralFert import NITROGEN_FROM_MINERAL_FERT_PER_CROP_PER_COUNTRY
from defaultTables import N_UPTAKE_PER_KG_MAIN_PRODUCT_PER_CROP as N_PER_KG, LEGUME_CROPS, \
    N_UPTAKE_PER_KG_MAIN_PRODUCT_OTHER_CROPS as N_PER_KG_OTHER


def _defaults(**inputs):
    return DefaultValuesWrapper(inputs, DEFAULTS_VALUES_GENERATORS)


def test_legumes_and_share():
    assert LEGUME_CROPS == {"soybean", "peanut", "chick_pea", "lentil", "guar"}
    assert dataloader.param("legume_uptake_share") == 0.4


@pytest.mark.parametrize("crop, country, yield_per_cycle", [("soybean", "BR", 3200.0), ("peanut", "IN", 2000.0)])
def test_legume_inputs_follow_the_share_of_the_uptake(crop, country, yield_per_cycle):
    defaults = _defaults(crop=crop, country=country, yield_main_product_per_crop_cycle=yield_per_cycle)
    uptake = 0.4 * yield_per_cycle * N_PER_KG[crop]
    assert defaults["nitrogen_uptake_by_crop"] == pytest.approx(uptake)
    assert MineralNitrogenDefaultGenerator.level1(defaults) == pytest.approx(0.8 * uptake)  # L2: L33
    # manure per kg of N uptake depends only on the country (L29): same as for a non-legume crop
    wheat = _defaults(crop="wheat", country=country, yield_main_product_per_crop_cycle=5000.0)
    for field in ("total_manureliquid", "total_manuresolid"):
        assert defaults[field] / uptake == pytest.approx(wheat[field] / wheat["nitrogen_uptake_by_crop"])


@pytest.mark.parametrize("crop", ["chick_pea", "guar", "lentil"])
def test_legumes_without_level1_coefficients(crop):
    defaults = _defaults(crop=crop, country="IN", yield_main_product_per_crop_cycle=1000.0)
    assert defaults["nitrogen_uptake_by_crop"] == pytest.approx(0.4 * 1000.0 * N_PER_KG_OTHER[crop])  # decision L41
    # the mineral N does not follow this uptake: IFA pulses rate where there is one (decisions L34, L37), else the
    # legacy matrix (AR: no pulses rate in FUBC, neither in AR nor in the other FUBC 9 countries of Latin America)
    argentina = _defaults(crop=crop, country="AR")
    assert argentina["nitrogen_from_mineral_fert"] == NITROGEN_FROM_MINERAL_FERT_PER_CROP_PER_COUNTRY[crop]["GLO"] == 0.0


def test_other_crops_count_the_whole_uptake():
    defaults = _defaults(crop="castor_beans", country="IN", yield_main_product_per_crop_cycle=1000.0)
    assert defaults["nitrogen_uptake_by_crop"] == pytest.approx(1000.0 * N_PER_KG_OTHER["castor_beans"])

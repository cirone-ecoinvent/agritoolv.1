"""Decision L54: on flooded crops (data/crop_types.csv, rice), urea and AS lose 22 % of the N applied as NH3-N,
for both pH classes (EMEP/EEA 2023 3.D Annex 1, text of the 2019 Guidebook: Yan et al. 2003), instead of
Table 3-2 (L38). The other fertiliser types and the other crops keep Table 3-2."""
import pytest

import dataloader
from models.atomicmass import N_TO_NH3_FACTOR
from models.fertilisermodel import (CaFertiliserType, FertModel, KFertiliserType, NFertiliserType,
                                    PFertiliserType, ZnFertiliserType)

PADDY = 0.22 * N_TO_NH3_FACTOR


def _nh3(crop, n, share_normal_ph=0.5):
    quantities = dict.fromkeys(NFertiliserType, 0.0)
    quantities.update(n)
    return FertModel({
        "n_fertiliser_quantities": quantities,
        "p_fertiliser_quantities": dict.fromkeys(PFertiliserType, 0.0),
        "k_fertiliser_quantities": dict.fromkeys(KFertiliserType, 0.0),
        "ca_fertiliser_quantities": dict.fromkeys(CaFertiliserType, 0.0),
        "zn_fertiliser_quantities": dict.fromkeys(ZnFertiliserType, 0.0),
        "magnesium_from_fertilizer": 0.0,
        "soil_with_ph_under_or_7": share_normal_ph,
        "cultivation_type": "open_ground",
        "crop": crop,
    }).computeNH3()


def test_table_gives_22_percent_for_urea_and_as():
    table = dataloader.table("emep2023_flooded_rice_nh3.csv")
    assert {name: row["nh3_n_pct"] for name, row in table.items()} == {"Urea": 22.0, "AS": 22.0}


def test_rice_is_the_only_flooded_crop():
    flooded = [crop for crop, row in dataloader.table("crop_types.csv", numeric=False).items() if row["flooded"] == "yes"]
    assert flooded == ["rice"]


@pytest.mark.parametrize("fert_type", [NFertiliserType.urea, NFertiliserType.ammonium_sulphate])
@pytest.mark.parametrize("share_normal_ph", [0.0, 0.5, 1.0])
def test_urea_and_as_on_rice(fert_type, share_normal_ph):
    assert _nh3("rice", {fert_type: 100.0}, share_normal_ph) == pytest.approx(100.0 * PADDY)
    assert PADDY == pytest.approx(0.2675, abs=1e-4)


@pytest.mark.parametrize("fert_type", [NFertiliserType.ureaAN, NFertiliserType.di_ammonium_phosphate,
                                       NFertiliserType.ammonium_nitrate])
def test_other_types_on_rice_keep_table_3_2(fert_type):
    assert _nh3("rice", {fert_type: 100.0}) == pytest.approx(_nh3("wheat", {fert_type: 100.0}))


def test_other_crops_keep_table_3_2():
    normal, high = FertModel.nh3_emission_factors(NFertiliserType.urea)
    assert _nh3("wheat", {NFertiliserType.urea: 100.0}) == pytest.approx(100.0 * (0.5 * normal + 0.5 * high))
    assert FertModel.nh3_emission_factors(NFertiliserType.urea, flooded=True) == pytest.approx((PADDY, PADDY))

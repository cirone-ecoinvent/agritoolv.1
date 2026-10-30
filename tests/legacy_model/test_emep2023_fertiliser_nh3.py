"""Decision L38: NH3 after mineral N fertiliser application from EMEP/EEA 2023 3.D Tier 2, Table 3-2
(g NH3 per kg N applied, soils of normal pH <= 7.0 and high pH > 7.0, no climate classes), rows assigned to the
legacy fertiliser types by emep2023_fertiliser_type_mapping.csv; replaces the 2016 factors written in the code."""
import pytest

import dataloader
from models.fertilisermodel import (CaFertiliserType, FertModel, KFertiliserType, NFertiliserType,
                                    PFertiliserType, ZnFertiliserType)

TABLE = "emep2023_3d_table3_2.csv"
MAPPING = "emep2023_fertiliser_type_mapping.csv"


def _model(n, share_normal_ph, cultivation_type="open_ground", crop="wheat"):
    quantities = {member: 0.0 for member in NFertiliserType}
    quantities.update(n)
    return FertModel({
        "n_fertiliser_quantities": quantities,
        "p_fertiliser_quantities": dict.fromkeys(PFertiliserType, 0.0),
        "k_fertiliser_quantities": dict.fromkeys(KFertiliserType, 0.0),
        "ca_fertiliser_quantities": dict.fromkeys(CaFertiliserType, 0.0),
        "zn_fertiliser_quantities": dict.fromkeys(ZnFertiliserType, 0.0),
        "magnesium_from_fertilizer": 0.0,
        "soil_with_ph_under_or_7": share_normal_ph,
        "cultivation_type": cultivation_type,
        "crop": crop,
    })


def test_table_matches_the_nh3_n_shares_of_annex_table_a1_1():
    # g NH3 per kg N = NH3-N % x 17/14 x 10, rounded as printed
    rows = dataloader.rows(TABLE)
    assert len(rows) == 11
    for row in rows:
        for ph in ("normal_ph", "high_ph"):
            if not row["nh3_n_pct_" + ph]:
                assert row["emep_fertiliser_type"] == "Anhydrous ammonia (AH)"
                continue
            derived = round(float(row["nh3_n_pct_" + ph]) * 17.0 / 14.0 * 10.0)
            if row["emep_fertiliser_type"] == "Other straight N compounds" and ph == "normal_ph":
                assert (float(row["ef_" + ph]), derived) == (24.0, 84)  # probable misprint, noted in the row
                continue
            assert float(row["ef_" + ph]) == pytest.approx(derived, abs=1.0), row


def test_every_n_fertiliser_type_is_mapped_and_signed():
    mapping = dataloader.table(MAPPING, numeric=False)
    table = dataloader.table(TABLE)
    assert set(mapping) == {member.value for member in NFertiliserType}
    for key, row in mapping.items():
        assert row["emep_fertiliser_type"] in table, key
        assert row["status"] == "confirmed" and row["reviewed_by"], key
    assert "Other straight N compounds" not in {row["emep_fertiliser_type"] for row in mapping.values()}


@pytest.mark.parametrize("fert_type, normal_ph, high_ph", [
    (NFertiliserType.ammonium_nitrate, 24, 52),
    (NFertiliserType.urea, 195, 206),
    (NFertiliserType.ureaAN, 87, 161),  # N solutions
    (NFertiliserType.mono_ammonium_phosphate, 84, 187),  # AP
    (NFertiliserType.di_ammonium_phosphate, 84, 187),  # AP
    (NFertiliserType.an_phosphate, 84, 187),  # NP mixtures
    (NFertiliserType.lime_ammonium_nitrate, 24, 52),  # CAN
    (NFertiliserType.ammonium_sulphate, 84, 187),
    (NFertiliserType.potassium_nitrate, 24, 52),  # NK mixtures
    (NFertiliserType.ammonia_liquid, 20, 20)])  # anhydrous ammonia
def test_emission_factors_per_type(fert_type, normal_ph, high_ph):
    assert FertModel.nh3_emission_factors(fert_type) == pytest.approx((normal_ph / 1000.0, high_ph / 1000.0))


def test_nh3_is_the_ph_weighted_sum_in_kg_nh3():
    model = _model({NFertiliserType.urea: 100.0, NFertiliserType.ammonium_sulphate: 50.0}, 0.8)
    expected = 100.0 * (0.8 * 0.195 + 0.2 * 0.206) + 50.0 * (0.8 * 0.084 + 0.2 * 0.187)
    assert model.computeNH3() == pytest.approx(expected)


def test_hydroponic_greenhouses_count_as_normal_ph():
    model = _model({NFertiliserType.ammonium_sulphate: 100.0}, 0.0, "greenhouse_hydroponic_heated")
    assert model.computeNH3() == pytest.approx(100.0 * 0.084)
    assert _model({NFertiliserType.ammonium_sulphate: 100.0}, 0.0).computeNH3() == pytest.approx(100.0 * 0.187)

"""Decision L63: default clay, organic carbon, pH share and erodibility K from the Harmonized World Soil Database v2.0,
averaged over the SPAM 2020 V2r2 physical area of the crop in the country (scripts/build_hwsd_soil.py), replacing the
WFLDB 2017 country values (L22, L26, L27)."""
import csv

import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS

TABLE = "hwsd2_soil.csv"


def _row(crop, country):
    with open(dataloader.data_path(TABLE), newline="", encoding="utf-8") as f:
        return next(r for r in csv.DictReader(f) if r["crop"] == crop and r["country"] == country)


def _defaults(**inputs):
    return DefaultValuesWrapper(inputs, DEFAULTS_VALUES_GENERATORS)


def test_table_covers_every_crop_and_country():
    crops = {row["crop"] for row in dataloader.rows("crop_types.csv")} | {"all_crops"}
    countries = {row["country"] for row in dataloader.rows("faostat_country_mapping.csv")} - {"GLO"}
    rows = dataloader.rows(TABLE)
    assert {(r["crop"], r["country"]) for r in rows} == {(c, k) for c in crops for k in countries}
    assert all(float(r["coverage"]) > 0.97 for r in rows)


def test_values_are_in_range():
    for r in dataloader.rows(TABLE):
        assert float(r["clay_pct"]) + float(r["silt_pct"]) + float(r["sand_pct"]) == pytest.approx(100.0, abs=1.0)
        assert 0.0 < float(r["org_carbon_0_50_pct"]) < 20.0
        assert 0.0 <= float(r["ph_le7_share"]) <= 1.0 and 3.5 < float(r["ph_water"]) < 9.5
        assert 0.005 < float(r["k_lanca"]) < 0.06 and 0.005 < float(r["k_renard"]) < 0.06


@pytest.mark.parametrize("crop, country", [("wheat", "IT"), ("rice", "IN"), ("apple", "FR"), ("coffee_arabica", "BR")])
def test_defaults_are_the_crop_row(crop, country):
    row, defaults = _row(crop, country), _defaults(crop=crop, country=country)
    assert defaults["clay_content"] == pytest.approx(float(row["clay_pct"]) / 100.0)
    assert defaults["organic_carbon_content"] == pytest.approx(float(row["org_carbon_0_50_pct"]) / 100.0)
    assert defaults["soil_with_ph_under_or_7"] == float(row["ph_le7_share"])
    assert defaults["soil_erodibility_factor"] == float(row["k_lanca"])


def test_crop_without_spam_area_uses_all_crops():
    row = _row("wheat", "ID")
    assert row["weights"] == "all_crops"
    assert row["k_lanca"] == _row("all_crops", "ID")["k_lanca"]


def test_countries_outside_wfldb_get_soil_values():
    # MA and CS had no WFLDB soil types and kept a legacy texture lookup for K (L27)
    for country in ("MA", "CS"):
        assert _defaults(crop="wheat", country=country)["soil_erodibility_factor"] == float(_row("wheat", country)["k_lanca"])


def test_permeability_classes_cover_the_usda_texture_classes_of_hwsd():
    rows = dataloader.rows("lanca2016_permeability_classes.csv")
    assert [int(r["texture_usda_code"]) for r in rows] == list(range(1, 14))
    assert all(1 <= int(r["permeability_class"]) <= 6 and r["status"] == "confirmed" and r["reviewed_by"] == "FC"
               for r in rows)


def test_stoniness_factors_of_lanca_table_5():
    rows = dataloader.rows("lanca2016_stoniness_factors.csv")
    assert [float(r["stoniness_factor"]) for r in rows] == [1.0, 1.0, 1.0, 0.74, 0.332, 0.074]
    assert [float(r["coarse_max_pct"]) for r in rows] == [0.0, 5.0, 15.0, 40.0, 80.0, 100.0]


def test_k_parameters_are_signed():
    rows = {r["parameter"]: r for r in dataloader.rows("hwsd_k_factor_parameters.csv")}
    assert float(rows["very_fine_sand_share_of_sand"]["value"]) == 0.0  # FC: lower bound of the LANCA M factor
    assert all(r["status"] == "confirmed" and r["reviewed_by"] == "FC" for r in rows.values())

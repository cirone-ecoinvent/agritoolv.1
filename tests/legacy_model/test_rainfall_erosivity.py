"""Decision L60: rainfall erosivity R from the GloREDa monthly maps, summed to the year and averaged over the SPAM 2020
V2r2 physical area of the crop in the country (scripts/build_gloreda_erosivity.py), replacing the LANCA equations of the
climate zones."""
import csv

import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS
from models.erosionmodel import ErosionModel, TillageMethod, AntiErosionPractice

TABLE = "gloreda2023_rainfall_erosivity.csv"


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
    assert all(float(r["r_factor_mj_mm_per_ha_h_yr"]) > 0.0 and float(r["coverage"]) > 0.99 for r in rows)


def test_every_crop_has_a_signed_spam_crop():
    rows = dataloader.rows("spam2020_crop_mapping.csv")
    spam = {r["spam_crop"] for r in dataloader.rows("spam2020_crops.csv")}
    assert {r["crop"] for r in rows} == {r["crop"] for r in dataloader.rows("crop_types.csv")}
    assert all(r["spam2020_crop"] in spam and r["status"] == "confirmed" and r["reviewed_by"] == "FC" for r in rows)


def test_spam_mapping_follows_mapspamc():
    # rule "mapspamc": the SPAM crop of the FAOSTAT item in the faostat2crop table of the mapspamc R package
    mapspamc = {r["faostat_item_code"]: r["spam_crop"] for r in dataloader.rows("mapspamc_faostat_spam_crops.csv")}
    for row in dataloader.rows("spam2020_crop_mapping.csv"):
        if row["rule"] == "mapspamc":
            assert mapspamc[row["faostat_item_code"]] == row["spam2020_crop"], row["crop"]


@pytest.mark.parametrize("crop, country", [("wheat", "IT"), ("rice", "IN"), ("apple", "FR"), ("almond", "ES")])
def test_default_is_the_crop_row(crop, country):
    row = _row(crop, country)
    assert _defaults(crop=crop, country=country)["rainfall_erosivity"] == float(row["r_factor_mj_mm_per_ha_h_yr"])


def test_crop_without_spam_area_uses_all_crops():
    row = _row("wheat", "ID")
    assert row["weights"] == "all_crops"
    assert row["r_factor_mj_mm_per_ha_h_yr"] == _row("all_crops", "ID")["r_factor_mj_mm_per_ha_h_yr"]


def test_eroded_soil_is_proportional_to_r():
    values = {"rainfall_erosivity": 1000.0, "slope": 0.03, "slope_length": 50.0,
              "tillage_method": TillageMethod.unknown, "anti_erosion_practice": AntiErosionPractice.no_practice,
              "soil_erodibility_factor": 0.03, "crop_factor": 0.2}
    reference = ErosionModel(values).compute()["m_Erosion_eroded_soil"]
    values["rainfall_erosivity"] = 2500.0
    assert ErosionModel(values).compute()["m_Erosion_eroded_soil"] == pytest.approx(2.5 * reference)

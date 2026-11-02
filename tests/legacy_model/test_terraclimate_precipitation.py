"""Decision L61: default annual precipitation from the TerraClimate monthly climatology 1991-2020, summed to the year
and averaged over the SPAM 2020 V2r2 physical area of the crop in the country (scripts/build_terraclimate_climate.py),
replacing the WFLDB 2017 country values."""
import csv

import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS

TABLE = "terraclimate1991_2020_climate.csv"


def _row(crop, country):
    with open(dataloader.data_path(TABLE), newline="", encoding="utf-8") as f:
        return next(r for r in csv.DictReader(f) if r["crop"] == crop and r["country"] == country)


def _defaults(**inputs):
    values = {"cultivation_type": "open_ground"}
    values.update(inputs)
    return DefaultValuesWrapper(values, DEFAULTS_VALUES_GENERATORS)


def test_table_covers_every_crop_and_country():
    crops = {row["crop"] for row in dataloader.rows("crop_types.csv")} | {"all_crops"}
    countries = {row["country"] for row in dataloader.rows("faostat_country_mapping.csv")} - {"GLO"}
    rows = dataloader.rows(TABLE)
    assert {(r["crop"], r["country"]) for r in rows} == {(c, k) for c in crops for k in countries}
    assert all(float(r["annual_precipitation_mm"]) > 0.0 and float(r["coverage"]) > 0.99 for r in rows)


@pytest.mark.parametrize("crop, country", [("wheat", "IT"), ("rice", "IN"), ("apple", "FR"), ("cotton", "PE")])
def test_default_is_the_crop_row(crop, country):
    row = _row(crop, country)
    assert _defaults(crop=crop, country=country)["average_annual_precipitation"] == float(row["annual_precipitation_mm"])


def test_crop_without_spam_area_uses_all_crops():
    row = _row("wheat", "ID")
    assert row["weights"] == "all_crops"
    assert row["annual_precipitation_mm"] == _row("all_crops", "ID")["annual_precipitation_mm"]


def test_no_precipitation_outside_open_ground():
    assert _defaults(crop="tomato_fresh", country="NL", cultivation_type="greenhouse_hydroponic")["average_annual_precipitation"] == 0.0


def test_precipitation_per_crop_cycle_follows_the_annual_value():
    defaults = _defaults(crop="wheat", country="CH")
    assert defaults["precipitation_per_crop_cycle"] == pytest.approx(
        float(_row("wheat", "CH")["annual_precipitation_mm"]) * 10.0 / defaults["crop_cycle_per_year"])

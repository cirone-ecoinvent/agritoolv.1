"""Decision L62: default support-practice factor P of the EU from the map of Panagos et al. (2015b) (contouring, stone
walls, grass margins), averaged over the SPAM 2020 V2r2 physical area of the crop in the country
(scripts/build_panagos_p_factor.py), used by the erosion model when the practice has no AH 537 factor; 1 elsewhere."""
import csv

import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS
from models.erosionmodel import ErosionModel, TillageMethod, AntiErosionPractice

TABLE = "panagos2015b_p_factor.csv"
EU_COUNTRIES = {"BE", "DE", "ES", "FI", "FR", "HU", "IT", "NL", "PL"}

# Panagos et al. (2015b) Table 6, P-factor per country (mean over the whole country; cross-check only)
TABLE_6 = {"BE": 0.9465, "DE": 0.9782, "ES": 0.9293, "FI": 0.9942, "FR": 0.9627, "HU": 0.9840, "IT": 0.9519,
           "NL": 0.9561, "PL": 0.9781}


def _row(crop, country):
    with open(dataloader.data_path(TABLE), newline="", encoding="utf-8") as f:
        return next(r for r in csv.DictReader(f) if r["crop"] == crop and r["country"] == country)


def _defaults(**inputs):
    return DefaultValuesWrapper(inputs, DEFAULTS_VALUES_GENERATORS)


def _erosion(practice, support_practice_factor):
    return ErosionModel({"rainfall_erosivity": 1000.0, "slope": 0.03, "slope_length": 50.0,
                         "tillage_method": TillageMethod.unknown, "anti_erosion_practice": practice,
                         "soil_erodibility_factor": 0.03, "crop_factor": 0.2,
                         "support_practice_factor": support_practice_factor})


def test_table_covers_every_crop_and_country():
    crops = {row["crop"] for row in dataloader.rows("crop_types.csv")} | {"all_crops"}
    countries = {row["country"] for row in dataloader.rows("faostat_country_mapping.csv")} - {"GLO"}
    rows = dataloader.rows(TABLE)
    assert {(r["crop"], r["country"]) for r in rows} == {(c, k) for c in crops for k in countries}


def test_values_only_in_the_eu():
    rows = dataloader.rows(TABLE)
    assert {r["country"] for r in rows if r["p_factor"]} == EU_COUNTRIES
    assert all(0.0 < float(r["p_factor"]) <= 1.0 and float(r["coverage"]) > 0.9 for r in rows if r["p_factor"])


@pytest.mark.parametrize("country", sorted(EU_COUNTRIES))
def test_country_value_close_to_table_6(country):
    # the crop area weighting gives slightly lower values than the country means of Table 6 (P = 0.95 on agricultural
    # land against 0.9702 over the EU-28 in Panagos et al. 2015b)
    p_factor = float(_row("all_crops", country)["p_factor"])
    assert TABLE_6[country] * 0.96 < p_factor <= TABLE_6[country] * 1.001


@pytest.mark.parametrize("crop, country", [("wheat", "IT"), ("apple", "FR"), ("almond", "ES"), ("oat", "BE")])
def test_default_is_the_crop_row(crop, country):
    assert _defaults(crop=crop, country=country)["support_practice_factor"] == float(_row(crop, country)["p_factor"])


@pytest.mark.parametrize("country", ["IN", "CH", "US", "TR"])
def test_default_is_one_outside_the_eu(country):
    assert _defaults(crop="wheat", country=country)["support_practice_factor"] == 1.0


@pytest.mark.parametrize("practice", [AntiErosionPractice.unknown, AntiErosionPractice.no_practice,
                                      AntiErosionPractice.cross_slope, AntiErosionPractice.strip_cropping_cross_slope])
def test_practice_without_ah537_factor_uses_the_default(practice):
    assert _erosion(practice, 0.93)._compute_practice_factor() == 0.93


@pytest.mark.parametrize("practice", [AntiErosionPractice.contour_farming, AntiErosionPractice.strip_cropping_contour,
                                      AntiErosionPractice.terraces])
def test_practice_with_ah537_factor_ignores_the_default(practice):
    assert _erosion(practice, 0.93)._compute_practice_factor() == _erosion(practice, 1.0)._compute_practice_factor()


def test_eroded_soil_is_proportional_to_the_default():
    reference = _erosion(AntiErosionPractice.unknown, 1.0).compute()["m_Erosion_eroded_soil"]
    assert _erosion(AntiErosionPractice.unknown, 0.93).compute()["m_Erosion_eroded_soil"] == pytest.approx(0.93 * reference)

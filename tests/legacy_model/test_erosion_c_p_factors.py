"""Decision L59: C = C_crop x C_tillage of Panagos et al. (2015a), with C_crop from Panagos Table 1 or from the crop
groups of Borrelli et al. (2017), and P from USDA Agriculture Handbook 537, Tables 13-15, by practice and slope class."""
import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS
from models.erosionmodel import ErosionModel, TillageMethod, AntiErosionPractice


def _defaults(**inputs):
    return DefaultValuesWrapper(inputs, DEFAULTS_VALUES_GENERATORS)


def _erosion(**inputs):
    values = {"average_annual_precipitation": 800.0, "slope": 0.03, "slope_length": 50.0,
              "tillage_method": TillageMethod.unknown, "anti_erosion_practice": AntiErosionPractice.no_practice,
              "soil_erodibility_factor": 0.03, "crop_factor": 0.2, "mean_elevation_m": 700,
              "nb_wet_days_per_year": 180, "climate_zone_specific": "warm_summer_dry_warm"}
    values.update(inputs)
    return ErosionModel(values)


def test_every_crop_has_a_signed_c_mapping():
    crops = {row["crop"] for row in dataloader.rows("crop_types.csv")}
    mapping = dataloader.rows("erosion_crop_c_factor_mapping.csv")
    assert {row["crop"] for row in mapping} == crops
    assert all(row["status"] == "confirmed" and row["reviewed_by"] == "FC" for row in mapping)


@pytest.mark.parametrize("crop, c_crop", [
    ("wheat", 0.20),        # Panagos Table 1, common wheat and spelt
    ("maizegrain", 0.38),   # Panagos, grain maize
    ("rice", 0.15),         # Panagos, rice
    ("lentil", 0.32),       # Panagos, dried pulses
    ("cotton", 0.50),       # Panagos, cotton seed (Borrelli sub-group cotton would give 0.40)
    ("oat", 0.20),          # Borrelli group 1, various
    ("sweetcorn", 0.38),    # Borrelli group 1, maize
    ("tomato_fresh", 0.25),  # Borrelli group 4
    ("grape", 0.35),        # Borrelli group 9, grapes
    ("coffee_arabica", 0.20),  # Borrelli group 13, coffee
    ("strawberry_fresh", 0.20),  # Borrelli group 12, strawberries
    ("hemp", 0.15),         # Borrelli: FAOSTAT 777 in group 13
    ("apple", 0.15)])       # Borrelli group 14
def test_default_crop_factor(crop, c_crop):
    assert _defaults(crop=crop, country="FR")["crop_factor"] == pytest.approx(c_crop)


@pytest.mark.parametrize("tillage, c_tillage", [
    (TillageMethod.unknown, 1.0), (TillageMethod.fall_plaw, 1.0), (TillageMethod.spring_plow, 1.0),
    (TillageMethod.mulch_tillage, 0.35), (TillageMethod.ridge_tillage, 0.35), (TillageMethod.zone_tillage, 0.35),
    (TillageMethod.no_till, 0.25)])
def test_tillage_factor(tillage, c_tillage):
    assert _erosion(tillage_method=tillage)._compute_tillage_factor() == c_tillage


@pytest.mark.parametrize("practice, slope_pct, p_value", [
    (AntiErosionPractice.unknown, 3, 1.0),
    (AntiErosionPractice.no_practice, 3, 1.0),
    (AntiErosionPractice.cross_slope, 3, 1.0),
    (AntiErosionPractice.strip_cropping_cross_slope, 3, 1.0),
    (AntiErosionPractice.contour_farming, 0.5, 0.6),  # under 1 %: class 1-2
    (AntiErosionPractice.contour_farming, 2, 0.6),
    (AntiErosionPractice.contour_farming, 2.5, 0.5),  # between 2 and 3: class 3-5
    (AntiErosionPractice.contour_farming, 3, 0.5),
    (AntiErosionPractice.contour_farming, 8.5, 0.6),  # class 9-12
    (AntiErosionPractice.contour_farming, 25, 0.9),
    (AntiErosionPractice.contour_farming, 26, 1.0),   # above the tables
    (AntiErosionPractice.strip_cropping_contour, 3, 0.38),  # Table 14, system B
    (AntiErosionPractice.strip_cropping_contour, 14, 0.52),
    (AntiErosionPractice.terraces, 3, 0.5),            # Table 15, farm planning, contour factor, 3-8 %
    (AntiErosionPractice.terraces, 18, 0.8)])
def test_practice_factor(practice, slope_pct, p_value):
    assert _erosion(anti_erosion_practice=practice, slope=slope_pct / 100.0)._compute_practice_factor() == p_value


def test_eroded_soil_is_proportional_to_c_and_p():
    reference = _erosion().compute()["m_Erosion_eroded_soil"]
    changed = _erosion(tillage_method=TillageMethod.no_till,
                       anti_erosion_practice=AntiErosionPractice.contour_farming).compute()["m_Erosion_eroded_soil"]
    assert changed == pytest.approx(reference * 0.25 * 0.5)

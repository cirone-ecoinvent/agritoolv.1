"""Fix F7: flooded rice gets land occupation and transformation like every other crop, with the
ecoinvent flooded-crop flows. Reference: reference_models.land_occupation_m2a."""
import pytest

import dataloader
from models.lucmodel import LUCModel
from outputMapping import OutputMapping


def test_rice_is_an_annual_flooded_crop():
    row = dataloader.table("crop_types.csv", numeric=False)["rice"]
    assert row["crop_type"] == "annual" and row["flooded"] == "yes"
    assert LUCModel({"crop": "rice", "country": "IN", "crop_cycle_per_year": 1.0}).compute()["m_LUC_luc_crop_type"] == "annual"


def test_only_rice_is_flooded():
    flooded = [c for c, r in dataloader.table("crop_types.csv", numeric=False).items() if r["flooded"] == "yes"]
    assert flooded == ["rice"]


def _occupation(crop, cycles=1.0, water=0.0):
    om = OutputMapping()
    luc = LUCModel({"crop": crop, "country": "IN", "crop_cycle_per_year": cycles}).compute()
    om.mapLucModel(luc, {"crop": crop, "crop_cycle_per_year": cycles, "water_use_total": water,
                         "cultivation_type": "open_ground", "organic_certified": "no",
                         "orchard_lifetime": 20.0})
    return om.output


def test_rice_occupation_and_transformation_flooded():
    out = _occupation("rice", cycles=2.4, water=8000.0)
    assert out["occupation_annual_flooded"] == pytest.approx(10000.0 / 2.4)  # m2*year, 5 months
    assert out["transformation_from_annual_flooded"] == 10000.0
    assert out["transformation_to_annual_flooded"] == 10000.0
    assert not [k for k in out if k.endswith("_irr") or k.endswith("non-irr")]


def test_other_crops_unchanged():
    out = _occupation("wheat", cycles=1.0, water=0.0)
    assert out["occupation_annual_non-irr"] == pytest.approx(10000.0)
    assert "occupation_annual_flooded" not in out

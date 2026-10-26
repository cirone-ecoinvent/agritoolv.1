"""Decision L51: greenhouse and plastic tunnel. The ecoinvent products 'greenhouse, glass walls and roof',
'greenhouse, plastic walls and roof' (m2*year) and 'plastic tunnel' (m2) stand for 1 m2 used over 1 year; the amount
per ha and crop cycle is the m2 of infrastructure of the template / crop cycles per year, like the land occupation."""
import pytest

import dataloader
from outputMapping import OutputMapping

FIELDS = ("greenhouse_plastic_tunnel", "greenhouse_glass_roof", "greenhouse_plastic_roof")


def _inputs(crop, cycles, area, **extra):
    inputs = {"country": "ES", "crop": crop, "crop_cycle_per_year": cycles, "yield_main_product_per_crop_cycle": 1.0,
              "yield_BP1_per_crop_cycle": 0.0, "yield_BP2_per_crop_cycle": 0.0, "yield_BP3_per_crop_cycle": 0.0,
              "yield_main_product_dry_per_crop_cycle": 1.0}
    inputs.update({field: area for field in FIELDS})
    inputs.update(extra)
    return inputs


def _greenhouse(inputs):
    om = OutputMapping()
    om.mapAsIsOutput(inputs)
    return {field: om.output[field] for field in FIELDS}


@pytest.mark.parametrize("cycles", [1.0, 2.0, 0.5])
def test_greenhouse_is_area_times_years_of_the_crop_cycle(cycles):
    out = _greenhouse(_inputs("tomato_fresh", cycles, 10000.0))
    assert out == {field: pytest.approx(10000.0 / cycles) for field in FIELDS}


def test_greenhouse_equals_the_land_occupation_when_it_covers_the_hectare():
    # as in the ecoinvent 3.12 tomato and strawberry datasets: greenhouse m2*year = occupation m2*year
    occupation = 10000.0 / 1.5
    assert _greenhouse(_inputs("strawberry_fresh", 1.5, 10000.0))["greenhouse_plastic_roof"] == pytest.approx(occupation)


def test_greenhouse_does_not_depend_on_the_orchard_lifetime():
    short = _greenhouse(_inputs("raspberry", 1.0, 2000.0, orchard_lifetime=8.0))
    long_ = _greenhouse(_inputs("raspberry", 1.0, 2000.0, orchard_lifetime=25.0))
    assert short == long_ == {field: pytest.approx(2000.0) for field in FIELDS}


def test_no_legacy_greenhouse_parameter_left():
    assert "orchard_lifetime_other_crops" not in dataloader.table("model_parameters.csv", numeric=False)

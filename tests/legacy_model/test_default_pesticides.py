"""Decisions L25, L43 and L48: default total pesticides per crop and country (g a.i./ha). The crops of the Global atlas
of pesticide use from data/atlas2026_pesticides_country.csv (test_atlas_pesticides.py), with the WFLDB 3.1
Documentation 2017 as fallback; the other crops with WFLDB 2017 datasets from that documentation
(test_wfldb2017_pesticides.py); the rest from data/default_pesticides.csv (legacy)."""
import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS
from defaultMatrixTotalPesticides import TOTAL_PESTICIDES_PER_CROP_PER_COUNTRY as PESTICIDES


def _default(**inputs):
    return DefaultValuesWrapper(inputs, DEFAULTS_VALUES_GENERATORS)["pest_total"]


def test_every_crop_has_a_glo_value():
    assert set(PESTICIDES) == set(dataloader.table("crop_types.csv", numeric=False))
    assert all("GLO" in table for table in PESTICIDES.values())


def test_potato_uses_the_atlas_and_the_wfldb_documentation_as_fallback():
    # atlas, kg a.i./ha: US 90.44 (soil fumigants 82 %), CN 3.39, IN 2.74; RU and UA below the range of the
    # tool countries (atlas2026_pesticides_review.csv): WFLDB 2017 (L25) 0.87 (L1) and 1.91 (L1)
    assert {country: PESTICIDES["potato"][country] for country in ("US", "CN", "IN", "RU", "UA")} == pytest.approx(
        {"US": 90440.8, "CN": 3387.45, "IN": 2741.88, "RU": 870.0, "UA": 1910.0})


def test_potato_in_a_country_without_value_uses_glo():
    assert "VN" not in PESTICIDES["potato"]
    assert _default(crop="potato", country="VN") == pytest.approx(6060.83)  # WFLDB 2017 GLO: 1635

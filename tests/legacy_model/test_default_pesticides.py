"""Decisions L25 and L43: default total pesticides per crop and country (g a.i./ha). Potato and the
other crops of data/wfldb2017_pesticides_crop_mapping.csv from the WFLDB 3.1 Documentation 2017
(test_wfldb2017_pesticides.py), the rest from data/default_pesticides.csv (legacy)."""
import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS
from defaultMatrixTotalPesticides import TOTAL_PESTICIDES_PER_CROP_PER_COUNTRY as PESTICIDES


def _default(**inputs):
    return DefaultValuesWrapper(inputs, DEFAULTS_VALUES_GENERATORS)["pest_total"]


def test_every_crop_has_a_glo_value():
    assert set(PESTICIDES) == set(dataloader.table("crop_types.csv", numeric=False))
    assert all("GLO" in table for table in PESTICIDES.values())


def test_potato_uses_the_wfldb_documentation():
    # sheet '2a) Main inputs_Arable', row 19, kg a.i./ha: CN 2.76 (L1), IN 1 (L3), RU 0.87 (L1), UA 1.91 (L1)
    assert PESTICIDES["potato"] == pytest.approx({"CN": 2760.0, "IN": 1000.0, "RU": 870.0, "UA": 1910.0,
                                                  "GLO": (2760.0 + 1000.0 + 870.0 + 1910.0) / 4})


def test_potato_in_a_country_without_wfldb_value_uses_glo():
    assert _default(crop="potato", country="US") == pytest.approx(1635.0)

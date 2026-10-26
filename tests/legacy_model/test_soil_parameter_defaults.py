"""Decision L52: the soil constants of the SQCB nitrate model are read from data/model_parameters.csv
(before: the same values hardcoded in defaultGeneration.py)."""
import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS


@pytest.mark.parametrize("field, parameter, value", [
    ("considered_soil_volume", "soil_volume_m3", 5000.0),
    ("bulk_density_of_soil", "bulk_density_kg_m3", 1300.0),
    ("c_per_n_ratio", "soil_cn_ratio", 11.0),
    ("norg_per_ntotal_ratio", "norg_ntot_ratio", 0.85),
])
def test_soil_defaults_are_the_model_parameters(field, parameter, value):
    defaults = DefaultValuesWrapper(dict(crop="wheat", country="FR"), DEFAULTS_VALUES_GENERATORS)
    assert defaults[field] == dataloader.param(parameter) == value


def test_template_value_is_kept():
    defaults = DefaultValuesWrapper(dict(crop="wheat", country="FR", bulk_density_of_soil=1450.0),
                                    DEFAULTS_VALUES_GENERATORS)
    assert defaults["bulk_density_of_soil"] == 1450.0

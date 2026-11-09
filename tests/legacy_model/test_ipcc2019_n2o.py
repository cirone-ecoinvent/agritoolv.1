"""Decision L64: N2O factors of the IPCC 2019 Refinement Vol. 4 Tables 11.1 and 11.3 (ipcc2019_n2o_emission_factors.csv)
disaggregated by wet and dry climate, weighted by the share of the crop area in a wet climate
(ipcc_climate_wet_share.csv, built by scripts/build_ipcc_climate_wet_share.py from CRU TS 4.10 1991-2020)."""
import csv

import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS
from models.atomicmass import NH3_TO_N_FACTOR, N_TO_N2O_FACTOR
from models.nmodel import NModel
from test_fix_f2_n2o import BASE_INPUTS

TABLE = "ipcc_climate_wet_share.csv"
FACTORS = "ipcc2019_n2o_emission_factors.csv"

# Table 11.1 (Updated) p. 11.13 and Table 11.3 (Updated) p. 11.26: value, uncertainty range
PUBLISHED = {
    "ef1_aggregated": (0.010, 0.002, 0.018),
    "ef1_synthetic_wet": (0.016, 0.013, 0.019),
    "ef1_other_wet": (0.006, 0.001, 0.011),
    "ef1_dry": (0.005, 0.000, 0.011),
    "ef1fr_aggregated": (0.004, 0.000, 0.029),
    "ef1fr_continuous_flooding": (0.003, 0.000, 0.010),
    "ef1fr_drainage": (0.005, 0.000, 0.016),
    "ef4_aggregated": (0.010, 0.002, 0.018),
    "ef4_wet": (0.014, 0.011, 0.017),
    "ef4_dry": (0.005, 0.000, 0.011),
    "ef5_leaching": (0.011, 0.000, 0.020),
}


def _model(**overrides):
    inputs = dict(BASE_INPUTS)
    inputs.update(overrides)
    return NModel(inputs)


def _row(crop, country):
    with open(dataloader.data_path(TABLE), newline="", encoding="utf-8") as f:
        return next(r for r in csv.DictReader(f) if r["crop"] == crop and r["country"] == country)


def test_factor_table_is_the_published_one():
    rows = {r["parameter"]: r for r in dataloader.rows(FACTORS)}
    assert {name: (float(r["value"]), float(r["uncertainty_low"]), float(r["uncertainty_high"]))
            for name, r in rows.items()} == PUBLISHED
    assert all(r["source_table"] == ("Table 11.1 (Updated)" if r["page"] == "11.13" else "Table 11.3 (Updated)")
               for r in rows.values())


def test_ipcc2006_factors_are_gone_from_model_parameters():
    names = set(dataloader.params())
    assert not names & {"ef1_direct_n2o", "ef1_flooded_rice", "ef4_volatilisation", "ef5_leaching"}


@pytest.mark.parametrize("share, synthetic, other", [(1.0, 0.016, 0.006), (0.0, 0.005, 0.005),
                                                      (0.25, 0.25 * 0.016 + 0.75 * 0.005, 0.25 * 0.006 + 0.75 * 0.005)])
def test_direct_factor_by_climate_and_n_input(share, synthetic, other):
    model = _model(wet_climate_share=share)
    assert model._compute_direct_n2o_as_n(100.0, 0.0, None) == pytest.approx(synthetic * 100.0)
    assert model._compute_direct_n2o_as_n(0.0, 100.0, None) == pytest.approx(other * 100.0)


@pytest.mark.parametrize("share, ef4", [(1.0, 0.014), (0.0, 0.005), (0.4, 0.4 * 0.014 + 0.6 * 0.005)])
def test_volatilisation_factor_by_climate(share, ef4):
    # 17 kg NH3, no NOx, no leaching
    n2o = _model(wet_climate_share=share)._compute_n2o_total(0.0, 0.0, 17.0, 0.0, 0.0, ef1fr=None)
    assert n2o == pytest.approx(ef4 * 17.0 * NH3_TO_N_FACTOR * N_TO_N2O_FACTOR, rel=1e-9)


def test_flooded_rice_takes_the_aggregated_ef1fr_in_any_climate():
    for share in (0.0, 1.0):
        assert _model(crop="rice", wet_climate_share=share)._compute_direct_n2o_as_n(100.0, 50.0, "ef1fr_aggregated") \
            == pytest.approx(0.004 * 150.0)


def test_manure_n_is_an_other_n_input():
    out = _model(nitrogen_from_all_manure=100.0).compute()
    out_other_orga = _model(nitrogen_from_other_orga_fert=100.0).compute()
    assert out["m_N_N2o_air"] == pytest.approx(out_other_orga["m_N_N2o_air"])
    assert _model()._compute_direct_n2o_as_n(0.0, 100.0, None) == pytest.approx(0.6)


def test_wet_climate_share_must_be_a_fraction():
    with pytest.raises(ValueError):
        _model(wet_climate_share=1.5).compute()


def test_table_covers_every_crop_and_country():
    crops = {row["crop"] for row in dataloader.rows("crop_types.csv")} | {"all_crops"}
    countries = {row["country"] for row in dataloader.rows("faostat_country_mapping.csv")} - {"GLO"}
    rows = dataloader.rows(TABLE)
    assert {(r["crop"], r["country"]) for r in rows} == {(c, k) for c in crops for k in countries}
    assert all(float(r["coverage"]) > 0.95 and 0.0 <= float(r["wet_share"]) <= 1.0
               and 0.0 <= float(r["tropical_share"]) <= 1.0 for r in rows)


@pytest.mark.parametrize("country, low, high", [("NL", 0.99, 1.0), ("BE", 0.99, 1.0), ("FI", 0.99, 1.0),
                                                 ("ES", 0.0, 0.1), ("HU", 0.0, 0.1), ("UA", 0.0, 0.1),
                                                 ("FR", 0.3, 0.6), ("ID", 0.99, 1.0)])
def test_wet_share_of_the_countries_checked_against_figure_3a_5_1(country, low, high):
    assert low <= float(_row("all_crops", country)["wet_share"]) <= high


@pytest.mark.parametrize("crop, country", [("wheat", "IT"), ("rice", "IN"), ("apple", "FR")])
def test_default_is_the_crop_row(crop, country):
    defaults = DefaultValuesWrapper({"crop": crop, "country": country}, DEFAULTS_VALUES_GENERATORS)
    assert defaults["wet_climate_share"] == float(_row(crop, country)["wet_share"])

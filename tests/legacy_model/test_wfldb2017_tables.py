"""Decision L22: country soil, precipitation and irrigation water source tables of defaultTables.py
from the WFLDB 2017 background parameters (ecoinvent 3 report, 04 May 2017). The manure shares of
sheet 3 were replaced by FAOSTAT 2021-2023 (decision L29, test_manure_defaults.py); the precipitation column is kept
as transcribed but the model default comes from TerraClimate (decision L61, test_terraclimate_precipitation.py); the
soil columns and the soil-type K factors are kept as transcribed but the model defaults come from HWSD v2.0 (decision
L63, test_hwsd_soil.py)."""
from pathlib import Path

import pytest

import dataloader
import defaultTables as t
from models.irrigationmodel import WaterUseType

WORKBOOK = (Path(__file__).resolve().parents[2] / "Literature"
            / "ecoinvent 3 report_WFLDB_BackgroundParameters_2017.xlsx")
COUNTRY_TABLES = ["YEARLY_PRECIPITATION_AS_SNOW_PER_COUNTRY", "IRR_WATERUSE_RATIO_PER_COUNTRY"]
NOT_IN_WFLDB = {"MA", "CS"}


def _column(column):
    return {country: row[column] for country, row in dataloader.table("wfldb2017_agr_system_parameters.csv").items()}


@pytest.mark.parametrize("name", COUNTRY_TABLES)
def test_tables_cover_the_39_countries_of_the_tool(name):
    assert set(getattr(t, name)) == set(dataloader.table("luc_blonk_country_expansion.csv"))
    assert set(_column("clay_content_ratio")) == set(dataloader.table("luc_blonk_country_expansion.csv"))


def test_water_shares_keep_the_enum_keys_and_sum_to_one():
    for shares in t.IRR_WATERUSE_RATIO_PER_COUNTRY.values():
        assert set(shares) == set(WaterUseType) and sum(shares.values()) == pytest.approx(1.0, abs=1e-9)


def test_spot_values_from_the_workbook():
    # sheet '1) Agr. system parameters': P12 (FR clay), W17 (IT precipitation), D7 (AR sandy soils)
    assert _column("clay_content_ratio")["FR"] == 0.304420218037661
    assert dataloader.table("wfldb2017_agr_system_parameters.csv")["IT"]["annual_precipitation_mm"] == 930.193617321
    assert _column("sandy_soils_ratio")["AR"] == 0.04018014391385297


def test_china_humus_is_the_documented_estimate():
    # workbook cell J13 is 0; WFLDB Documentation 2017 p. 14 note 3: estimate of 2 % for China
    assert _column("soil_organic_carbon_ratio")["CN"] == 0.02


@pytest.fixture(scope="module")
def workbook():
    if not WORKBOOK.is_file():
        pytest.skip("WFLDB 2017 workbook not in Literature/")
    import warnings
    import openpyxl
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)  # "Unknown extension is not supported"
        return openpyxl.load_workbook(WORKBOOK, data_only=True, read_only=False)


def _columns(ws, first_col):
    return {ws.cell(3, c).value: c for c in range(first_col, ws.max_column + 1) if ws.cell(3, c).value}


def test_agricultural_parameters_equal_the_workbook(workbook):
    ws = workbook["1) Agr. system parameters"]
    cols = _columns(ws, 4)
    rows = {"clay_content_ratio": 12, "sandy_soils_ratio": 7, "soil_organic_carbon_ratio": 13,
            "soil_ph_le7_ratio": 14, "precipitation_as_snow_ratio": 18}
    for name, row in rows.items():
        for country, value in _column(name).items():
            if country in NOT_IN_WFLDB or (name == "soil_organic_carbon_ratio" and country == "CN"):
                continue
            assert value == ws.cell(row, cols[country]).value, (name, country)
    for country, row in dataloader.table("wfldb2017_agr_system_parameters.csv").items():
        if country not in NOT_IN_WFLDB:
            assert row["annual_precipitation_mm"] == ws.cell(17, cols[country]).value, country


def test_clay_is_the_soil_type_mix_of_documentation_tab6(workbook):
    ws = workbook["1) Agr. system parameters"]
    clay_of_soil_type = {5: 0.30, 6: 0.50, 7: 0.04, 8: 0.35, 9: 0.35, 10: 0.35}  # HAC, LAC, sandy, spodic, volcanic, wetland
    clay_content = _column("clay_content_ratio")
    for country, col in _columns(ws, 4).items():
        if country in clay_content:
            mix = sum(ws.cell(row, col).value * clay for row, clay in clay_of_soil_type.items())
            assert clay_content[country] == pytest.approx(mix, abs=1e-12), country


def test_water_sources_equal_the_workbook(workbook):
    ws = workbook["2) Irrigation water sources"]
    cols = _columns(ws, 2)
    for country, shares in t.IRR_WATERUSE_RATIO_PER_COUNTRY.items():
        if country not in NOT_IN_WFLDB:
            for member, row in ((WaterUseType.groundwater, 4), (WaterUseType.surfacewater, 5),
                                (WaterUseType.nonconventional, 6)):
                assert shares[member] == ws.cell(row, cols[country]).value, (country, member)


def test_soil_type_shares_and_k_factors_of_documentation_tab6():
    # decision L27 (replaced by L63): K = sum of the soil-type shares (sheet 1 rows 5-10) x K-factor ** of Tab. 6
    k_factors = dataloader.table("wfldb2017_soil_type_k_factors.csv")
    assert {t: r["k_factor_panagos2014_t_h_per_mj_mm"] for t, r in k_factors.items()} == {
        "hac": 0.0347, "lac": 0.01325, "sandy": 0.0122, "spodic": 0.02735, "volcanic": 0.0385, "wetland": 0.0032}
    for country, row in dataloader.table("wfldb2017_agr_system_parameters.csv").items():
        if country not in NOT_IN_WFLDB:
            assert sum(row[soil + "_soils_ratio"] for soil in k_factors) == pytest.approx(1.0, abs=1e-9), country


def test_k_factor_from_clay_column_matches_the_tab6_formula():
    for row in dataloader.table("wfldb2017_soil_type_k_factors.csv").values():
        x = 100.0 * row["clay_content_ratio"]
        assert row["k_factor_from_clay_t_h_per_mj_mm"] == pytest.approx(
            -0.00002217 * x * x + 0.00171117 * x + 0.00572691, abs=5e-5)


"""Decision L22: country soil, precipitation, irrigation water source and manure tables of
defaultTables.py from the WFLDB 2017 background parameters (ecoinvent 3 report, 04 May 2017)."""
from pathlib import Path

import pytest

import dataloader
import defaultTables as t
from models.irrigationmodel import WaterUseType
from models.manuremodel import LiquidManureType, SolidManureType

WORKBOOK = (Path(__file__).resolve().parents[2] / "Literature"
            / "ecoinvent 3 report_WFLDB_BackgroundParameters_2017.xlsx")
COUNTRY_TABLES = ["ANNUAL_PRECIPITATION_PER_COUNTRY", "CLAY_CONTENT_PER_COUNTRY", "SAND_CONTENT_PER_COUNTRY",
                  "SOIL_CARBON_CONTENT_PER_COUNTRY", "SOIL_WITH_PH_UNDER_OR_7_PER_COUNTRY",
                  "YEARLY_PRECIPITATION_AS_SNOW_PER_COUNTRY", "IRR_WATERUSE_RATIO_PER_COUNTRY",
                  "MANURE_LIQUID_RATIO_PER_COUNTRY", "MANURE_SOLID_RATIO_PER_COUNTRY"]
NOT_IN_WFLDB = {"MA", "CS"}


@pytest.mark.parametrize("name", COUNTRY_TABLES)
def test_tables_cover_the_39_countries_of_the_tool(name):
    assert set(getattr(t, name)) == set(dataloader.table("luc_blonk_country_expansion.csv"))


def test_share_tables_keep_the_enum_keys_and_water_and_liquid_shares_sum_to_one():
    for shares in t.IRR_WATERUSE_RATIO_PER_COUNTRY.values():
        assert set(shares) == set(WaterUseType) and sum(shares.values()) == pytest.approx(1.0, abs=1e-9)
    for shares in t.MANURE_LIQUID_RATIO_PER_COUNTRY.values():
        assert set(shares) == set(LiquidManureType) and sum(shares.values()) == pytest.approx(1.0, abs=1e-9)
    for shares in t.MANURE_SOLID_RATIO_PER_COUNTRY.values():
        # solid shares sum to less than 1 for 33 countries already in the workbook
        assert set(shares) == set(SolidManureType) and sum(shares.values()) <= 1.0 + 1e-9


def test_spot_values_from_the_workbook():
    # sheet '1) Agr. system parameters': P12 (FR clay), W17 (IT precipitation), D7 (AR sandy soils)
    assert t.CLAY_CONTENT_PER_COUNTRY["FR"] == 0.304420218037661
    assert t.ANNUAL_PRECIPITATION_PER_COUNTRY["IT"] == 930.193617321
    assert t.SAND_CONTENT_PER_COUNTRY["AR"] == 0.04018014391385297
    # sheet '3) Animal shares org.Fertiliser', column C (AR): pig = r6 + r7, laying_hen_litter = r14 + r15
    assert t.MANURE_LIQUID_RATIO_PER_COUNTRY["AR"][LiquidManureType.pig] == 0 + 0.006943975890980679
    assert t.MANURE_SOLID_RATIO_PER_COUNTRY["AR"][SolidManureType.laying_hen_litter] == \
        0.021349697278433374 + 0.03737728870097202


def test_china_humus_is_the_documented_estimate():
    # workbook cell J13 is 0; WFLDB Documentation 2017 p. 14 note 3: estimate of 2 % for China
    assert t.SOIL_CARBON_CONTENT_PER_COUNTRY["CN"] == 0.02


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
    rows = {"ANNUAL_PRECIPITATION_PER_COUNTRY": 17, "CLAY_CONTENT_PER_COUNTRY": 12, "SAND_CONTENT_PER_COUNTRY": 7,
            "SOIL_CARBON_CONTENT_PER_COUNTRY": 13, "SOIL_WITH_PH_UNDER_OR_7_PER_COUNTRY": 14,
            "YEARLY_PRECIPITATION_AS_SNOW_PER_COUNTRY": 18}
    for name, row in rows.items():
        for country, value in getattr(t, name).items():
            if country in NOT_IN_WFLDB or (name == "SOIL_CARBON_CONTENT_PER_COUNTRY" and country == "CN"):
                continue
            assert value == ws.cell(row, cols[country]).value, (name, country)


def test_clay_is_the_soil_type_mix_of_documentation_tab6(workbook):
    ws = workbook["1) Agr. system parameters"]
    clay_of_soil_type = {5: 0.30, 6: 0.50, 7: 0.04, 8: 0.35, 9: 0.35, 10: 0.35}  # HAC, LAC, sandy, spodic, volcanic, wetland
    for country, col in _columns(ws, 4).items():
        if country in t.CLAY_CONTENT_PER_COUNTRY:
            mix = sum(ws.cell(row, col).value * clay for row, clay in clay_of_soil_type.items())
            assert t.CLAY_CONTENT_PER_COUNTRY[country] == pytest.approx(mix, abs=1e-12), country


def test_water_sources_and_manure_shares_equal_the_workbook(workbook):
    ws = workbook["2) Irrigation water sources"]
    cols = _columns(ws, 2)
    for country, shares in t.IRR_WATERUSE_RATIO_PER_COUNTRY.items():
        if country not in NOT_IN_WFLDB:
            for member, row in ((WaterUseType.groundwater, 4), (WaterUseType.surfacewater, 5),
                                (WaterUseType.nonconventional, 6)):
                assert shares[member] == ws.cell(row, cols[country]).value, (country, member)
    ws = workbook["3) Animal shares org.Fertiliser"]
    cols = _columns(ws, 3)
    for row in dataloader.rows("wfldb2017_manure_animal_shares.csv"):
        if row["country"] in NOT_IN_WFLDB or row["wfldb_rows"] == "-":
            continue
        cells = [ws.cell(int(r[1:]), cols[row["country"]]).value for r in row["wfldb_rows"].split("+")]
        assert float(row["share"]) == sum(cells), row

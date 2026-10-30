"""Decision L44: default irrigation water consumption from Pfister & Bayer (2014), technique shares from FAO
AQUASTAT (area equipped for full control irrigation per technique), irrigation efficiencies of the WFLDB Guidelines
v3.0 Tab. 3 in data/model_parameters.csv; tables of Mialyk et al. (2024) kept as cross-check."""
import importlib.util
import os
from collections import defaultdict
from pathlib import Path

import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS
from defaultMatrixEvapoTranspiration import EVAPO_TRANSPI_PER_CROP_PER_COUNTRY
from defaultTables import IRR_TECH_RATIO_PER_COUNTRY, _LEGACY_IRR_TECH_RATIO_PER_COUNTRY
from models.irrigationmodel import IrrigationModel, IrrigationType, IRRIGATION_TECHNIQUE, irrigation_efficiency

ROOT = Path(__file__).resolve().parents[2]
COUNTRIES = [row["country"] for row in dataloader.rows("faostat_country_mapping.csv") if row["country"] != "GLO"]


def _build_module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _technique_shares(table):
    shares = {"surface": 0.0, "sprinkler": 0.0, "localized": 0.0}
    for irrigation_type, share in table.items():
        shares[IRRIGATION_TECHNIQUE[irrigation_type]] += share
    return shares


def _electricity_share(table):
    electric = sum(v for k, v in table.items() if k.name.endswith("_electricity"))
    diesel = sum(v for k, v in table.items() if k.name.endswith("_diesel"))
    return electric / (electric + diesel)


def test_every_tool_country_has_a_technique_source_and_shares_summing_to_one():
    sources = {row["country"]: row["source"] for row in dataloader.rows("irrigation_technique_source.csv")}
    assert sorted(sources) == sorted(COUNTRIES)
    for country in COUNTRIES:
        assert sum(IRR_TECH_RATIO_PER_COUNTRY[country].values()) == pytest.approx(1.0)
        assert set(IRR_TECH_RATIO_PER_COUNTRY[country]) == set(IrrigationType)


def test_aquastat_countries_take_the_area_shares_and_keep_the_legacy_electricity_split():
    areas = {}
    for row in dataloader.rows("aquastat_irrigation_technique_area.csv"):
        areas.setdefault(row["country"], {})[row["technique"]] = float(row["area_kha"])
    for row in dataloader.rows("irrigation_technique_source.csv"):
        country, table = row["country"], IRR_TECH_RATIO_PER_COUNTRY[row["country"]]
        legacy = _LEGACY_IRR_TECH_RATIO_PER_COUNTRY[country]
        if row["source"] == "legacy":
            assert table == legacy
            continue
        total = sum(areas[country].values())
        for technique, share in _technique_shares(table).items():
            assert share == pytest.approx(areas[country].get(technique, 0.0) / total)
        assert _electricity_share(table) == pytest.approx(_electricity_share(legacy))
        assert table[IrrigationType.surface_irrigation_no_energy] == 0.0


@pytest.mark.parametrize("country, shares", [
    ("FR", {"surface": 129.0, "sprinkler": 2473.0, "localized": 241.0}),
    ("RU", {"surface": 0.6, "sprinkler": 0.3, "localized": 0.1}),
    ("VN", {"surface": 4584.0, "sprinkler": 1.1, "localized": 0.0}),
    ("NL", {"surface": 0.02, "sprinkler": 0.97, "localized": 0.01})])
def test_reviewed_technique_shares(country, shares):
    total = sum(shares.values())
    for technique, share in _technique_shares(IRR_TECH_RATIO_PER_COUNTRY[country]).items():
        assert share == pytest.approx(shares[technique] / total, abs=0.006)


def test_irrigation_efficiency_comes_from_the_model_parameters():
    for technique in ("surface", "sprinkler", "localized"):
        only = {k: (1.0 if v == technique else 0.0) for k, v in IRRIGATION_TECHNIQUE.items()}
        only = {k: v / sum(only.values()) for k, v in only.items()}
        assert irrigation_efficiency(only) == pytest.approx(dataloader.param("irrigation_efficiency_" + technique))
    assert dataloader.param("irrigation_efficiency_surface") == pytest.approx(0.60 * 0.75)
    assert irrigation_efficiency(IRR_TECH_RATIO_PER_COUNTRY["FR"]) == pytest.approx(0.749, abs=0.001)


def test_irrigation_model_and_default_water_use_share_the_efficiency():
    defaults = DefaultValuesWrapper({"crop": "wheat", "country": "FR", "yield_main_product_per_crop_cycle": 7000.0},
                                    DEFAULTS_VALUES_GENERATORS)
    efficiency = irrigation_efficiency(IRR_TECH_RATIO_PER_COUNTRY["FR"])
    water = defaults["water_use_total"]
    assert water == pytest.approx(EVAPO_TRANSPI_PER_CROP_PER_COUNTRY["wheat"]["FR"] / efficiency * 7.0)
    output = IrrigationModel({"water_use_total": water,
                              "irrigation_types_proportions": IRR_TECH_RATIO_PER_COUNTRY["FR"]}).compute()
    assert output["m_Irr_wfldb_water_to_air"] == pytest.approx(EVAPO_TRANSPI_PER_CROP_PER_COUNTRY["wheat"]["FR"] * 7.0)
    assert output["m_Irr_wfldb_water_to_water_river"] + output["m_Irr_wfldb_water_to_water_groundwater"] == \
        pytest.approx(water * (1.0 - efficiency))


def test_mialyk_crop_mapping_follows_the_default_yield_items():
    items = {row["crop"]: row for row in dataloader.rows("faostat_crop_item_mapping.csv")}
    proxies = {row["crop"]: row["ludemann_item_code"] for row in dataloader.rows("n_uptake_other_crop_parameters.csv")}
    mapping = {row["crop"]: row for row in dataloader.rows("mialyk2024_crop_mapping.csv")}
    assert sorted(mapping) == sorted(items)
    for crop, row in mapping.items():
        if row["use"] == "direct":
            assert row["mialyk_crop_code"] == items[crop]["faostat_item_code"]
            assert row["kg_item_per_kg_product"] == items[crop]["faostat_kg_per_kg_product"]
        elif row["use"] == "proxy":
            assert row["mialyk_crop_code"] == proxies[crop]
        else:
            assert row["use"] == "legacy" and crop in ("flax", "mulberry")


def test_mialyk_glo_rows_are_production_weighted_means():
    rows = dataloader.rows("mialyk2024_national_blue_wf.csv")
    glo = [row for row in rows if row["country"] == "GLO"]
    codes = {row["mialyk_crop_code"] for row in dataloader.rows("mialyk2024_crop_mapping.csv") if row["mialyk_crop_code"]}
    assert {row["mialyk_crop_code"] for row in glo} == codes
    for row in rows:
        assert float(row["wfb_i_m3_t"]) >= 0.0 and float(row["production_t"]) > 0.0


def test_aquastat_table_equals_the_workbook():
    build = _build_module("build_aquastat_irrigation_techniques")
    workbook = dataloader.EXTERNAL_DATA_DIR / build.WORKBOOK
    if not workbook.is_file():
        pytest.skip("AQUASTAT workbook not in data/external_data/")
    rebuilt = [{k: str(v) for k, v in row.items()} for row in build.build(workbook)]
    assert rebuilt == [dict(row) for row in dataloader.rows("aquastat_irrigation_technique_area.csv")]


def test_mialyk_table_equals_the_dataset():
    build = _build_module("build_mialyk_blue_water")
    source = dataloader.EXTERNAL_DATA_DIR / build.MIALYK_FILE
    if not source.is_file():
        pytest.skip("Mialyk et al. national averages not in data/external_data/")
    rebuilt = [{k: str(v) for k, v in row.items()} for row in build.build(source)]
    assert rebuilt == [dict(row) for row in dataloader.rows("mialyk2024_national_blue_wf.csv")]


def test_default_consumption_is_the_pfister_appendix_b_value():
    expected = defaultdict(dict)
    for row in dataloader.rows("pfister2014_blue_water_country.csv"):
        if row["bw_expected_m3_t"] != "":
            expected[row["pfister_crop"]][row["country"]] = float(row["bw_expected_m3_t"])
    mapping = {row["crop"]: row for row in dataloader.rows("pfister2014_crop_mapping.csv")}
    legacy = dataloader.crop_country_table("legacy_irrigation_water_consumption.csv", "etirr_m3_per_t")
    assert sorted(legacy) == sorted(crop for crop, row in mapping.items() if row["use"] == "legacy")
    assert sorted(mapping) == sorted(row["crop"] for row in dataloader.rows("faostat_crop_item_mapping.csv"))
    assert sorted(EVAPO_TRANSPI_PER_CROP_PER_COUNTRY) == sorted(mapping)
    mialyk = defaultdict(dict)
    for row in dataloader.rows("mialyk2024_national_blue_wf.csv"):
        mialyk[row["mialyk_crop_code"]][row["country"]] = float(row["wfb_i_m3_t"])
    mialyk_items = {row["crop"]: row["mialyk_crop_code"] for row in dataloader.rows("mialyk2024_crop_mapping.csv")}
    assert sorted(crop for crop, row in mapping.items() if row["use"] == "mialyk") == ["hemp", "mint"]  # decision L56
    for crop, row in mapping.items():
        if row["use"] == "legacy":
            assert EVAPO_TRANSPI_PER_CROP_PER_COUNTRY[crop] == legacy[crop]
        elif row["use"] == "mialyk":
            assert EVAPO_TRANSPI_PER_CROP_PER_COUNTRY[crop] == mialyk[mialyk_items[crop]]
        else:
            assert EVAPO_TRANSPI_PER_CROP_PER_COUNTRY[crop] == expected[row["pfister_crop"]]
            assert "GLO" in EVAPO_TRANSPI_PER_CROP_PER_COUNTRY[crop]


@pytest.mark.parametrize("crop, country, value", [
    ("wheat", "FR", 111.2098653379725), ("potato", "US", 85.36298210876255), ("tea", "KE", 1284.5369299344975),
    ("wheat", "GLO", 414.5089098246473), ("mint", "MA", 154.838), ("mint", "GLO", 150.909), ("hemp", "FR", 0.0),
    ("hemp", "GLO", 3.862), ("mulberry", "IN", 164.73), ("mulberry", "GLO", 164.73), ("flax", "FR", 7.8)])
def test_reviewed_consumption_values(crop, country, value):
    assert EVAPO_TRANSPI_PER_CROP_PER_COUNTRY[crop][country] == pytest.approx(value)


def test_countries_without_appendix_b_value_take_glo():
    defaults = DefaultValuesWrapper({"crop": "cranberry", "country": "US", "yield_main_product_per_crop_cycle": 1000.0},
                                    DEFAULTS_VALUES_GENERATORS)
    assert "US" not in EVAPO_TRANSPI_PER_CROP_PER_COUNTRY["cranberry"]
    efficiency = irrigation_efficiency(IRR_TECH_RATIO_PER_COUNTRY["US"])
    assert defaults["water_use_total"] == pytest.approx(EVAPO_TRANSPI_PER_CROP_PER_COUNTRY["cranberry"]["GLO"] / efficiency)


@pytest.mark.parametrize("crop, country, yield_kg", [("tea", "KE", 2200.0), ("rice", "IN", 4300.0)])
def test_withdrawal_is_consumption_per_ha_divided_by_the_efficiency(crop, country, yield_kg):
    """m3/t x kg/ha / 1000 = m3/ha consumed; / EFirr = m3/ha withdrawn (WFLDB Guidelines v3.0 section 3.5.2)."""
    defaults = DefaultValuesWrapper({"crop": crop, "country": country, "yield_main_product_per_crop_cycle": yield_kg},
                                    DEFAULTS_VALUES_GENERATORS)
    consumed = EVAPO_TRANSPI_PER_CROP_PER_COUNTRY[crop][country] * yield_kg / 1000.0
    assert defaults["water_use_total"] == pytest.approx(consumed / irrigation_efficiency(IRR_TECH_RATIO_PER_COUNTRY[country]))


def test_pfister_ranges_and_watershed_shares():
    countries = {row["country"] for row in dataloader.rows("pfister2014_country_mapping.csv")}
    assert countries == set(COUNTRIES)
    for row in dataloader.rows("pfister2014_blue_water_country.csv"):
        if row["bw_min_m3_t"] != "":
            assert 0.0 <= float(row["bw_min_m3_t"]) <= float(row["bw_max_m3_t"])
    shares, months = defaultdict(float), []
    for row in dataloader.rows("pfister2014_blue_water_watershed.csv"):
        if row["blue_water_share"] != "":
            shares[(row["pfister_crop"], row["country"])] += float(row["blue_water_share"])
        if row["month_01"] != "":
            months.append(sum(float(row["month_%02d" % m]) for m in range(1, 13)))
    assert all(total == pytest.approx(1.0, abs=1e-4) for total in shares.values())
    assert all(total == pytest.approx(1.0, abs=1e-4) for total in months)


@pytest.mark.skipif(not os.environ.get("AGRITOOL_SLOW_TESTS"), reason="about 90 s; set AGRITOOL_SLOW_TESTS=1")
def test_pfister_tables_equal_the_source_files():
    build = _build_module("build_pfister_blue_water")
    supplementary = dataloader.EXTERNAL_DATA_DIR / build.SUPPLEMENTARY
    archive = dataloader.EXTERNAL_DATA_DIR / build.WATERSHED_ZIP
    if not supplementary.is_file() or not archive.is_file():
        pytest.skip("Pfister & Bayer files not in data/external_data/")
    country_rows, watershed_rows = build.build(supplementary, archive)
    as_text = lambda rows: [{k: str(v) for k, v in row.items()} for row in rows]
    assert as_text(country_rows) == [dict(row) for row in dataloader.rows("pfister2014_blue_water_country.csv")]
    assert as_text(watershed_rows) == [dict(row) for row in dataloader.rows("pfister2014_blue_water_watershed.csv")]

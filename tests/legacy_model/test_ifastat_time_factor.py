"""Decision L53: the IFA Fertilizer Use by Crop rates are brought to 2021-2023 with the ratio of the IFASTAT
consumption (data/ifastat_fertiliser_time_factor.csv, built by scripts/build_ifastat_time_factor.py; before: FAOSTAT
RFN use per area of cropland), and a region rate (L37) is at most the highest rate of the region countries, each
brought to 2021-2023 with its own factor."""
import importlib.util
from pathlib import Path

import pytest

import dataloader
from defaultTables import IFA_MINERAL_FERTILISER_PER_CROP_PER_COUNTRY as IFA

ROOT = Path(__file__).resolve().parents[2]
FACTORS = dataloader.rows("ifastat_fertiliser_time_factor.csv")


def _factor(key, value, nutrient):
    return float(next(r for r in FACTORS if r[key] == value and r["nutrient"] == nutrient)["factor"])


def _rate(fubc_country, fubc_crop, nutrient):
    row = next(r for r in dataloader.rows("ifa_fubc_rates.csv")
               if r["fubc_country"] == fubc_country and r["fubc_crop"] == fubc_crop)
    return float(row[nutrient.lower() + "_kg_per_ha"])


def test_every_tool_country_has_a_factor():
    countries = {r["country"] for r in dataloader.rows("ifa_fubc_country_mapping.csv")}
    assert {(r["country"], r["nutrient"]) for r in FACTORS if r["country"] and r["factor"]} == \
        {(c, n) for c in countries for n in ("N", "P2O5", "K2O")}


def test_only_ratios_are_stored():
    # the IFASTAT values are reserved for IFA members (FC decision 2026-10-26, as for L45)
    assert list(FACTORS[0]) == ["country", "fubc_country", "ifastat_alpha3", "nutrient", "base_years", "target_years",
                                "factor", "note"]


def test_countries_without_factor():
    assert sorted({r["fubc_country"] for r in FACTORS if not r["factor"]}) == \
        ["Bolivia (Plurinational State of)", "Burkina Faso"]


def test_mappings_agree():
    tool = {r["country"]: r["ifastat_alpha3"] for r in dataloader.rows("ifastat_country_mapping.csv")}
    for row in FACTORS:
        if row["country"]:
            assert row["ifastat_alpha3"] == tool[row["country"]], row


@pytest.mark.parametrize("country, fubc_crop, crop", [("TH", "Rice", "rice"), ("PH", "Rice", "rice"),
                                                      ("FR", "Wheat", "wheat")])
def test_own_rate_times_the_ifastat_factor(country, fubc_crop, crop):
    fubc_country = next(r["fubc_country"] for r in FACTORS if r["country"] == country)
    for nutrient in ("N", "P2O5", "K2O"):
        assert IFA[crop][country][nutrient.lower()] == pytest.approx(
            _rate(fubc_country, fubc_crop, nutrient) * _factor("country", country, nutrient))


def test_no_faostat_break():
    # FAOSTAT RFN gave TH P2O5 x1.87 and PH P2O5 x2.57 (2022-2023 values); IFASTAT 0.75 and 1.16
    assert _factor("country", "TH", "P2O5") == pytest.approx(0.7492)
    assert _factor("country", "PH", "P2O5") == pytest.approx(1.1552)
    assert IFA["wheat"]["TH"]["p2o5"] == pytest.approx(124.8 * 0.7492, abs=0.1)  # was 234 kg/ha


def test_region_rate_is_bounded_by_the_highest_region_country():
    # palm AR: median of Mexico and Peru x factor of AR = 165.5 kg N/ha, above both countries in 2021-2023
    rows = [r for r in dataloader.rows("ifa_fubc_rates.csv")
            if r["fubc_country"] in ("Mexico", "Peru") and r["fubc_crop"] in ("Oil palm fruit", "Oil Palm")]
    assert {r["fubc_country"] for r in rows} == {"Mexico", "Peru"}
    scaled = [float(r["n_kg_per_ha"]) * _factor("fubc_country", r["fubc_country"], "N") for r in rows]
    median = sum(float(r["n_kg_per_ha"]) for r in rows) / 2 * _factor("country", "AR", "N")
    assert median > max(scaled)
    assert IFA["palmtree"]["AR"]["n"] == pytest.approx(max(scaled))


@pytest.mark.skipif(not (dataloader.EXTERNAL_DATA_DIR / "ifastat-data-2026-10-19.csv").is_file(),
                    reason="IFASTAT export not in data/external_data/")
def test_table_is_rebuilt_from_the_ifastat_export():
    spec = importlib.util.spec_from_file_location("build", ROOT / "scripts" / "build_ifastat_time_factor.py")
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    rows = build.build(dataloader.EXTERNAL_DATA_DIR / "ifastat-data-2026-10-19.csv")
    assert [{k: str(v) for k, v in r.items()} for r in rows] == [dict(r) for r in FACTORS]

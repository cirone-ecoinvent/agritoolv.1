"""Decision L48: default total pesticides (g a.i./ha and crop cycle) from the Global atlas of pesticide use
(data/atlas2026_pesticides_country.csv, built by scripts/build_atlas_pesticides.py): applied mass of all a.i. 2016-2020
/ FAOSTAT area harvested; flagged values decided in data/atlas2026_pesticides_review.csv; fallback WFLDB 2017 value of
the country (L43), else GLO = world mass / FAOSTAT World area."""
import importlib.util
import os
from pathlib import Path

import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS
from defaultMatrixTotalPesticides import TOTAL_PESTICIDES_PER_CROP_PER_COUNTRY as PESTICIDES, _load_wfldb_pesticides

ROOT = Path(__file__).resolve().parents[2]
ATLAS = dataloader.rows("atlas2026_pesticides_country.csv")
REVIEW = {(row["atlas_crop"], row["country"]): row for row in dataloader.rows("atlas2026_pesticides_review.csv")}
FUMIGANTS = {row["cas_rn"] for row in dataloader.rows("soil_fumigant_active_ingredients.csv")}
LEGACY_TAG = "legacy, undocumented, provisional"


def _build_module():
    spec = importlib.util.spec_from_file_location("build", ROOT / "scripts" / "build_atlas_pesticides.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _atlas(crop, country):
    return next(row for row in ATLAS if (row["atlas_crop"], row["country"]) == (crop, country))


def _default(**inputs):
    return DefaultValuesWrapper(inputs, DEFAULTS_VALUES_GENERATORS)["pest_total"]


def test_review_table_holds_exactly_the_flagged_values():
    flagged = _build_module().flags(ATLAS)
    assert len(flagged) == 74
    assert {key: row["flag"] for key, row in REVIEW.items()} == flagged


def test_review_tables_are_signed():
    for row in list(REVIEW.values()) + list(dataloader.rows("soil_fumigant_active_ingredients.csv")):
        assert row["status"] == "confirmed" and row["reviewed_by"].strip()
    assert {row["use"] for row in REVIEW.values()} == {"atlas", "fallback"}
    assert len(FUMIGANTS) == 12


def test_kept_values_are_the_values_above_the_range_dominated_by_soil_fumigants():
    above = {key for key, row in REVIEW.items() if row["flag"] == "above_median_range"}
    fumigants = {key for key in above if float(_atlas(*key)["soil_fumigant_mass_kg"])
                 > 0.5 * float(_atlas(*key)["applied_mass_kg"])}
    assert {key for key, row in REVIEW.items() if row["use"] == "atlas"} == fumigants
    assert fumigants == {("strawberry", "ES"), ("strawberry", "US"), ("strawberry", "IL"), ("strawberry", "MA"),
                         ("rasberry", "ES"), ("carrot", "IT"), ("carrot", "US"), ("onion", "IL"), ("groundnut", "IL")}


def test_values_are_the_applied_mass_over_the_area_harvested():
    for row in ATLAS:
        if row["area_harvested_ha"]:
            assert float(row["kg_ai_per_ha"]) == pytest.approx(
                float(row["applied_mass_kg"]) / float(row["area_harvested_ha"]), rel=1e-5)
        else:
            assert row["kg_ai_per_ha"] == "" and REVIEW[(row["atlas_crop"], row["country"])]["flag"] == "no_area"
    assert all(int(row["area_years"]) == 5 for row in ATLAS if row["country"] == "GLO")


def test_tool_crops_take_the_atlas_values():
    assert PESTICIDES["rice"]["IN"] == pytest.approx(645.097)  # WFLDB 2017: 1500, rice_IN snapshot
    assert PESTICIDES["wheat"]["FR"] == pytest.approx(float(_atlas("wheat", "FR")["kg_ai_per_ha"]) * 1000.0)
    assert PESTICIDES["strawberry_fresh"]["ES"] == pytest.approx(229470.0)  # soil fumigants 84 %, kept
    # one atlas crop for the grades and species of the tool
    for first, second in (("tomato_fresh", "tomato_processing"), ("bellpepper", "chilli"), ("lemon", "citruslime"),
                          ("asparagus_green", "asparagus_white"), ("cabbage_red", "cabbage_white")):
        assert PESTICIDES[first] == PESTICIDES[second]
    assert PESTICIDES["tomato_fresh"]["ES"] == pytest.approx(66229.9)  # WFLDB 2017: fresh 32300, processing 19520


def test_glo_is_the_world_mass_over_the_world_area():
    grape = _atlas("grape", "GLO")
    assert PESTICIDES["grape"]["GLO"] == pytest.approx(
        float(grape["applied_mass_kg"]) / float(grape["area_harvested_ha"]) * 1000.0, rel=1e-5)
    assert PESTICIDES["grape"]["GLO"] == pytest.approx(22597.9)  # legacy GLO 0
    assert PESTICIDES["maizegrain"]["GLO"] == pytest.approx(1811.76)  # WFLDB 2017: 130 (AR only)


def test_fallback_to_the_wfldb_value_of_the_country_else_glo():
    wfldb = _load_wfldb_pesticides()
    assert PESTICIDES["onion"]["CN"] == wfldb["onion"]["CN"] == pytest.approx(10600.0)  # atlas 4.8 g/ha, 4 a.i.
    assert PESTICIDES["onion"]["NZ"] == pytest.approx(23330.0)  # no FAOSTAT area
    assert PESTICIDES["potato"]["RU"] == pytest.approx(870.0)  # atlas below the range
    assert PESTICIDES["pear"]["AR"] == pytest.approx(13780.0)  # no atlas value
    assert PESTICIDES["strawberry_fresh"]["CH"] == pytest.approx(45770.0)  # no atlas value
    # no WFLDB value: GLO of the atlas
    assert "NL" not in PESTICIDES["maizegrain"]  # atlas maize NL 23.4 kg/ha includes silage maize
    assert _default(crop="maizegrain", country="NL") == pytest.approx(1811.76)
    assert "PE" not in PESTICIDES["banana"]
    assert _default(crop="blueberry", country="US") == pytest.approx(1560.6, rel=1e-4)  # legacy 97373


def test_crops_without_an_atlas_crop_keep_wfldb_or_legacy():
    items = {row["faostat_item_code"] for row in ATLAS}
    without = {row["crop"] for row in dataloader.rows("faostat_crop_item_mapping.csv")
               if row["faostat_item_code"] not in items}
    assert without == {"castor_beans", "coconut", "cranberry", "flax", "guar", "hemp", "mint", "mulberry",
                       "pomegranate", "sweetcorn"}
    wfldb = _load_wfldb_pesticides()
    for crop in ("coconut", "mint", "sweetcorn"):
        assert PESTICIDES[crop] == wfldb[crop]
    assert PESTICIDES["cranberry"]["GLO"] == pytest.approx(97373.0)
    assert PESTICIDES["castor_beans"] == {"GLO": 0.0}


def test_legacy_table_keeps_only_the_crops_without_atlas_and_wfldb_values():
    rows = dataloader.rows("default_pesticides.csv")
    assert len(rows) == 9 and all(row["note"].endswith(LEGACY_TAG) for row in rows)
    assert {row["crop"] for row in rows} == {"castor_beans", "cranberry", "flax", "guar", "hemp", "mulberry",
                                             "pomegranate"}


@pytest.mark.skipif(not os.environ.get("AGRITOOL_SLOW_TESTS"), reason="about 15 s; set AGRITOOL_SLOW_TESTS=1")
def test_atlas_table_equals_the_source_files():
    build = _build_module()
    files = [dataloader.EXTERNAL_DATA_DIR / name for name in (build.S1_FILE, build.S2_FILE, build.QCL_FILE,
                                                               build.M49_FILE)]
    if not all(path.is_file() for path in files):
        pytest.skip("atlas, FAOSTAT or UNSD files not in data/external_data/")
    rebuilt = build.build(*files)
    assert [{key: str(value) for key, value in row.items()} for row in rebuilt] == [dict(row) for row in ATLAS]

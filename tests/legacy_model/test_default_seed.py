"""Decision L46: default seed of the sown crops from FAOSTAT SUA seed / area harvested of the next year (2021-2023),
checked against the seeding rates of the FAO Technical Conversion Factors (data/default_seed.csv, built by
scripts/build_default_seed.py); crops without usable data keep the legacy GLO values."""
import importlib.util
import os
from pathlib import Path

import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS, TREE_BASED_CROPS, \
    SEEDLINGS_BASED_CROPS
from defaultMatrixSeed import NB_SEEDS_PER_PARTIAL_CROP_PER_COUNTRY, _LEGACY_SEEDS

ROOT = Path(__file__).resolve().parents[2]
MAPPING = {row["crop"]: row for row in dataloader.rows("seed_rate_crop_mapping.csv")}
SEEDS = {(row["crop"], row["country"]): row for row in dataloader.rows("default_seed.csv")}
COUNTRIES = [row["country"] for row in dataloader.rows("faostat_country_mapping.csv")]
FACTOR = dataloader.param("seed_rate_max_ratio")


def _build_module():
    spec = importlib.util.spec_from_file_location("build", ROOT / "scripts" / "build_default_seed.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _float(value):
    return float(value) if value != "" else None


def test_mapping_covers_the_sown_crops_and_splits_them_into_table_and_legacy():
    crops = [row["crop"] for row in dataloader.rows("faostat_crop_item_mapping.csv")]
    sown = {crop for crop in crops if crop not in TREE_BASED_CROPS and crop not in SEEDLINGS_BASED_CROPS}
    assert set(MAPPING) == sown
    assert {crop for crop, row in MAPPING.items() if row["use"] == "legacy"} == set(_LEGACY_SEEDS)
    assert {crop for crop, _ in SEEDS} == {crop for crop, row in MAPPING.items() if row["use"] == "sua_tcf"}


def test_every_table_crop_has_a_positive_rate_for_every_country_and_glo():
    for crop in {crop for crop, _ in SEEDS}:
        for country in COUNTRIES:
            row = SEEDS[(crop, country)]
            assert float(row["seed_kg_per_ha"]) > 0
            assert NB_SEEDS_PER_PARTIAL_CROP_PER_COUNTRY[crop][country] == float(row["seed_kg_per_ha"])
        assert SEEDS[(crop, "GLO")]["source"] == "faostat_sua"


def test_each_rate_follows_the_sua_tcf_glo_rule():
    for (crop, country), row in SEEDS.items():
        if country == "GLO":
            continue
        sua, tcf = _float(row["sua_kg_per_ha"]), _float(row["tcf_kg_per_ha"])
        glo = float(SEEDS[(crop, "GLO")]["seed_kg_per_ha"])
        reference = tcf if tcf is not None else glo
        if sua is not None and 1 / FACTOR <= sua / reference <= FACTOR:
            expected = (sua, "faostat_sua")
        elif tcf is not None:
            expected = (tcf, "fao_tcf")
        else:
            expected = (glo, "glo")
        assert (float(row["seed_kg_per_ha"]), row["source"]) == expected, (crop, country)


def test_tcf_column_is_the_extracted_tcf_table():
    item_crop = {item: crop for crop, row in MAPPING.items() for item in row["tcf_items"].split("|") if item}
    tcf = {(item_crop[row["tcf_item"]], row["country"]): float(row["seed_rate_kg_per_ha"])
           for row in dataloader.rows("fao_tcf_seed_rates.csv")}
    assert len(tcf) == len(dataloader.rows("fao_tcf_seed_rates.csv"))
    assert {key: _float(row["tcf_kg_per_ha"]) for key, row in SEEDS.items() if row["tcf_kg_per_ha"]} == tcf


def test_wheat_france_is_the_mean_of_seed_over_next_year_area():
    # FAOSTAT SUA seed of wheat, France, 2021-2023 (t) and QCL area harvested 2022-2024 (ha)
    seed = (745788.97, 696986.51, 702389.78)
    area = (4949840.0, 4998280.0, 4454180.0)
    expected = sum(s * 1000 / a for s, a in zip(seed, area)) / 3
    row = SEEDS[("wheat", "FR")]
    assert float(row["sua_kg_per_ha"]) == pytest.approx(expected, abs=1e-3)
    assert row["source"] == "faostat_sua" and float(row["tcf_kg_per_ha"]) == 162.0


def test_outliers_take_the_tcf_or_glo_rate():
    # maize NL: seed of silage maize divided by the grain maize area; soybean ZA: SUA far below the TCF rate
    assert (SEEDS[("maizegrain", "NL")]["source"], float(SEEDS[("maizegrain", "NL")]["seed_kg_per_ha"])) == \
        ("fao_tcf", 25.0)
    assert (SEEDS[("soybean", "ZA")]["source"], float(SEEDS[("soybean", "ZA")]["seed_kg_per_ha"])) == ("fao_tcf", 75.0)
    assert SEEDS[("sunflower", "CH")]["source"] == "glo"


def test_default_seed_quantities_use_the_table_and_the_legacy_values():
    for crop, country, expected in (("wheat", "FR", float(SEEDS[("wheat", "FR")]["seed_kg_per_ha"])),
                                    ("rice", "IN", float(SEEDS[("rice", "IN")]["seed_kg_per_ha"])),
                                    ("carrot", "FR", 4.2), ("sugarbeet", "DE", 2.1)):
        defaults = DefaultValuesWrapper({"crop": crop, "country": country}, DEFAULTS_VALUES_GENERATORS)
        assert defaults["seeds"] == expected
        assert defaults["seed_quantities"] == {crop: expected}


@pytest.mark.skipif(not os.environ.get("AGRITOOL_SLOW_TESTS"), reason="about 30 s; set AGRITOOL_SLOW_TESTS=1")
def test_seed_table_equals_the_faostat_downloads():
    build = _build_module()
    sua = dataloader.EXTERNAL_DATA_DIR / build.SUA_FILE
    qcl = dataloader.EXTERNAL_DATA_DIR / build.QCL_FILE
    if not (sua.is_file() and qcl.is_file()):
        pytest.skip("FAOSTAT downloads not in data/external_data/")
    rebuilt = [{key: str(value) for key, value in row.items()} for row in build.build(sua, qcl)]
    assert rebuilt == [dict(row) for row in dataloader.rows("default_seed.csv")]

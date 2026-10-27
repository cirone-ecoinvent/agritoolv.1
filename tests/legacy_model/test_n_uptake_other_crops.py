"""Decision L41: default N uptake (U of the SQCB nitrate model) of the crops without WFLDB level 1 coefficients =
yield per crop cycle x N per kg of main product: N of the crop product of Ludemann et al. 2023 (World coefficients
of the FAO Cropland Nutrient Budget) or, for fibre flax and hemp, N of main and by-product of GRUDAF 2009 Tab. 1;
for the field crops plus the above-ground residues of IPCC 2019 Table 11.1a (DRY x R_AG x N_AG)."""
import importlib.util
from pathlib import Path

import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS
from defaultTables import N_UPTAKE_PER_KG_MAIN_PRODUCT_PER_CROP, N_UPTAKE_PER_KG_MAIN_PRODUCT_OTHER_CROPS as N_PER_KG

ROOT = Path(__file__).resolve().parents[2]


def _defaults(**inputs):
    return DefaultValuesWrapper(inputs, DEFAULTS_VALUES_GENERATORS)


def test_parameters_cover_the_other_crops_and_are_signed():
    crops = set(dataloader.table("crop_types.csv", numeric=False)) - set(N_UPTAKE_PER_KG_MAIN_PRODUCT_PER_CROP)
    rows = dataloader.rows("n_uptake_other_crop_parameters.csv")
    assert {row["crop"] for row in rows} == crops - {"mulberry"}
    ludemann = dataloader.table("ludemann2023_world_crop_coefficients.csv", numeric=False)
    ipcc = dataloader.table("ipcc2019_table11_1a.csv")
    grudaf = dataloader.table("grudaf2009_table1_reference_yields.csv")
    for row in rows:
        assert row["status"] == "confirmed" and row["reviewed_by"], row
        assert bool(row["ludemann_item_code"]) != bool(row["grudaf_crop"]), row
        if row["ludemann_item_code"]:
            assert ludemann[row["ludemann_item_code"]]["item"] == row["ludemann_item"], row
        assert not row["grudaf_crop"] or row["grudaf_crop"] in grudaf, row
        assert not row["ipcc_residue_crop"] or row["ipcc_residue_crop"] in ipcc, row


def test_items_follow_the_faostat_items_of_the_default_yield():
    items = dataloader.table("faostat_crop_item_mapping.csv", numeric=False)
    for row in dataloader.rows("n_uptake_other_crop_parameters.csv"):
        if row["ludemann_item_code"] and row["crop"] in items and items[row["crop"]]["faostat_item_code"]:
            assert row["ludemann_item_code"] == items[row["crop"]]["faostat_item_code"], row


@pytest.mark.parametrize("name, n_ag, r_ag, dry", [
    ("Generic value for crops not indicated below", 0.008, 1.0, 0.85), ("Millet", 0.007, 1.4, 0.90),
    ("Beans and Pulses", 0.008, 2.1, 0.91), ("Potatoes and Tubers", 0.019, 0.4, 0.22)])
def test_ipcc_rows_in_use(name, n_ag, r_ag, dry):
    # IPCC 2019 Refinement Vol. 4 Table 11.1a, p. 11.18
    row = dataloader.table("ipcc2019_table11_1a.csv")[name]
    assert (row["n_ag_kg_per_kg_dm"], row["r_ag"], row["dry"]) == (n_ag, r_ag, dry)


@pytest.mark.parametrize("crop, g_n_per_kg", [
    ("bellpepper", 2.165), ("blueberry", 1.04), ("pineapple", 1.03), ("grape", 3.175), ("mint", 11.425),
    ("cassava", 2.47 + 0.22 * 0.4 * 19.0), ("chick_pea", 27.32823088625 + 0.91 * 2.1 * 8.0),
    ("pearl_millet", 22.9033333333333 + 0.90 * 1.4 * 7.0), ("cotton", 58.5 + 0.85 * 1.0 * 8.0),
    ("castor_beans", 14.4 + 0.85 * 1.0 * 8.0),
    ("flax", (45.0 + 82.0) / 45.0 * 10.0),  # GRUDAF Faserlein: 45 dt fibres 45 kg N, 15 dt seeds 82 kg N
    ("hemp", (30.0 + 110.0) / 100.0 * 10.0)])  # GRUDAF Faserhanf: 100 dt stems 30 kg N, 40 dt seeds/leaves 110 kg N
def test_n_per_kg_of_main_product(crop, g_n_per_kg):
    assert N_PER_KG[crop] == pytest.approx(g_n_per_kg / 1000.0)


def test_proxies():
    assert N_PER_KG["turmeric"] == N_PER_KG["ginger"]  # FAOSTAT item Ginger, as for the default yield
    assert N_PER_KG["guar"] == pytest.approx((26.0666666666667 + 0.91 * 2.1 * 8.0) / 1000.0)  # Pulses nes
    assert N_PER_KG["pomegranate"] == pytest.approx(1.93333333333333 / 1000.0)  # Fruit, fresh nes


@pytest.mark.parametrize("crop, country", [("grape", "FR"), ("cotton", "IN"), ("pineapple", "CR"), ("hemp", "CN")])
def test_uptake_follows_the_yield(crop, country):
    reference = _defaults(crop=crop, country=country)
    yield_ref = reference["yield_main_product_per_crop_cycle"]
    assert reference["nitrogen_uptake_by_crop"] == pytest.approx(yield_ref * N_PER_KG[crop])
    double = _defaults(crop=crop, country=country, yield_main_product_per_crop_cycle=2.0 * yield_ref)
    assert double["nitrogen_uptake_by_crop"] == pytest.approx(2.0 * reference["nitrogen_uptake_by_crop"])


@pytest.mark.parametrize("crop", ["chick_pea", "lentil", "guar"])
def test_legumes_count_the_share_of_the_uptake(crop):
    # decision L30: legume_uptake_share (0.4); lentil had a legacy N uptake of 0
    defaults = _defaults(crop=crop, country="IN", yield_main_product_per_crop_cycle=1000.0)
    assert defaults["nitrogen_uptake_by_crop"] == pytest.approx(0.4 * 1000.0 * N_PER_KG[crop])


@pytest.mark.parametrize("crop", ["guar", "pomegranate"])
def test_crops_without_default_yield_follow_the_template_yield(crop):
    assert _defaults(crop=crop, country="IN")["nitrogen_uptake_by_crop"] == 0.0
    assert _defaults(crop=crop, country="IN", yield_main_product_per_crop_cycle=1000.0)["nitrogen_uptake_by_crop"] > 0.0


def test_mulberry_keeps_the_legacy_value():
    defaults = _defaults(crop="mulberry", country="CN", yield_main_product_per_crop_cycle=9000.0)
    assert defaults["nitrogen_uptake_by_crop"] == 400.0  # data/legacy_n_uptake.csv (decision L55)


def test_table_equals_the_dryad_download():
    script = ROOT / "scripts" / "build_ludemann_crop_coefficients.py"
    spec = importlib.util.spec_from_file_location("build_ludemann_crop_coefficients", script)
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    download = dataloader.EXTERNAL_DATA_DIR / build.ZIP_NAME
    if not download.is_file():
        pytest.skip("Dryad download not in data/external_data/")
    assert build.build(download) == [dict(row) for row in dataloader.rows("ludemann2023_world_crop_coefficients.csv")]

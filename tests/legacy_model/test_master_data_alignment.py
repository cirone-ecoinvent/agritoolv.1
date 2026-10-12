"""Checks against the real ecoinvent Master Data; skipped when agritool.cfg / the env var is not set."""
import csv

import pytest

import config
import dataloader
import seedexchanges

pytestmark = pytest.mark.skipif(
    config.master_data_path() is None or not config.master_data_path().is_file(),
    reason="ecoinvent Master Data not configured")


@pytest.fixture(scope="module")
def exchanges():
    return seedexchanges.master_data_exchanges()


def test_every_seed_exchange_name_exists_with_the_mapped_unit(exchanges):
    mapping = seedexchanges.load_seed_mapping()
    assert seedexchanges.validate_seed_mapping(mapping, exchanges) == []
    for row in dataloader.rows("seed_exchange_mapping.csv"):
        if row["seed_exchange_name"]:
            assert exchanges[row["seed_exchange_name"]].unit == row["unit"], row["crop_key"]


@pytest.mark.parametrize("filename", ["elementary_flow_alignment.csv", "intermediate_exchange_alignment.csv"])
def test_confirmed_alignment_names_have_a_master_data_uuid(filename):
    with open(dataloader.DATA_DIR / filename, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    bad = [r["legacy_name"] for r in rows
           if r["status"] in ("ok", "renamed", "proposed", "confirmed") and not r["md312_uuid"]]
    assert bad == []


def test_every_fertiliser_product_has_a_nutrient_content():
    path = config.master_data_path()
    contents = {mv: dataloader.fertiliser_nutrient_content(path, mv)
                for mv in dataloader.table(dataloader.FERTILISER_BASIS_TABLE)}
    assert all(0.0 < c <= 1.0 for c in contents.values()), contents
    # plausibility against the compositions stated in the Master Data comments
    assert contents["fert_n_mono_ammonium_phosphate"] == pytest.approx(0.084)
    assert contents["fert_p_mono_ammonium_phosphate"] == pytest.approx(0.52, abs=0.005)
    assert contents["fert_p_di_ammonium_phosphate"] == pytest.approx(0.46, abs=0.005)
    assert contents["fert_n_an_phosphate"] == pytest.approx(0.22)
    assert contents["fert_k_potassium_salt"] == pytest.approx(0.63, abs=0.005)
    assert contents["fert_n_urea"] == pytest.approx(0.466, abs=0.001)
    assert contents["fert_p_ground_basic_slag"] == pytest.approx(1.0)

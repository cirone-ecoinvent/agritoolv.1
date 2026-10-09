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

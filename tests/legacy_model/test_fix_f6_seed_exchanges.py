"""Fix F6: seed / seedling exchanges resolved from the ecoinvent Master Data through the reviewed
mapping; the run stops on unmapped, unreviewed, unknown or unit-mismatched crops.
Reference: reference_models.load_intermediate_exchanges / resolve_seed_exchange."""
import pytest

import config
import dataloader
import seedexchanges as se
from outputMapping import OutputMapping

MASTER_XML = """<?xml version="1.0" encoding="utf-8"?>
<validIntermediateExchanges xmlns="http://www.EcoInvent.org/EcoSpold02">
  <intermediateExchange id="uuid-maize-seed" unitId="u1">
    <name xml:lang="en">maize seed, for sowing</name><unitName xml:lang="en">kg</unitName>
  </intermediateExchange>
  <intermediateExchange id="uuid-tomato-seedling" unitId="u2">
    <name xml:lang="en">tomato seedling, for planting</name><unitName xml:lang="en">unit</unitName>
  </intermediateExchange>
  <intermediateExchange id="uuid-maize-grain" unitId="u1">
    <name xml:lang="en">maize grain</name><unitName xml:lang="en">kg</unitName>
  </intermediateExchange>
</validIntermediateExchanges>"""

MAPPING_CSV = ("crop_key,seed_exchange_name,unit,status,note,reviewed_by\n"
               "maize_grain,\"maize seed, for sowing\",kg,confirmed,,FR\n"
               "tomato_fresh_grade,\"tomato seedling, for planting\",unit,confirmed,,FR\n"
               "sugar_cane,,,no_exchange,,FR\n"
               "sweet_corn,\"maize seed, for sowing\",kg,to_decide,,\n"
               "rice,\"rice seed, for sowing\",kg,confirmed,,FR\n")


@pytest.fixture
def master(tmp_path, monkeypatch):
    xml = tmp_path / "IntermediateExchanges.xml"
    xml.write_text(MASTER_XML, encoding="utf-8")
    monkeypatch.setenv(config.ENV_VAR, str(xml))
    se._MASTER_DATA_CACHE.clear()
    mapping_file = tmp_path / "map.csv"
    mapping_file.write_text(MAPPING_CSV, encoding="utf-8")
    mapping = se.load_seed_mapping(mapping_file)
    monkeypatch.setattr(se, "load_seed_mapping", lambda path=None: mapping)
    return dataloader.load_intermediate_exchanges(xml), mapping


def test_legacy_codes_are_translated_by_the_alias_table():
    assert se.crop_key("maizegrain") == "maize_grain"
    assert se.crop_key("tomato_fresh") == "tomato_fresh_grade"
    assert se.crop_key("wheat") == "wheat"


def test_every_legacy_crop_has_a_mapping_key():
    mapping = se.load_seed_mapping()
    crops = dataloader.table("crop_types.csv", numeric=False)
    missing = [c for c in crops if se.crop_key(c) not in mapping]
    assert missing == []


def test_resolution_and_failures(master):
    exchanges, mapping = master
    assert se.validate_seed_mapping(mapping, exchanges) == ["rice seed, for sowing"]
    assert se.resolve_seed_exchange("maizegrain", mapping, exchanges, "kg").uuid == "uuid-maize-seed"
    assert se.resolve_seed_exchange("sugarcane", mapping, exchanges) is None
    with pytest.raises(ValueError, match="review it first"):
        se.resolve_seed_exchange("sweetcorn", mapping, exchanges)
    with pytest.raises(ValueError, match="Unit mismatch"):
        se.resolve_seed_exchange("maize grain", mapping, exchanges, "unit")
    with pytest.raises(KeyError, match="No seed mapping"):
        se.resolve_seed_exchange("sugarbeet", mapping, exchanges)
    with pytest.raises(KeyError, match="not in master data"):
        se.resolve_seed_exchange("rice", mapping, exchanges)
    assert se.suggest_seed_exchanges("maize", exchanges) == ["maize seed, for sowing"]


def _inputs(crop, quantity):
    return {"crop": crop, "seed_quantities": {crop: quantity}, "orchard_lifetime": 20.0}


def test_output_mapping_emits_exchange_and_amount(master):
    om = OutputMapping()
    om.mapSeeds(_inputs("maizegrain", 25.0))
    assert om.output["seed_exchange_name"] == "maize seed, for sowing"
    assert om.output["seed_exchange_uuid"] == "uuid-maize-seed"
    assert om.output["seed_amount_kg"] == 25.0
    om = OutputMapping()
    om.mapSeeds(_inputs("tomato_fresh", 30000.0))
    assert om.output["seed_exchange_unit"] == "unit" and om.output["seed_amount_unit"] == 30000.0


def test_perennial_plantings_are_amortised_over_the_lifetime():
    crops = dataloader.table("crop_types.csv", numeric=False)
    assert crops["asparagus_green"]["planting_amortised_over_lifetime"] == "yes"
    assert crops["apple"]["planting_amortised_over_lifetime"] == "yes"
    assert crops["wheat"]["planting_amortised_over_lifetime"] == "no"


def test_reviewed_mapping_resolves_every_legacy_crop_against_the_real_master_data():
    if config.master_data_path() is None or not config.master_data_path().is_file():
        pytest.skip("ecoinvent Master Data not configured")
    exchanges = se.master_data_exchanges()
    mapping = se.load_seed_mapping()
    seedlings = {c for c in dataloader.table("crop_types.csv", numeric=False)}
    from defaultGeneration import SEEDLINGS_BASED_CROPS, TREE_BASED_CROPS
    for crop in seedlings:
        unit = "unit" if crop in TREE_BASED_CROPS or crop in SEEDLINGS_BASED_CROPS else "kg"
        se.resolve_seed_exchange(crop, mapping, exchanges, unit)  # raises on any problem


def test_output_mapping_stops_on_unreviewed_crop(master):
    with pytest.raises(ValueError, match="review it first"):
        OutputMapping().mapSeeds(_inputs("sweetcorn", 25.0))


def test_without_master_data_the_legacy_lookup_stays(monkeypatch):
    monkeypatch.delenv(config.ENV_VAR, raising=False)
    monkeypatch.setattr(config, "CONFIG_FILE", config.REPO_ROOT / "does-not-exist.cfg")
    om = OutputMapping()
    om.mapSeeds(_inputs("wheat", 180.0))
    assert om.output["seeds_wheat"] == 180.0
    assert om.output["seed_exchange_status"].startswith("master data not configured")

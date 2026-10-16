"""Decision L42: the manure N of the FAOSTAT items mapped to both forms (cattle, buffalo, pigs, laying hens) is split
into liquid and solid manure with the manure management systems of IPCC 2019 Refinement Vol. 4 Tables 10A.6-10A.9
in the IPCC region of the country (replaces the WFLDB 50/50 rule of L29), and the same split per region gives the
world mix of the 'other' manure (L13)."""
import importlib.util
from pathlib import Path

import pytest

import dataloader
from models.manuremodel import ManureModel, LiquidManureType, SolidManureType

ROOT = Path(__file__).resolve().parents[2]
SYSTEMS = ["lagoon", "liquid_slurry", "pit_below_1_month", "pit_above_1_month", "solid_storage", "drylot",
           "pasture_range_paddock", "daily_spread", "digester", "burned_for_fuel", "poultry_manure_with_litter", "other"]


def _liquid(item, region):
    return ManureModel._ipcc_liquid_share(item, region)


def test_transcription_rows_sum_to_100_and_use_the_regions():
    rows = dataloader.rows("ipcc2019_table10a_awms.csv")
    assert len(rows) == 116
    regions = set(dataloader.table("ipcc2019_regions.csv", numeric=False))
    for row in rows:
        assert sum(float(row[system]) for system in SYSTEMS if row[system]) == pytest.approx(100.0), row
        assert row["region"] in regions and row["productivity_class"] in ("", "High", "Low"), row


@pytest.mark.parametrize("category, productivity, region, values", [
    # IPCC 2019 Refinement Vol. 4, pp. 10.119-10.126
    ("Dairy cattle", "", "North America", {"lagoon": 26, "liquid_slurry": 24, "solid_storage": 24,
                                           "pasture_range_paddock": 15, "daily_spread": 11}),
    ("Non-dairy cattle", "", "Eastern Europe", {"liquid_slurry": 64, "solid_storage": 5, "pasture_range_paddock": 31}),
    ("Buffalo non-dairy", "", "Near East and North Africa", {"solid_storage": 16, "drylot": 12,
                                                            "pasture_range_paddock": 57, "burned_for_fuel": 15}),
    ("Growing swine", "Low", "East Asia and South-East Asia", {
        "lagoon": 5, "liquid_slurry": 27, "solid_storage": 18, "drylot": 14, "pit_below_1_month": 14,
        "pit_above_1_month": 5, "daily_spread": 6, "digester": 5, "pasture_range_paddock": 6}),
    ("Breeding swine", "High", "South Asia", {"lagoon": 12, "liquid_slurry": 23, "solid_storage": 14, "drylot": 32,
                                              "pit_below_1_month": 3, "daily_spread": 8, "digester": 8}),
    ("Chicken layer", "High", "Western Europe", {"liquid_slurry": 1, "solid_storage": 20, "drylot": 21,
                                                 "pit_above_1_month": 43, "daily_spread": 1,
                                                 "poultry_manure_with_litter": 14}),
    ("Chicken", "Low", "Sub-Saharan Africa", {"pasture_range_paddock": 50, "daily_spread": 50})])
def test_transcribed_rows(category, productivity, region, values):
    row = next(r for r in dataloader.rows("ipcc2019_table10a_awms.csv") if r["animal_category"] == category
               and r["productivity_class"] == productivity and r["region"] == region)
    assert {s: float(row[s]) for s in SYSTEMS if row[s]} == values


def test_forms_of_the_systems():
    forms = {row["system"]: row["form"] for row in dataloader.rows("ipcc2019_awms_forms.csv")}
    assert set(forms) == set(SYSTEMS)
    assert {s for s, f in forms.items() if f == "liquid"} == {
        "lagoon", "liquid_slurry", "pit_below_1_month", "pit_above_1_month", "digester"}
    assert {s for s, f in forms.items() if f == "not_applied"} == {"pasture_range_paddock", "burned_for_fuel", "other"}


def test_tables_are_signed():
    for table in ("ipcc2019_awms_forms.csv", "ipcc2019_faostat_item_awms_mapping.csv",
                  "ipcc2019_m49_region_mapping.csv"):
        for row in dataloader.rows(table):
            assert row["status"] == "confirmed" and row["reviewed_by"], (table, row)


def test_items_of_both_forms_have_ipcc_categories():
    forms = {}
    for row in dataloader.rows("manure_other_faostat_mapping.csv"):
        forms.setdefault(row["faostat_item"], set()).add(row["form"])
    both = {item for item, f in forms.items() if f == {"liquid", "solid"}}
    assert {row["faostat_item"] for row in dataloader.rows("ipcc2019_faostat_item_awms_mapping.csv")} == both


@pytest.mark.parametrize("category", ["Sheep meat", "Sheep dairy", "Goats", "Chicken broiler"])
def test_items_of_the_solid_form_only_have_no_liquid_system_in_ipcc(category):
    # sheep, goats (proxy of horses, asses and mules, Table 10A.9 note 1) and broilers stay solid only
    forms = {row["system"]: row["form"] for row in dataloader.rows("ipcc2019_awms_forms.csv")}
    for row in dataloader.rows("ipcc2019_table10a_awms.csv"):
        if row["animal_category"] == category:
            assert not any(row[s] for s, f in forms.items() if f == "liquid"), row


@pytest.mark.parametrize("item, region, share", [
    ("Cattle, dairy", "North America", (26 + 24) / (26 + 24 + 24 + 11)),
    ("Cattle, dairy", "Western Europe", 43 / (43 + 29 + 2)),
    ("Cattle, dairy", "South Asia", 0.0),  # dry lot and solid storage only
    ("Cattle, dairy", "Russian Federation", 5 / (5 + 74 + 1)),  # Eastern Europe rows
    ("Buffalo", "Western Europe", 34 / (34 + 63)),  # dairy row only
    ("Buffalo", "Eastern Europe", (18 / (18 + 68 + 1) + 9 / (9 + 64)) / 2),  # mean of dairy and non-dairy
    ("Buffalo", "Sub-Saharan Africa", 0.0),  # no buffalo rows: non-dairy cattle
    ("Swine, market", "Western Europe", (6 + 51 + 2 + 26) / 100),  # high productivity (Tier 1, Europe)
    ("Swine, market", "East Asia and South-East Asia", (5 + 27 + 14 + 5 + 5) / (100 - 6)),  # low productivity
    ("Swine, breeding", "Russian Federation", 24 / 100),
    ("Chickens, layers", "Western Europe", (1 + 43) / 100),
    ("Chickens, layers", "Russian Federation", 1.0),  # pit > 1 month = laying hens - slurry
    ("Chickens, layers", "East Asia and South-East Asia", 0.0)])  # low productivity: daily spread
def test_ipcc_liquid_shares(item, region, share):
    assert _liquid(item, region) == pytest.approx(share)


def test_wfldb_rule_where_ipcc_gives_no_managed_system():
    # Oceania: non-dairy cattle 100 % pasture, no buffalo rows; FAOSTAT still has manure applied (AU feedlots)
    assert _liquid("Cattle, non-dairy", "Oceania") is None and _liquid("Buffalo", "Oceania") is None
    n = ManureModel._n_per_type({("Oceania", "Cattle, non-dairy"): 100.0})
    assert n[LiquidManureType][LiquidManureType.cattle] == n[SolidManureType][SolidManureType.cattle] == 50.0


@pytest.mark.parametrize("country, region", [
    ("US", "North America"), ("FR", "Western Europe"), ("FI", "Western Europe"), ("CS", "Eastern Europe"),
    ("UA", "Eastern Europe"), ("RU", "Russian Federation"), ("NZ", "Oceania"), ("CN", "East Asia and South-East Asia"),
    ("IN", "South Asia"), ("LK", "South Asia"), ("CR", "Latin America and the Caribbean"),
    ("TR", "Near East and North Africa"), ("MA", "Near East and North Africa"), ("ZA", "Sub-Saharan Africa")])
def test_region_of_the_tool_countries(country, region):
    assert ManureModel.ipcc_region(country) == region


def test_india_cattle_manure_is_solid():
    liquid, solid = ManureModel.country_shares("IN")
    assert liquid[LiquidManureType.cattle] == 0.0 and liquid[LiquidManureType.pig] == pytest.approx(1.0)
    assert ManureModel.liquid_n_fraction("IN") < 0.01


def test_regions_add_up_to_the_world():
    world = dataloader.table("faostat_manure_n_applied_world.csv")
    total = {}
    for row in dataloader.rows("faostat_manure_n_applied_ipcc_region.csv"):
        total[row["item"]] = total.get(row["item"], 0.0) + float(row["n_applied_mean_2021_2023_kg"])
    assert set(total) == set(world)
    for item, n in total.items():
        assert n == pytest.approx(world[item]["n_applied_mean_2021_2023_kg"], abs=1.0), item


def test_world_excludes_the_faostat_china_aggregate():
    excluded = [row for row in dataloader.rows("ipcc2019_country_region.csv") if row["rule"] == "excluded"]
    assert [(row["m49_code"], row["faostat_area"]) for row in excluded] == [("159", "China")]
    assert len(dataloader.rows("ipcc2019_country_region.csv")) == 198


def test_other_liquid_mix_splits_each_region():
    n = {}
    for row in dataloader.rows("faostat_manure_n_applied_ipcc_region.csv"):
        n[(row["ipcc_region"], row["item"])] = float(row["n_applied_mean_2021_2023_kg"])
    cattle = sum(v * _liquid(item, region) for (region, item), v in n.items()
                 if item in ("Cattle, dairy", "Cattle, non-dairy", "Buffalo") and _liquid(item, region) is not None)
    cattle += sum(v / 2 for (region, item), v in n.items()
                  if item in ("Cattle, dairy", "Cattle, non-dairy", "Buffalo") and _liquid(item, region) is None)
    pig = sum(v * _liquid(item, region) for (region, item), v in n.items() if item in ("Swine, market",
                                                                                       "Swine, breeding"))
    hens = sum(v * _liquid(item, region) for (region, item), v in n.items() if item == "Chickens, layers")
    units = {LiquidManureType.cattle: cattle, LiquidManureType.pig: pig, LiquidManureType.laying_hens: hens}
    units = {k: v / ManureModel._content(k, "n_total") for k, v in units.items()}
    shares = ManureModel._other_shares(LiquidManureType.other)
    for k, v in units.items():
        assert shares[k] == pytest.approx(v / sum(units.values()))


def test_tables_equal_the_downloads():
    script = ROOT / "scripts" / "build_faostat_manure_ipcc_region.py"
    spec = importlib.util.spec_from_file_location("build_faostat_manure_ipcc_region", script)
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    faostat = dataloader.EXTERNAL_DATA_DIR / build.FAOSTAT_FILE
    m49 = dataloader.EXTERNAL_DATA_DIR / build.M49_FILE
    if not (faostat.is_file() and m49.is_file()):
        pytest.skip("FAOSTAT or UNSD M49 download not in data/external_data/")
    for rows, name in zip(build.build(faostat, m49), (build.COUNTRY_OUTPUT, build.REGION_OUTPUT, build.WORLD_OUTPUT)):
        assert [{k: str(v) for k, v in row.items()} for row in rows] == [dict(r) for r in dataloader.rows(name)]

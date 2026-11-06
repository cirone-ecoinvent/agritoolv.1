"""Decision L65: emissions of the pesticide active ingredients with the OLCA-Pest default fractions (Nemecek et al.
2022, Table 2 and section 3.4), as in the OLCApest mapping tool (sheet 'calculation pathway' step 8, sheet OLCA CALC):
air = f_air x m; soil, agricultural = (f_soil + f_crop + f_off_field x agri) x m; soil, forestry = f_off_field x forest
x m; water, surface water = f_off_field x water x m; land shares of the country from FAOSTAT Land Use
(data/faostat_country_land_shares.csv, built by scripts/build_faostat_country_land_shares.py)."""
import csv
import importlib.util
from pathlib import Path

import pytest

import dataloader
from models import olcapestmodel
from models.hmmodel import HmModel
from models.olcapestmodel import OlcaPestModel, land_shares, scenario, split

ROOT = Path(__file__).resolve().parents[2]
FAOSTAT_ZIP = dataloader.EXTERNAL_DATA_DIR / "Inputs_LandUse_E_All_Data_(Normalized).zip"
M49_FILE = dataloader.EXTERNAL_DATA_DIR / "UNSD — Methodology.csv"
needs_faostat = pytest.mark.skipif(not (FAOSTAT_ZIP.is_file() and M49_FILE.is_file()),
                                   reason="FAOSTAT Land Use download or UNSD M49 file not in data/external_data")

# OLCA CALC rows 3-5 of the OLCApest mapping tool, column Italy (FAOSTAT Land Use 2020, downloaded 2026-07-08)
IT_OLCA_CALC_2020 = {"agri": 0.560164507, "forest": 0.418813736, "water": 0.021021757}
# Pooideae / Hrb-post, scenario SC83 of OLCA CALC (c_PrimAir, c_PrimSoil, c_PrimCrop, c_PrimOffField)
SC83 = {"f_air": 0.1, "f_soil": 0.667104385, "f_crop": 0.222368128, "f_off_field": 0.010527486}


def _build_module():
    spec = importlib.util.spec_from_file_location("build_land", ROOT / "scripts" / "build_faostat_country_land_shares.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _italy_2024_by_hand():
    # FAOSTAT Land Use 2024, Italy, element Area (1000 ha): Country area, Agricultural land, Forest land, Inland waters
    country, agri, forest, water = 30207.0, 12901.53, 9409.47, 635.0
    a, f, w = agri / country, forest / country, water / country
    delta = a + f + w - 1.0
    return {"agri": a - delta * a / (a + f), "forest": f - delta * f / (a + f), "water": w}


def test_split_reproduces_the_olca_tool_for_wheat_italy_2020():
    # FC's check values: glyphosate 1500 g on wheat (Pooideae) with the Hrb-post fractions, Italy shares of OLCA CALC
    parts = split(1500.0, SC83, IT_OLCA_CALC_2020)
    assert parts["air"] == pytest.approx(150.000, abs=1e-3)
    assert parts["soil_agricultural"] == pytest.approx(1343.054, abs=1e-3)
    assert parts["soil_forestry"] == pytest.approx(6.614, abs=1e-3)
    assert parts["water_surface"] == pytest.approx(0.332, abs=1e-3)
    # the fractions of SC83 sum to 0.999999999
    assert sum(parts.values()) == pytest.approx(1500.0, abs=1e-5)


def test_split_with_the_2024_shares_of_italy():
    shares = _italy_2024_by_hand()
    assert land_shares("IT")["agri"] == pytest.approx(shares["agri"], abs=1e-9)
    assert land_shares("IT")["forest"] == pytest.approx(shares["forest"], abs=1e-9)
    assert land_shares("IT")["water"] == pytest.approx(shares["water"], abs=1e-9)
    parts = split(1500.0, SC83, land_shares("IT"))
    assert parts["air"] == pytest.approx(150.000, abs=1e-3)
    assert parts["soil_agricultural"] == pytest.approx(1343.148, abs=1e-3)
    assert parts["soil_forestry"] == pytest.approx(6.520, abs=1e-3)
    assert parts["water_surface"] == pytest.approx(0.332, abs=1e-3)


def test_model_wheat_italy_glyphosate_uses_its_olca_pest_class():
    # glyphosate is Hrb-pre in sheet contextualized_Pest: Pooideae / Hrb-pre = SC88
    # (f_air 0.1, f_soil 0.888763865, f_crop 0, f_off_field 0.011236135); 1500 g = 1.5 kg; Italy 2024 shares
    out = OlcaPestModel({"specified_pesticides": {"part_herbicides_glyphosate": 1500.0}, "crop": "wheat",
                         "country": "IT"}).compute()["pesti_herbicides_glyphosate"]
    shares = _italy_2024_by_hand()
    off_field = 0.011236135 * 1.5
    assert out["air"] == pytest.approx(0.15, rel=1e-12)
    assert out["soil_agricultural"] == pytest.approx(0.888763865 * 1.5 + off_field * shares["agri"], rel=1e-7)
    assert out["soil_forestry"] == pytest.approx(off_field * shares["forest"], rel=1e-7)
    assert out["water_surface"] == pytest.approx(off_field * shares["water"], rel=1e-7)
    assert out["soil_forestry"] == pytest.approx(0.0069587, abs=1e-7)


def test_tree_herbicides_without_a_scenario_take_hrb_post():
    for pest_class in ("Hrb-pre", "Hrb-Avg"):
        fractions = scenario("apple", pest_class)
        assert (fractions["scenario_id"], fractions["pest_class"]) == ("SC23", "Hrb-post")
    assert scenario("wheat", "Hrb-pre")["scenario_id"] == "SC88"


def test_every_crop_and_class_has_fractions_summing_to_one():
    classes = {row["olca_pest_class"] for row in dataloader.rows(olcapestmodel.CLASS_TABLE)}
    shares = land_shares("IT")
    for crop in dataloader.table("crop_types.csv", numeric=False):
        for pest_class in classes:
            assert sum(split(1.0, scenario(crop, pest_class), shares).values()) == pytest.approx(1.0, abs=1e-8), \
                (crop, pest_class)


def test_non_substances_have_no_emission_and_unknown_keys_fail():
    inputs = {"crop": "wheat", "country": "IT",
              "specified_pesticides": {"part_herbicides_other": 100.0, "part_fungicides_fungicide_unspecified": 50.0}}
    assert OlcaPestModel(inputs).compute() == {}
    inputs["specified_pesticides"] = {"part_herbicides_not_a_substance": 1.0}
    with pytest.raises(KeyError):
        OlcaPestModel(inputs).compute()


def test_every_tool_country_has_its_own_land_shares():
    for country, row in dataloader.table("faostat_country_mapping.csv", numeric=False).items():
        shares = land_shares(country)
        assert shares["m49_code"] == row["m49_code"], country
        assert shares["agri"] + shares["forest"] + shares["water"] == pytest.approx(1.0, abs=1e-8)
    assert land_shares("CS")["area"] == "Serbia"
    assert land_shares("GLO")["area"] == "World"


def test_country_without_shares_falls_back_to_its_subregion(monkeypatch):
    # Bosnia and Herzegovina (M49 070) has no Country area in FAOSTAT 2024: Southern Europe (M49 039)
    real_table = dataloader.table

    def table(filename, *args, **kwargs):
        if filename == olcapestmodel.COUNTRY_MAPPING:
            return {"BA": {"m49_code": "070"}}
        return real_table(filename, *args, **kwargs)

    monkeypatch.setattr(olcapestmodel.dataloader, "table", table)
    assert land_shares("BA")["m49_code"] == "039"


def test_land_share_table():
    rows = dataloader.rows(olcapestmodel.LAND_SHARES_TABLE)
    assert len({row["m49_code"] for row in rows}) == len(rows)
    assert {row["year"] for row in rows} == {"2024"}
    for row in rows:
        if row["agri_share"]:
            total = sum(float(row[c]) for c in ("agri_share", "forest_share", "water_share"))
            assert total == pytest.approx(1.0, abs=1e-8), row["area"]
    namibia = next(row for row in rows if row["m49_code"] == "516")
    assert (namibia["area_type"], namibia["iso2"]) == ("country", "NA")


def test_class_table_covers_every_pesticide_flow_in_four_compartments():
    classes = dataloader.table(olcapestmodel.CLASS_TABLE, numeric=False)
    fraction_classes = {row["pest_class"] for row in dataloader.rows(olcapestmodel.FRACTIONS_TABLE)}
    assert all(row["olca_pest_class"] in fraction_classes for row in classes.values())
    with open(dataloader.DATA_DIR / "elementary_flow_alignment.csv", newline="", encoding="utf-8") as f:
        flows = {(r["model_variable"], r["compartment"], r["subcompartment"]): r for r in csv.DictReader(f)}
    for variable, row in classes.items():
        for prefix, compartment in (("pestiair_", ("air", "non-urban air or from high stacks")),
                                    ("pestisoil_", ("soil", "agricultural")), ("pestiforestry_", ("soil", "forestry")),
                                    ("pestiwater_", ("water", "surface water"))):
            flow = flows[(variable.replace("pesti_", prefix, 1),) + compartment]
            assert flow["md312_name"] == row["md312_name"] and flow["md312_uuid"], variable


def test_heavy_metal_field_fraction_uses_the_same_scenario():
    model = HmModel.__new__(HmModel)
    model.crop = "apple"
    # Fruit trees temperate / Fun: f_soil + f_crop
    fractions = scenario("apple", "Fun")
    assert model._pesticide_field_fraction("Fun") == pytest.approx(fractions["f_soil"] + fractions["f_crop"])


@needs_faostat
def test_script_on_2020_reproduces_olca_calc_for_italy():
    year, rows = _build_module().build(2020, FAOSTAT_ZIP, M49_FILE)
    italy = next(row for row in rows if row["iso2"] == "IT")
    assert year == 2020
    for key, value in IT_OLCA_CALC_2020.items():
        assert float(italy[key + "_share"]) == pytest.approx(value, abs=1e-9)


@needs_faostat
def test_script_reads_namibia_as_a_country_and_reproduces_the_table():
    year, rows = _build_module().build(None, FAOSTAT_ZIP, M49_FILE)
    namibia = next(row for row in rows if row["m49_code"] == "516")
    assert (namibia["area_type"], namibia["iso2"]) == ("country", "NA")
    table = {row["m49_code"]: row for row in dataloader.rows(olcapestmodel.LAND_SHARES_TABLE)}
    assert year == 2024 and len(rows) == len(table)
    for row in rows:
        assert all(str(row.get(c, "")) == table[row["m49_code"]][c] for c in ("agri_share", "forest_share", "water_share"))

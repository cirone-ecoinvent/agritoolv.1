"""Tests for the single data-loading module (src/legacy_model/dataloader.py)."""
import dataloader as dl


def test_params_are_read_from_csv():
    assert dl.param("ef1_direct_n2o") == 0.01
    assert dl.param("hm_accumulation_factor") == 1.86


def test_metal_tables_na_becomes_zero():
    metals = ("Cd", "Cu", "Zn", "Pb", "Ni", "Cr", "Hg")
    leaching = dl.single_metal_row("hm_leaching_mg_per_ha_yr.csv", metals)
    assert leaching["Ni"] == 0.0 and leaching["Zn"] == 33000.0
    rice = dl.metal_row("hm_plant_content_mg_per_kg_dm.csv", "rice_grains", metals)
    assert rice["Hg"] == 0.0 and rice["Cu"] == 5.27


def test_table_keeps_text_columns():
    fert = dl.table("hm_mineral_fertiliser_mg_per_kg_nutrient.csv")
    assert fert["urea"]["nutrient"] == "N"
    assert fert["urea"]["Zn"] == 95.65


def test_every_data_file_is_registered_in_sources():
    registered = {row["file"] for row in dl.rows("sources.csv")}
    on_disk = {p.name for p in dl.DATA_DIR.iterdir() if p.name != "sources.csv"}
    assert on_disk <= registered, "unregistered data files: %s" % sorted(on_disk - registered)

"""Tests for the single data-loading module (src/legacy_model/dataloader.py)."""
import dataloader as dl


def test_params_are_read_from_csv():
    assert dl.param("ef1_direct_n2o") == 0.01
    assert dl.param("hm_accumulation_factor") == 1.86


def test_hm_entry_reads_the_salca2023_table_by_name():
    leaching = dl.hm_entry("leaching")
    assert leaching["Ni"] == 0.0 and leaching["Zn"] == 33000.0
    rice = dl.hm_entry("rice")
    assert rice["Hg"] == 0.0 and rice["Cu"] == 5.27 and rice["dm"] == 0.87


def test_hm_entry_names_the_table_when_a_row_is_missing():
    import pytest
    with pytest.raises(KeyError, match="hm_salca2023_table1.csv"):
        dl.hm_entry("quinoa")


def test_table_keeps_text_columns():
    row = dl.table("hm_salca2023_table1.csv", key_column="name_en")["N urea (kg N)"]
    assert row["concentration_unit"] == "mg/kg N"
    assert row["Zn"] == 95.7


def test_every_data_file_is_registered_in_sources():
    registered = {row["file"] for row in dl.rows("sources.csv")}
    on_disk = {p.name for p in dl.DATA_DIR.iterdir() if p.name != "sources.csv"}
    assert on_disk <= registered, "unregistered data files: %s" % sorted(on_disk - registered)

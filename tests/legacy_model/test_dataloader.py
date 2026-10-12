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


def test_manure_composition_references_existing_rows_and_weights_sum_to_one():
    from collections import defaultdict
    contents = dl.table("grudaf2009_table39.csv")
    emep = {(r["livestock"], r["manure_type"]) for r in dl.rows("emep2023_3b_table3_9.csv")}
    weights = defaultdict(float)
    for row in dl.rows("manure_type_composition.csv"):
        assert row["grudaf_row_id"] in contents
        assert (row["emep_livestock"], row["emep_manure_type"]) in emep
        weights[row["manure_type"]] += float(row["weight"])
    assert all(abs(w - 1.0) < 1e-12 for w in weights.values()), dict(weights)


def test_faostat_mapping_uses_existing_items_and_manure_types():
    items = dl.table("faostat_manure_n_applied_world.csv")
    composition = {row["manure_type"] for row in dl.rows("manure_type_composition.csv")}
    for row in dl.rows("manure_other_faostat_mapping.csv"):
        assert row["faostat_item"] in items
        assert row["manure_type"] in composition and row["manure_type"].startswith(row["form"])


def test_fertiliser_basis_matches_the_confirmed_alignment_rows():
    from collections import Counter
    alignment = {r["model_variable"]: r for r in dl.rows("intermediate_exchange_alignment.csv")}
    basis = dl.table(dl.FERTILISER_BASIS_TABLE)
    for model_variable, row in basis.items():
        assert alignment[model_variable]["status"] == "confirmed"
        assert alignment[model_variable]["md312_name"] == row["md312_name"]
        assert row["amount_basis"] in ("N", "P2O5", "K2O", "Ca")
    groups = Counter(row["compound_group"] for row in basis.values() if row["compound_group"])
    assert groups and all(n == 2 for n in groups.values()), groups


def test_every_crop_has_an_olca_pest_archetype_with_fungicide_fractions():
    fractions = {(r["crop_archetype"], r["pest_class"]) for r in dl.rows("olca_pest_default_fractions.csv")}
    mapping = dl.table("pesticide_crop_archetype_mapping.csv", numeric=False)
    classes = {r["olca_pest_class"] for r in dl.rows("hm_pesticide_mapping.csv")}
    for crop in dl.table("crop_types.csv", numeric=False):
        for pest_class in classes:
            assert (mapping[crop]["olca_crop_archetype"], pest_class) in fractions, crop
    for r in dl.rows("olca_pest_default_fractions.csv"):
        total = sum(float(r[k]) for k in ("f_air", "f_soil", "f_crop", "f_off_field"))
        assert abs(total - 1.0) < 1e-6, r["scenario_id"]


def test_organic_fertiliser_composition_covers_every_type_with_an_emep_category():
    from models.otherorganicfertilisermodel import CompostType, SludgeType
    composition = dl.table("organic_fertiliser_composition.csv")
    categories = {r["nfr"] for r in dl.rows("emep2023_3d_table3_1.csv") if r["pollutant"] == "NH3"}
    manure_rows = {(r["nfr"], r["livestock"], r["manure_type"]) for r in dl.rows("emep2023_3b_table3_9.csv")
                   if r["ef_application"]}
    assert set(composition) == {t.value for t in (*CompostType, *SludgeType)}
    for fert_type, row in composition.items():
        if row["emep_nfr"].startswith("3B"):  # livestock manure, decision L21
            assert (row["emep_nfr"], row["emep_livestock"], row["emep_manure_type"]) in manure_rows, fert_type
        else:
            assert row["emep_nfr"] in categories, fert_type
        assert 0.0 <= row["tan_kg_n_per_t_fm"] <= row["n_total_kg_per_t_fm"], fert_type


def test_luc_tables_use_known_crops_countries_and_products():
    crops = dl.table("crop_types.csv", numeric=False)
    countries = dl.table("luc_blonk_country_expansion.csv")
    for row in dl.rows("luc_blonk_crop_expansion.csv"):
        assert row["crop"] in crops and row["country"] in countries, row
        assert float(row["rec_crop_specific"]) >= 0.0, row
    products = {(r["crop_type"], r["flooded"]) for r in dl.rows("luc_product_mapping.csv")}
    assert {(r["crop_type"], r["flooded"]) for r in crops.values()} <= products
    alignment = {r["md312_name"]: r for r in dl.rows("intermediate_exchange_alignment.csv")}
    for row in dl.rows("luc_product_mapping.csv"):
        assert alignment[row["md312_name"]]["status"] == "confirmed"
        assert alignment[row["md312_name"]]["md312_unit"] == "ha"

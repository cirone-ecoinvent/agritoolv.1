"""Decision L45: default mineral fertiliser mixes per country from IFASTAT fertilizer consumption by product
(2021-2023), assigned to the tool fertiliser types by data/ifastat_product_type_mapping.csv; only the derived shares
are in the repository (data/ifastat_fertiliser_mix.csv)."""
import importlib.util
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS
from defaultTables import FERT_N_RATIO_PER_COUNTRY, FERT_P_RATIO_PER_COUNTRY, FERT_K_RATIO_PER_COUNTRY
from models.fertilisermodel import NFertiliserType, PFertiliserType, KFertiliserType

ROOT = Path(__file__).resolve().parents[2]
COUNTRIES = [row["country"] for row in dataloader.rows("faostat_country_mapping.csv") if row["country"] != "GLO"]
TABLES = ((FERT_N_RATIO_PER_COUNTRY, NFertiliserType), (FERT_P_RATIO_PER_COUNTRY, PFertiliserType),
          (FERT_K_RATIO_PER_COUNTRY, KFertiliserType))


def _build_module():
    spec = importlib.util.spec_from_file_location("build", ROOT / "scripts" / "build_ifastat_fertiliser_mix.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_tool_country_has_mixes_of_all_types_summing_to_one():
    for table, fertiliser_types in TABLES:
        assert sorted(table) == sorted(COUNTRIES)
        for country in COUNTRIES:
            assert set(table[country]) == set(fertiliser_types)
            assert sum(table[country].values()) == pytest.approx(1.0)
            assert min(table[country].values()) >= 0.0


def test_stored_shares_sum_to_one_before_scaling():
    totals = defaultdict(float)
    for row in dataloader.rows("ifastat_fertiliser_mix.csv"):
        totals[(row["country"], row["nutrient"])] += float(row["share"])
    assert len(totals) == 3 * len(COUNTRIES)
    assert all(total == pytest.approx(1.0, abs=1e-5) for total in totals.values())


def test_product_fractions_sum_to_one_and_the_left_out_products():
    fractions = defaultdict(Fraction)
    left_out = []
    for row in dataloader.rows("ifastat_product_type_mapping.csv"):
        if row["fertiliser_type"]:
            fractions[(row["ifastat_nutrient"], row["ifastat_product"])] += Fraction(row["fraction"])
        else:
            left_out.append((row["ifastat_nutrient"], row["ifastat_product"]))
    assert all(total == 1 for total in fractions.values())
    assert left_out == [("Nitrogen", "Other"), ("Potassium", "NPK"), ("Potassium", "PK")]


def test_npk_nitrogen_takes_the_emep_factors_of_npk_mixtures():
    factors = {row["emep_fertiliser_type"]: (float(row["ef_normal_ph"]), float(row["ef_high_ph"]))
               for row in dataloader.rows("emep2023_3d_table3_2.csv")}
    emep_type = {row["legacy_fertiliser_type"]: row["emep_fertiliser_type"]
                 for row in dataloader.rows("emep2023_fertiliser_type_mapping.csv")}
    npk = [(row["fertiliser_type"], float(Fraction(row["fraction"])))
           for row in dataloader.rows("ifastat_product_type_mapping.csv")
           if (row["ifastat_nutrient"], row["ifastat_product"]) == ("Nitrogen", "NPK")]
    for ph in (0, 1):
        assert sum(fraction * factors[emep_type[fertiliser_type]][ph] for fertiliser_type, fraction in npk) ==             pytest.approx(factors["NPK mixtures"][ph])


def test_finland_npk_shares_and_world_potassium_mix():
    # FI uses only CAN, NPK and a little urea in IFASTAT 2021-2023: the NPK N and P2O5 go 1/3 each to MAP, DAP and
    # ammonium nitrate phosphate; its K2O is only in NPK (left out), so FI takes the world potassium mix
    n, p, k = FERT_N_RATIO_PER_COUNTRY["FI"], FERT_P_RATIO_PER_COUNTRY["FI"], FERT_K_RATIO_PER_COUNTRY["FI"]
    assert n[NFertiliserType.potassium_nitrate] == 0.0
    for np_type in (NFertiliserType.di_ammonium_phosphate, NFertiliserType.an_phosphate):
        assert n[np_type] == pytest.approx(n[NFertiliserType.mono_ammonium_phosphate], rel=1e-5)
    for p_type in (PFertiliserType.mono_ammonium_phosphate, PFertiliserType.di_ammonium_phosphate,
                   PFertiliserType.an_phosphate):
        assert p[p_type] == pytest.approx(1 / 3, rel=1e-5)
    notes = {(row["country"], row["nutrient"]): row["note"] for row in dataloader.rows("ifastat_fertiliser_mix.csv")}
    assert {key for key, note in notes.items() if note} == {("FI", "K2O")}
    assert max(k, key=k.get) == KFertiliserType.potassium_salt


def test_default_fertiliser_quantities_use_the_country_mixes():
    defaults = DefaultValuesWrapper({"crop": "wheat", "country": "FR", "yield_main_product_per_crop_cycle": 7000.0},
                                    DEFAULTS_VALUES_GENERATORS)
    for proportions, quantities, amount, table in (
            ("n_fertiliser_proportions", "n_fertiliser_quantities", "nitrogen_from_mineral_fert", FERT_N_RATIO_PER_COUNTRY),
            ("p_fertiliser_proportions", "p_fertiliser_quantities", "p2O5_from_mineral_fert", FERT_P_RATIO_PER_COUNTRY),
            ("k_fertiliser_proportions", "k_fertiliser_quantities", "k2O_from_mineral_fert", FERT_K_RATIO_PER_COUNTRY)):
        assert defaults[proportions] == table["FR"]
        for fertiliser_type, quantity in defaults[quantities].items():
            assert quantity == pytest.approx(defaults[amount] * table["FR"][fertiliser_type])


def test_mix_table_equals_the_ifastat_export():
    build = _build_module()
    source = dataloader.EXTERNAL_DATA_DIR / build.IFASTAT_FILE
    if not source.is_file():
        pytest.skip("IFASTAT export not in data/external_data/ (IFA member data, not in the repository)")
    rebuilt = [{key: str(value) for key, value in row.items()} for row in build.build(source)]
    assert rebuilt == [dict(row) for row in dataloader.rows("ifastat_fertiliser_mix.csv")]

"""Decision L33: WFLDB level 2 mineral N, P2O5 and K2O (Guidelines v3.0 section 3.6.1). The level 1 nutrient input
(L28, L31, L32) is corrected with k = (IFA rate + manure) / need at the default yield and default manure, so that at
the default yield the default mineral fertiliser equals the rate of IFA Fertilizer Use by Crop (Ludemann et al. 2022),
FUBC 9 rates brought to 2021-2023 with the FAOSTAT use per area of cropland."""
import importlib.util
import statistics
from pathlib import Path

import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS, MineralNitrogenDefaultGenerator, \
    MineralPhosphorusPotassiumDefaultGenerator as PK
from defaultTables import IFA_MINERAL_FERTILISER_PER_CROP_PER_COUNTRY as IFA, \
    PK_PER_KG_MAIN_PRODUCT_PER_CROP as PK_PER_KG
from models.manuremodel import LiquidManureType

ROOT = Path(__file__).resolve().parents[2]
FIELDS = {"n": "nitrogen_from_mineral_fert", "p2o5": "p2O5_from_mineral_fert", "k2o": "k2O_from_mineral_fert"}


def _defaults(**inputs):
    return DefaultValuesWrapper(inputs, DEFAULTS_VALUES_GENERATORS)


def _fubc(fubc_country, fubc_crop):
    rows = [r for r in dataloader.rows("ifa_fubc_rates.csv")
            if r["fubc_country"] == fubc_country and r["fubc_crop"] == fubc_crop]
    assert len(rows) == 1
    return rows[0]


def _scale(country, nutrient):
    row = next(r for r in dataloader.rows("faostat_fertiliser_use_country.csv")
               if r["country"] == country and r["nutrient"] == nutrient)
    return float(row["target_kg_per_ha_cropland"]) / float(row["base_kg_per_ha_cropland"])


def test_fubc9_rate_brought_to_2021_2023():
    wheat = _fubc("France", "Wheat")
    for nutrient in ("N", "P2O5", "K2O"):
        expected = float(wheat[nutrient.lower() + "_kg_per_ha"]) * _scale("FR", nutrient)
        assert IFA["wheat"]["FR"][nutrient.lower()] == pytest.approx(expected)


def test_time_factor_base_is_three_years_around_the_fubc_year():
    # decision L35: base = FUBC 9 reference year with the year before and after, target = 2021-2023
    use = dataloader.rows("faostat_fertiliser_use_country.csv")
    for row in use:
        years = [int(y) for y in row["base_years"].split()]
        assert years == list(range(years[0], years[0] + 3)) and row["target_years"] == "2021-2023", row
    assert {r["reference_years"] for r in dataloader.rows("ifa_fubc_rates.csv") if r["fubc_country"] == "France"} \
        == {"2018"}
    assert {r["base_years"] for r in use if r["country"] in ("FR", "GH", "CS")} == {"2017 2018 2019"}


def test_earlier_report_without_time_scaling():
    # FUBC 5 Ecuador 1995, banana: 300 / 20 / 400 kg N / P2O5 / K2O per fertilised ha on 70 % of the area
    assert IFA["banana"]["EC"] == pytest.approx({"n": 210.0, "p2o5": 14.0, "k2o": 280.0})
    assert _scale("EC", "N") != pytest.approx(1.0)  # used for the region rates only (decision L37)


def test_best_level_and_area_weighting():
    # exact before group: orange BR from 'Orange', lemon BR from 'Fruits & Treenuts'
    orange, fruits = _fubc("Brazil", "Orange"), _fubc("Brazil", "Fruits & Treenuts")
    assert IFA["orange_fresh"]["BR"]["n"] == pytest.approx(float(orange["n_kg_per_ha"]) * _scale("BR", "N"))
    assert IFA["lemon"]["BR"]["n"] == pytest.approx(float(fruits["n_kg_per_ha"]) * _scale("BR", "N"))
    # FUBC 5 Kenya: irrigated rice 60 kg N on 100 % of 13 kha, rainfed rice 60 kg N on 30 % of 6 kha; no K2O value
    assert IFA["rice"]["KE"]["n"] == pytest.approx((60.0 * 13000 + 18.0 * 6000) / 19000)
    assert IFA["rice"]["KE"]["k2o"] is None


def test_countries_without_fubc_take_their_ifa_region():
    # decision L37: median over the FUBC 9 countries of the region, the rows of each country combined by area
    mapping = {r["fubc_crop"] for r in dataloader.rows("ifa_fubc_crop_mapping.csv")
               if r["match"] == "exact" and "wheat" in r["crops"].split()}
    per_country = {}
    for r in dataloader.rows("ifa_fubc_rates.csv"):
        if r["region_ifa"] == "Africa" and r["fubc_report"] == "9" and r["fubc_crop"] in mapping:
            per_country.setdefault(r["fubc_country"], []).append(r)
    assert len(per_country) > 3
    rates = [sum(float(r["n_kg_per_ha"]) * float(r["area_ha"]) for r in rows) / sum(float(r["area_ha"]) for r in rows)
             for rows in per_country.values()]
    assert IFA["wheat"]["GH"]["n"] == pytest.approx(statistics.median(rates) * _scale("GH", "N"))


@pytest.mark.parametrize("crop, country", [
    ("wheat", "FR"), ("rice", "IN"), ("potato", "IN"), ("sugarbeet", "FR"), ("soybean", "AR"), ("apple", "FR"),
    ("coffee_arabica", "BR"), ("banana", "EC"), ("wheat", "GH"), ("olive", "IL")])
def test_default_at_the_default_yield_is_the_ifa_rate(crop, country):
    defaults = _defaults(crop=crop, country=country)
    for nutrient, field in FIELDS.items():
        assert defaults[field] == pytest.approx(IFA[crop][country][nutrient])


def _manure(defaults, nutrient):
    return PK.balance(defaults, nutrient)[1]


def test_level2_follows_the_yield_and_the_manure_in_use():
    reference = _defaults(crop="potato", country="DE")
    yield_ref = reference["yield_main_product_per_crop_cycle"]
    pig = dict.fromkeys(LiquidManureType, 0.0)
    pig[LiquidManureType.pig] = 1.0
    defaults = _defaults(crop="potato", country="DE", yield_main_product_per_crop_cycle=1.5 * yield_ref,
                         total_manureliquid=20.0, liquid_manure_proportions=pig, total_manuresolid=0.0)
    # N: IFA rate x N uptake / N uptake at the default yield (template manure not used, as in L28)
    assert defaults["nitrogen_from_mineral_fert"] == pytest.approx(1.5 * IFA["potato"]["DE"]["n"])
    for nutrient in ("p2o5", "k2o"):
        k = (IFA["potato"]["DE"][nutrient] + _manure(reference, nutrient)) / (yield_ref * PK_PER_KG["potato"][nutrient])
        expected = max(0.0, k * 1.5 * yield_ref * PK_PER_KG["potato"][nutrient] - _manure(defaults, nutrient))
        assert defaults[FIELDS[nutrient]] == pytest.approx(expected)
    assert _manure(defaults, "p2o5") == pytest.approx(35.0)  # 10 m3 undiluted pig slurry (GRUDAF Table 39)


@pytest.mark.parametrize("crop, country, nutrient", [
    ("cocoa", "CI", "n"), ("cocoa", "CI", "p2o5"), ("mint", "US", "p2o5"), ("rice", "KE", "k2o")])
def test_level1_without_ifa_rate(crop, country, nutrient):
    defaults = _defaults(crop=crop, country=country)
    assert IFA.get(crop, {}).get(country, {}).get(nutrient) is None
    level1 = MineralNitrogenDefaultGenerator.level1(defaults) if nutrient == "n" else PK.level1(defaults, nutrient)
    assert defaults[FIELDS[nutrient]] == pytest.approx(level1)


def test_mappings_are_signed_and_consistent():
    rates = dataloader.rows("ifa_fubc_rates.csv")
    names = {r["fubc_crop"] for r in rates}
    regions = {r["fubc_country"]: r["region_ifa"] for r in rates}
    crops = {r["crop"] for r in dataloader.rows("crop_types.csv")}
    for row in dataloader.rows("ifa_fubc_crop_mapping.csv"):
        assert row["status"] == "confirmed" and row["reviewed_by"], row
        assert row["fubc_crop"] in names and row["match"] in ("exact", "subgroup", "group"), row
        assert set(row["crops"].split()) <= crops, row
    countries = {r["country"] for r in dataloader.rows("faostat_country_mapping.csv")} - {"GLO"}
    mapping = dataloader.rows("ifa_fubc_country_mapping.csv")
    assert {r["country"] for r in mapping} == countries
    for row in mapping:
        assert row["status"] == "confirmed" and row["reviewed_by"], row
        if row["fubc_country"]:
            assert regions[row["fubc_country"]] == row["region_ifa"], row
        else:
            assert row["region_ifa"] in regions.values(), row


def test_tables_equal_the_ifa_and_faostat_downloads():
    script = ROOT / "scripts" / "build_ifa_fertiliser_use.py"
    spec = importlib.util.spec_from_file_location("build_ifa_fertiliser_use", script)
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    fubc_zip, rfn_zip = dataloader.EXTERNAL_DATA_DIR / build.FUBC_ZIP, dataloader.EXTERNAL_DATA_DIR / build.RFN_ZIP
    if not (fubc_zip.is_file() and rfn_zip.is_file()):
        pytest.skip("IFA or FAOSTAT download not in data/external_data/")
    mapping = dataloader.rows("ifa_fubc_country_mapping.csv")
    rates, fallback_year = build.build_rates(fubc_zip, mapping)
    use = build.build_use(rfn_zip, mapping, rates, fallback_year)
    for built, table in ((rates, "ifa_fubc_rates.csv"), (use, "faostat_fertiliser_use_country.csv")):
        assert [{k: str(v) for k, v in r.items()} for r in built] == [dict(r) for r in dataloader.rows(table)]
    # the FUBC 9 rates of single-crop categories are the published mean rates over the total crop area
    published = {(r["Country"], r["Crop"]): r for r in build.read_zip_csv(fubc_zip, build.FUBC_ALL)
                 if r["FUBC_report_number"] == "9"}
    checked = 0
    for r in rates:
        p = published.get((r["fubc_country"], r["fubc_crop"]))
        if r["fubc_report"] == 9 and r["fubc_crop"] in ("Wheat", "Rice", "Tea") and p:
            for nutrient in ("N", "P2O5", "K2O"):
                if r[nutrient.lower() + "_kg_per_ha"] != "" and p["Aver_%s_rate_kg_ha" % nutrient] != "NA":
                    assert r[nutrient.lower() + "_kg_per_ha"] == pytest.approx(
                        float(p["Aver_%s_rate_kg_ha" % nutrient]), abs=0.06), (r["fubc_country"], r["fubc_crop"])
                    checked += 1
    assert checked > 100

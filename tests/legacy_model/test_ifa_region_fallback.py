"""Decision L37: a crop missing in the FUBC data of a country takes the rate of the FUBC 9 countries of its IFA
region: per country the best match level, the rows of that level combined by area; median over the countries at the
best level found in the region, at least two countries; brought to 2021-2023 with the factor of the country (IFASTAT
since decision L53), at most the highest rate of these countries brought to 2021-2023 with their own factor (L53).
The countries without FUBC data (GH, CS) follow the same rule."""
import statistics

import pytest

import dataloader
from defaultGeneration import DefaultValuesWrapper, DEFAULTS_VALUES_GENERATORS
from defaultTables import IFA_MINERAL_FERTILISER_PER_CROP_PER_COUNTRY as IFA

NUTRIENTS = ("n", "p2o5", "k2o")
FIELDS = {"n": "nitrogen_from_mineral_fert", "p2o5": "p2O5_from_mineral_fert", "k2o": "k2O_from_mineral_fert"}


def _factor(key, value, nutrient):
    row = next(r for r in dataloader.rows("ifastat_fertiliser_time_factor.csv")
               if r[key] == value and r["nutrient"] == nutrient.upper())
    return float(row["factor"]) if row["factor"] else 1.0


def _scale(country, nutrient):
    return _factor("country", country, nutrient)


def _region_median(region, fubc_crops, country, nutrient):
    per_country = {}
    for r in dataloader.rows("ifa_fubc_rates.csv"):
        if r["region_ifa"] == region and r["fubc_report"] == "9" and r["fubc_crop"] in fubc_crops \
                and r[nutrient + "_kg_per_ha"]:
            per_country.setdefault(r["fubc_country"], []).append(r)
    rates = {fubc_country: sum(float(r[nutrient + "_kg_per_ha"]) * float(r["area_ha"]) for r in rows)
             / sum(float(r["area_ha"]) for r in rows) for fubc_country, rows in per_country.items()}
    assert len(rates) >= 2
    highest = max(rate * _factor("fubc_country", fubc_country, nutrient) for fubc_country, rate in rates.items())
    return min(statistics.median(rates.values()) * _scale(country, nutrient), highest)


def _own_names(fubc_country):
    return {r["fubc_crop"] for r in dataloader.rows("ifa_fubc_rates.csv") if r["fubc_country"] == fubc_country}


SOYBEAN = {"Soybeans", "Soybean", "Soya beans"}
PULSES = {"Pulses", "Pulses (pea, bean)", "Pulses (peas, beans)"}


@pytest.mark.parametrize("crop, country, region, fubc_country, fubc_crops", [
    ("soybean", "PE", "Latin America", "Peru", SOYBEAN),  # FUBC 9 country without soybean
    ("soybean", "CI", "Africa", "Cote d'Ivoire", SOYBEAN),  # earlier report (FUBC 4) without soybean
    ("lentil", "UA", "Eastern Europe and Central Asia", "Ukraine", PULSES)])
def test_missing_crop_takes_the_region_median(crop, country, region, fubc_country, fubc_crops):
    assert not _own_names(fubc_country) & fubc_crops
    for nutrient in NUTRIENTS:
        assert IFA[crop][country][nutrient] == pytest.approx(_region_median(region, fubc_crops, country, nutrient))


def test_region_rates_of_the_earlier_report_countries_are_scaled():
    row = next(r for r in dataloader.rows("ifastat_fertiliser_time_factor.csv")
               if r["country"] == "CI" and r["nutrient"] == "N")
    assert row["base_years"] == "2017 2018 2019" and "region rates only" in row["note"]
    assert _scale("CI", "n") != pytest.approx(1.0)
    # own FUBC 4 rate of cotton CI unscaled: 25.8 kg N/ha
    assert IFA["cotton"]["CI"]["n"] == pytest.approx(25.8)


@pytest.mark.parametrize("crop, country", [
    ("tea", "CO"),  # Latin America: one FUBC 9 country with tea
    ("coriander", "TR"),  # West Asia: fresh herbs of IL only
    ("lemon", "TH"),  # East Asia: citrus of CN only
    ("cassava", "GH"), ("cassava", "CI")])  # Africa: cassava of NG only
def test_no_region_rate_from_a_single_country(crop, country):
    assert IFA.get(crop, {}).get(country) is None


def test_own_data_before_the_region():
    # lemon ES: own FUBC 9 group 'Fruits & Treenuts', not the region
    rows = [r for r in dataloader.rows("ifa_fubc_rates.csv")
            if r["fubc_country"] == "Spain" and r["fubc_crop"] == "Fruits & Treenuts"]
    assert len(rows) == 1
    assert IFA["lemon"]["ES"]["n"] == pytest.approx(float(rows[0]["n_kg_per_ha"]) * _scale("ES", "n"))


@pytest.mark.parametrize("crop, country", [("soybean", "PE"), ("peanut", "AR"), ("peach", "CN"), ("cotton", "AR")])
def test_default_at_the_default_yield_is_the_region_rate(crop, country):
    defaults = DefaultValuesWrapper({"crop": crop, "country": country}, DEFAULTS_VALUES_GENERATORS)
    for nutrient, field in FIELDS.items():
        assert defaults[field] == pytest.approx(IFA[crop][country][nutrient])

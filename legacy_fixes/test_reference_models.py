"""Tests for reference_models.py. Expected values computed by hand from the Quantis (2019)
equations, independently of the implementation."""
import tempfile
from pathlib import Path

import pytest

import reference_models as rm

REL = 1e-6


def test_nox_eea2016_factor_in_no2_and_subtracts_nh3_n():
    # 100 kg N applied, 10 kg NH3 -> (100 - 10*14/17) * 0.04 kg NO2/kg N
    assert rm.nox(100, 10) == pytest.approx(3.670588, rel=REL)


def test_n2o_includes_nsom_and_rice_factor_on_direct_only():
    args = dict(n_applied_total=100, n_crop_residues=20, n_som=5, nh3_kg=10, nox_kg=5, no3_kg=50)
    assert rm.n2o(**args).total_n2o == pytest.approx(2.250675, rel=REL)
    rice = rm.n2o(**args, flooded_rice=True)
    assert rice.total_n2o == pytest.approx(0.875675, rel=REL)
    # indirect terms identical with and without rice
    assert rice.indirect_volatilisation_n == rm.n2o(**args).indirect_volatilisation_n


def test_volatilised_n_not_in_direct_term():
    assert rm.n2o_direct_n(100) == pytest.approx(1.0)


def test_n_som_only_from_soc_loss():
    assert rm.n_som_from_soc_change(-1100, 11) == pytest.approx(100)
    assert rm.n_som_from_soc_change(+500, 11) == 0.0


def test_soil_organic_n_italy():
    assert rm.soil_organic_n(0.011) == pytest.approx(5525.0)


def test_nitrate_leaching_annual_and_half_cycle():
    common = dict(precipitation_mm_yr=800, irrigation_mm_yr=0, clay_fraction=0.30108,
                  rooting_depth_m=0.7, n_mineral=120, n_organic_soluble=20,
                  nh3_n=5, nox_n=2, n2o_n=1.5, n_uptake=150, soil_c_fraction=0.011)
    res = rm.nitrate_leaching(**common)
    assert res.n_supply_net == pytest.approx(131.5)
    assert res.no3_n == pytest.approx(31.831482, rel=REL)
    assert res.no3 == pytest.approx(140.967990, rel=REL)
    assert rm.nitrate_leaching(**common, duration_yr=0.5).no3_n == pytest.approx(14.844360, rel=REL)


def test_clay_given_as_percent_is_rejected():
    with pytest.raises(ValueError):
        rm.nitrate_leaching(precipitation_mm_yr=800, irrigation_mm_yr=0, clay_fraction=30.1,
                            rooting_depth_m=0.7, n_mineral=100, n_organic_soluble=0, nh3_n=0,
                            nox_n=0, n2o_n=0, n_uptake=100, soil_c_fraction=0.011)


def test_phosphorus_erosion_and_leaching():
    assert rm.phosphorus_erosion(10_000) == pytest.approx(3.534, rel=REL)
    res = rm.phosphate_leaching("arable", 40)
    assert res.groundwater_po4 == pytest.approx(0.236094, rel=1e-5)
    assert res.drainage_surface_water_po4 == 0.0


def test_phosphate_drainage_factor_6_on_drained_share():
    res = rm.phosphate_leaching("arable", 40, drained_fraction=0.25)
    assert res.groundwater_po4 == pytest.approx(0.236094 * 0.75, rel=1e-5)
    assert res.drainage_surface_water_po4 == pytest.approx(0.236094 * 6 * 0.25, rel=1e-5)


def test_phosphate_runoff_slope_threshold():
    base = rm.phosphate_runoff("arable", 0, 0, 0)
    assert base == pytest.approx(0.175 * 94.971 / 30.974, rel=1e-6)
    assert rm.phosphate_runoff("arable", 0, 0, 0, slope_pct=2.0) == 0.0
    assert rm.phosphate_runoff("arable", 0, 0, 0, slope_pct=3.0) == 0.0
    assert rm.phosphate_runoff("arable", 0, 0, 0, slope_pct=5.0) == pytest.approx(base)


def test_nh3_conversion_for_organic_inputs():
    assert rm.nh3_from_nh3_n(14) == pytest.approx(17)


def test_compound_fertiliser_zinc_is_not_lead():
    hm = rm.hm_input_compound(n_kg=1)
    assert hm["Zn"] == pytest.approx(121.43)
    assert hm["Pb"] == pytest.approx(5.37)


def test_manure_heavy_metals_in_mg():
    # 10 t fresh cattle slurry, 7.5 % DM, 123.3 mg Zn/kg DM
    assert rm.hm_input_manure({"cattle_slurry": 10_000})["Zn"] == pytest.approx(92_475)


def test_heavy_metal_balance_zinc():
    agro = rm.hm_input_compound(n_kg=100)
    export = rm.hm_biomass({"wheat_grains": 8000})
    res = rm.heavy_metals(agro_inputs_mg=agro, biomass_export_mg=export,
                          soil_eroded_kg=10_000)["Zn"]
    assert res.allocation == pytest.approx(0.1184186, rel=1e-6)
    assert res.leaching_groundwater_kg == pytest.approx(0.0039078, rel=1e-4)
    assert res.erosion_kg == pytest.approx(0.0218497, rel=1e-4)  # uses a = 1.86
    assert res.soil_kg == pytest.approx(-0.0336035, rel=1e-4)


def test_no_agro_input_means_zero_allocation():
    res = rm.heavy_metals(agro_inputs_mg={}, biomass_export_mg={}, soil_eroded_kg=1000)
    assert all(r.allocation == 0 and r.soil_kg == 0 for r in res.values())


def test_balance_equals_freiermuth_form():
    # SALCA 2023 form (A applied to each output) == (inputs + dep - raw outputs) * A
    agro = rm.hm_input_compound(n_kg=100)
    export = rm.hm_biomass({"wheat_grains": 8000})
    res = rm.heavy_metals(agro_inputs_mg=agro, biomass_export_mg=export, soil_eroded_kg=10_000)
    a = res["Zn"].allocation
    old = (agro["Zn"] + 90400 - export["Zn"] - 33000 - 49.6 * 10_000 * 1.86 * 0.2) * a * 1e-6
    assert res["Zn"].soil_kg == pytest.approx(old, rel=1e-9)


def test_heavy_metal_leaching_split_by_drainage():
    res = rm.heavy_metals(agro_inputs_mg=rm.hm_input_compound(n_kg=100), biomass_export_mg={},
                          soil_eroded_kg=0, drained_fraction=0.4)["Zn"]
    total = res.leaching_groundwater_kg + res.leaching_surface_water_kg
    assert res.leaching_surface_water_kg == pytest.approx(0.4 * total)


def test_plant_na_is_zero_and_unknown_uses_generic_mean():
    assert rm.hm_plant_content("rice_grains")["Hg"] == 0.0
    with pytest.warns(UserWarning):
        assert rm.hm_plant_content("quinoa")["Hg"] == pytest.approx(0.04)


def test_land_occupation_rice():
    assert rm.land_occupation_m2a(12) == pytest.approx(10_000)
    assert rm.land_occupation_m2a(5) == pytest.approx(10_000 * 5 / 12)


_MASTER_XML = """<?xml version="1.0" encoding="utf-8"?>
<validIntermediateExchanges xmlns="http://www.EcoInvent.org/EcoSpold02">
  <intermediateExchange id="uuid-maize-seed" unitId="u1">
    <name xml:lang="en">maize seed, for sowing</name><unitName xml:lang="en">kg</unitName>
  </intermediateExchange>
  <intermediateExchange id="uuid-maize-grain" unitId="u1">
    <name xml:lang="en">maize grain</name><unitName xml:lang="en">kg</unitName>
  </intermediateExchange>
</validIntermediateExchanges>"""


def _master(tmpdir):
    path = Path(tmpdir) / "IntermediateExchanges.xml"
    path.write_text(_MASTER_XML, encoding="utf-8")
    return rm.load_intermediate_exchanges(path)


def test_seed_exchange_resolution_from_master_data():
    with tempfile.TemporaryDirectory() as d:
        ex = _master(d)
        mapping_file = Path(d) / "map.csv"
        mapping_file.write_text(
            "crop_key,seed_exchange_name,unit,status,note,reviewed_by\n"
            "Maize grain,\"maize seed, for sowing\",kg,confirmed,,FR\n"
            "Sugar cane,,,no_exchange,,FR\n"
            "Sweet corn,\"maize seed, for sowing\",kg,to_decide,,\n", encoding="utf-8")
        mapping = rm.load_seed_mapping(mapping_file)
        assert rm.validate_seed_mapping(mapping, ex) == []
        assert rm.resolve_seed_exchange("maize-grain", mapping, ex, "kg").uuid == "uuid-maize-seed"
        assert rm.resolve_seed_exchange("sugar cane", mapping, ex) is None
        with pytest.raises(ValueError, match="review it first"):
            rm.resolve_seed_exchange("sweet corn", mapping, ex)
        with pytest.raises(ValueError, match="Unit mismatch"):
            rm.resolve_seed_exchange("maize grain", mapping, ex, "unit")
        with pytest.raises(KeyError, match="No seed mapping"):
            rm.resolve_seed_exchange("sugar beet", mapping, ex)
        assert rm.suggest_seed_exchanges("maize", ex) == ["maize seed, for sowing"]


def test_mapping_to_unknown_exchange_is_reported():
    with tempfile.TemporaryDirectory() as d:
        ex = _master(d)
        mapping = {"rice": rm.SeedMappingRow("rice seed, for sowing", "confirmed")}
        assert rm.validate_seed_mapping(mapping, ex) == ["rice seed, for sowing"]


def test_shipped_mapping_loads_and_blocks_unreviewed_rows():
    mapping = rm.load_seed_mapping()
    assert mapping["wheat"].status == "proposed"
    assert all(r.status in ("proposed", "to_decide", "no_exchange", "confirmed")
               for r in mapping.values())

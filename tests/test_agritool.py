import json
import unittest

from agritool import (
    Emission,
    EmissionFactor,
    ClimateZone,
    Crop,
    FertilizerType,
    Operation,
    SoilPHClass,
    ammonia_from_n_fertilizers,
    build_inventory,
    direct_soil_n2o,
    enteric_methane,
    nitrogen_oxides_from_n_fertilizers,
    particulate_matter_from_field_operations,
)


class CalculationTests(unittest.TestCase):
    def setUp(self):
        self.soil_factor = EmissionFactor(
            0.01, "kg N2O-N/kg N", "IPCC 2006 Volume 4 Chapter 11 Table 11.1"
        )
        self.enteric_factor = EmissionFactor(
            50, "kg CH4/head/year", "Illustrative factor, not a species default"
        )

    def test_direct_soil_n2o_mass_conversion(self):
        emission = direct_soil_n2o(100, self.soil_factor)
        self.assertAlmostEqual(emission.amount_kg, 44 / 28)
        self.assertEqual(emission.flow, "Dinitrogen monoxide")
        self.assertEqual(emission.factor_source, self.soil_factor.source)

    def test_enteric_methane_annual_mean_population(self):
        emission = enteric_methane(2.5, self.enteric_factor)
        self.assertEqual(emission.amount_kg, 125)
        self.assertEqual(emission.flow, "Methane")

    def test_zero_inputs_and_factors(self):
        self.assertEqual(direct_soil_n2o(0, self.soil_factor).amount_kg, 0)
        self.assertEqual(enteric_methane(0, self.enteric_factor).amount_kg, 0)
        zero = EmissionFactor(0, self.soil_factor.unit, "Zero-factor scenario")
        self.assertEqual(direct_soil_n2o(100, zero).amount_kg, 0)

    def test_invalid_numbers(self):
        for value in (-1, float("nan"), float("inf"), True, "100", 10**1000):
            with self.subTest(value=value):
                for calculate, factor in (
                    (direct_soil_n2o, self.soil_factor),
                    (enteric_methane, self.enteric_factor),
                ):
                    with self.assertRaises(ValueError):
                        calculate(value, factor)
                with self.assertRaises(ValueError):
                    EmissionFactor(value, self.soil_factor.unit, "Source")
                with self.assertRaises(ValueError):
                    Emission("Methane", value, "Method", "Source")

    def test_wrong_factor_units(self):
        with self.assertRaises(ValueError):
            direct_soil_n2o(100, self.enteric_factor)
        with self.assertRaises(ValueError):
            enteric_methane(10, self.soil_factor)

    def test_missing_factor_metadata(self):
        for unit, source in (("", "Source"), ("kg/kg", " "), (None, "Source")):
            with self.subTest(unit=unit, source=source):
                with self.assertRaises(ValueError):
                    EmissionFactor(0.01, unit, source)

    def test_overflow_is_rejected(self):
        factor = EmissionFactor(1e308, self.enteric_factor.unit, "Source")
        with self.assertRaises(ValueError):
            enteric_methane(1e308, factor)

    def test_inventory_normalization_and_provenance(self):
        emissions = [
            direct_soil_n2o(100, self.soil_factor),
            enteric_methane(2.5, self.enteric_factor),
        ]
        inventory = build_inventory(iter(emissions), "Wheat grain", 1000, "kg")
        self.assertEqual(inventory["reference_amount"], 1)
        self.assertEqual(inventory["reference_unit"], "kg")
        self.assertEqual(inventory["mapping_status"], "unmapped")
        self.assertAlmostEqual(inventory["exchanges"][0]["amount"], (44 / 28) / 1000)
        self.assertEqual(inventory["exchanges"][1]["amount"], 0.125)
        self.assertEqual(inventory["exchanges"][1]["unit"], "kg")
        self.assertEqual(inventory["exchanges"][1]["compartment"], "air")
        self.assertEqual(inventory["exchanges"][0]["factor_source"], self.soil_factor.source)
        self.assertEqual(json.loads(json.dumps(inventory)), inventory)

    def test_invalid_production(self):
        for amount in (0, -1, float("nan"), float("inf"), True, "1"):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    build_inventory([], "Wheat grain", amount, "kg")
        for product, unit in (("", "kg"), ("Wheat grain", " "), (None, "kg")):
            with self.subTest(product=product, unit=unit):
                with self.assertRaises(ValueError):
                    build_inventory([], product, 1000, unit)

    def test_normalization_overflow_is_rejected(self):
        emission = Emission("Methane", 1e308, "Method", "Source")
        with self.assertRaises(ValueError):
            build_inventory([emission], "Product", 1e-308, "kg")

    def test_empty_inventory(self):
        self.assertEqual(build_inventory([], "Product", 1, "kg")["exchanges"], [])

    def test_tier2_ammonia_by_fertilizer_and_ph(self):
        emission = ammonia_from_n_fertilizers(
            {FertilizerType.AN: 100},
            ClimateZone.DRY,
            SoilPHClass.HIGH,
        )
        self.assertAlmostEqual(emission.amount_kg, 5.2)
        self.assertEqual(emission.flow, "Ammonia")
        self.assertIn("Table 3-2", emission.factor_source)

    def test_ammonia_factor_override_and_no_climate_adjustment(self):
        override = EmissionFactor(100, "g NH3/kg N", "Local NH3 factor")
        inputs = {FertilizerType.AN: 10}
        wet = ammonia_from_n_fertilizers(
            inputs, ClimateZone.WET, SoilPHClass.NORMAL,
            {(FertilizerType.AN, SoilPHClass.NORMAL): override},
        )
        dry = ammonia_from_n_fertilizers(
            inputs, ClimateZone.DRY, SoilPHClass.NORMAL,
            {(FertilizerType.AN, SoilPHClass.NORMAL): override},
        )
        self.assertEqual(wet.amount_kg, 1)
        self.assertEqual(dry.amount_kg, wet.amount_kg)
        self.assertEqual(wet.factor_source, "Local NH3 factor")

    def test_tier1_nitrogen_oxides_uses_no2_factor(self):
        emission = nitrogen_oxides_from_n_fertilizers(100)
        self.assertAlmostEqual(emission.amount_kg, 4)
        self.assertEqual(emission.flow, "Nitrogen oxides")
        self.assertIn("Table 3-1", emission.factor_source)
        override = EmissionFactor(0.1, "kg NO2/kg N", "Local NOx factor")
        self.assertEqual(nitrogen_oxides_from_n_fertilizers(100, override).amount_kg, 10)

    def test_tier2_particulate_matter_calculation_and_fractions(self):
        fine, coarse = particulate_matter_from_field_operations(
            Crop.WHEAT,
            2,
            ClimateZone.WET,
            {
                Operation.SOIL_CULTIVATION: 1,
                Operation.HARVESTING: 2,
                Operation.CLEANING: 1,
                Operation.DRYING: 1,
            },
        )
        self.assertAlmostEqual(fine.amount_kg, 0.464)
        self.assertAlmostEqual(coarse.amount_kg, 12.336)
        self.assertEqual(fine.flow, "Particulate Matter, < 2.5 um")
        self.assertEqual(coarse.flow, "Particulate Matter, > 2.5 um and < 10um")
        self.assertIn("Table 3-8", fine.factor_source)
        self.assertIn("PM10 minus PM2.5", coarse.methodology)

    def test_pm_override_and_unsupported_table_cells(self):
        override = EmissionFactor(0.5, "kg PM10/ha", "Local PM10")
        with self.assertRaisesRegex(ValueError, "no Tier 2 factor"):
            particulate_matter_from_field_operations(
                Crop.OTHER_ARABLE,
                1,
                ClimateZone.WET,
                {Operation.HARVESTING: 1},
            )
        fine, coarse = particulate_matter_from_field_operations(
            Crop.OTHER_ARABLE,
            2,
            ClimateZone.WET,
            {Operation.SOIL_CULTIVATION: 1},
            {
                (Crop.OTHER_ARABLE, Operation.SOIL_CULTIVATION, ClimateZone.WET, "PM10"):
                    override
            },
        )
        self.assertEqual(fine.amount_kg, 0.03)
        self.assertEqual(coarse.amount_kg, 0.97)
        self.assertIn("Local PM10", coarse.factor_source)

    def test_new_methods_validate_inputs_and_units(self):
        with self.assertRaises(ValueError):
            ammonia_from_n_fertilizers(
                {"unknown fertilizer": 2}, ClimateZone.WET, SoilPHClass.NORMAL
            )
        with self.assertRaises(ValueError):
            ammonia_from_n_fertilizers(
                {FertilizerType.AN: 2}, "tropical", SoilPHClass.NORMAL
            )
        with self.assertRaises(ValueError):
            ammonia_from_n_fertilizers(
                {FertilizerType.AN: 2}, ClimateZone.WET, "neutral"
            )
        with self.assertRaises(ValueError):
            ammonia_from_n_fertilizers(
                {FertilizerType.AN: -1}, ClimateZone.WET, SoilPHClass.NORMAL
            )
        with self.assertRaises(ValueError):
            ammonia_from_n_fertilizers(
                {FertilizerType.AN: 1},
                ClimateZone.WET,
                SoilPHClass.NORMAL,
                {(FertilizerType.AN, SoilPHClass.NORMAL):
                    EmissionFactor(1, "kg NH3/kg N", "Wrong unit")},
            )
        with self.assertRaises(ValueError):
            nitrogen_oxides_from_n_fertilizers(
                1, EmissionFactor(0.04, "kg NO/kg N", "Wrong unit")
            )
        with self.assertRaises(ValueError):
            particulate_matter_from_field_operations(
                "unknown crop", 1, ClimateZone.WET, {}
            )
        with self.assertRaises(ValueError):
            particulate_matter_from_field_operations(
                Crop.WHEAT, 1, ClimateZone.WET, {"unknown operation": 1}
            )
        with self.assertRaises(ValueError):
            particulate_matter_from_field_operations(
                Crop.WHEAT, 1, ClimateZone.WET, {Operation.HARVESTING: 1.5}
            )


if __name__ == "__main__":
    unittest.main()

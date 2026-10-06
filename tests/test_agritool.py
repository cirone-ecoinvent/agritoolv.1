import json
import unittest

from agritool import (
    Emission,
    EmissionFactor,
    build_inventory,
    direct_soil_n2o,
    enteric_methane,
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


if __name__ == "__main__":
    unittest.main()

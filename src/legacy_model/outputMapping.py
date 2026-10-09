import config
import dataloader
import seedexchanges
from defaultGeneration import TREE_BASED_CROPS, SEEDLINGS_BASED_CROPS
from directMappingEnums import Plantprotection, Soilcultivation, Sowingplanting, \
    Fertilisation, Harvesting, OtherWorkProcesses
from models.atomicmass import MA_NH3, MA_N, MG_TO_MGSULFATE_FACTOR, \
    MG_TO_DOLOMITE_FACTOR, Ca_TO_LIMESTONE_FACTOR, Ca_TO_LIMEALGAE_FACTOR, Zn_TO_ZINCOXIDE_FACTOR
from models.manuremodel import LiquidManureType

def identity(x): return x

class OutputMapping(object):

    def __init__(self):
        self.output = {}

    def mapAsIsOutput(self, allInputs):
        self.output["country"] = allInputs["country"]
        self.output["crop"] = allInputs["crop"]
        self.output["yield_main_product_per_crop_cycle"] = allInputs["yield_main_product_per_crop_cycle"]
        self.output["yield_BP1_per_crop_cycle"] = allInputs["yield_BP1_per_crop_cycle"]
        self.output["yield_BP2_per_crop_cycle"] = allInputs["yield_BP2_per_crop_cycle"]
        self.output["yield_BP3_per_crop_cycle"] = allInputs["yield_BP3_per_crop_cycle"]
        self.output["hm_uptake_formula"] = str(allInputs["yield_main_product_dry_per_crop_cycle"]) + " * Heavy_metal_uptake"
        self.output["greenhouse_plastic_tunnel"] = \
            allInputs["greenhouse_plastic_tunnel"] / 25.0 / allInputs["orchard_lifetime"]
        self.output["greenhouse_glass_roof"] = allInputs["greenhouse_glass_roof"] / allInputs["orchard_lifetime"]
        self.output["greenhouse_plastic_roof"] = allInputs["greenhouse_plastic_roof"] / allInputs["orchard_lifetime"]

        for k,f in self._DIRECT_OUTPUT_MAPPING.items():
            if k in allInputs:
                self.output[k] = f(allInputs[k])

    def mapDictsToOutput(self, allInputs):
        self._mapEnumMap(allInputs["plastic_disposal_quantities"])
        self._mapEnumMap(allInputs["biowaste_quantities"])

    def mapSeeds(self, allInputs):
        self.output["need_trellis"] = 0.0
        for key, value in allInputs["seed_quantities"].items():
            if allInputs["crop"] in TREE_BASED_CROPS:
                self.output["seeds_" + key] = value / allInputs["orchard_lifetime"]
                self.output["rooting_up_trees"] = 1.0 / allInputs["orchard_lifetime"]
                if value >= 500:
                    self.output["need_trellis"] = 1.0
            else:
                self.output["seeds_" + key] = value
        self._mapSeedExchange(allInputs)

    def _mapSeedExchange(self, allInputs):
        """Fix F6: seed / seedling exchange resolved from the ecoinvent Master Data.

        Emits seed_exchange_name, seed_exchange_uuid, seed_exchange_unit and the amount under
        seed_amount_kg or seed_amount_unit. The run stops (exception) on an unmapped or
        unreviewed crop, a name missing from the Master Data or a unit mismatch. When no Master
        Data path is configured (config.master_data_path() is None) the legacy static Java
        lookup stays in force and seed_exchange_status says so.
        """
        if config.master_data_path() is None:
            self.output["seed_exchange_status"] = "master data not configured: legacy seed lookup"
            return
        crop = allInputs["crop"]
        amount = sum(allInputs["seed_quantities"].values())
        # Perennial plantings (trees, perennial seedlings, asparagus) are amortised over the
        # plantation lifetime: column planting_amortised_over_lifetime of data/crop_types.csv
        # (reviewer decision 2026-10-09).
        if dataloader.table("crop_types.csv", numeric=False)[crop]["planting_amortised_over_lifetime"] == "yes":
            amount /= allInputs["orchard_lifetime"]
        expected_unit = "kg" if seedexchanges.crop_key(crop) in self._SEEDS_IN_KG else "unit"
        exchange = seedexchanges.resolve_seed_exchange(crop, seedexchanges.load_seed_mapping(),
                                                       seedexchanges.master_data_exchanges(),
                                                       expected_unit)
        if exchange is None:
            self.output["seed_exchange_status"] = "no seed exchange for this crop (no_exchange)"
            return
        self.output["seed_exchange_status"] = "resolved from master data"
        self.output["seed_exchange_name"] = exchange.name
        self.output["seed_exchange_uuid"] = exchange.uuid
        self.output["seed_exchange_unit"] = exchange.unit
        self.output["seed_amount_" + exchange.unit] = amount

    @property
    def _SEEDS_IN_KG(self):
        """Mapping keys whose template amount is a mass (template field "seeds" [kg]); the
        others are counts (nb_seedlings, nb_planted_trees) and must map to 'unit' exchanges."""
        return {seedexchanges.crop_key(c) for c in dataloader.table("crop_types.csv", numeric=False)
                if c not in TREE_BASED_CROPS and c not in SEEDLINGS_BASED_CROPS}

    def mapIrrigationModel(self, irrOutput):
        for key, value in irrOutput.items():
            self.output[key.replace("m_Irr_", "")] = value

    def mapIrrigationQuantities(self, allInputs):
        self._mapEnumMap(allInputs["irrigation_types_quantities"])
        self._mapEnumMap(allInputs["irrigation_water_use_quantities"])
        wateruse = allInputs["water_use_total"]
        self.output["water_use_total"] = wateruse
        self.output["ecoinvent_water_to_air"] = wateruse * allInputs["ecoinvent_water_ratio_to_air"]
        self.output["ecoinvent_water_to_water_river"] = wateruse * allInputs["ecoinvent_water_ratio_to_water_river"]
        self.output["ecoinvent_water_to_water_groundwater"] = \
            wateruse * allInputs["ecoinvent_water_ratio_to_water_groundwater"]

    def mapCo2Model(self, co2Output):
        for key, value in co2Output.items():
            self.output[key.replace("m_co2_", "")] = value

    def mapNModel(self, no3Output, allInputs):
        for key, value in no3Output.items():
            if allInputs["cultivation_type"].startswith("greenhouse_hydroponic") and key != "m_N_ammonia_total":
                value = 0.0
            self.output[key.replace("m_N_", "")] = value

    def mapPModel(self, pOutput, allInputs):
        for key, value in pOutput.items():
            if allInputs["cultivation_type"].startswith("greenhouse_hydroponic"):
                value = 0.0
            self.output[key.replace("m_P_", "")] = value
        #TODO: Is this the best place for that?
        self.output["PO4_surfacewater"] = self.output["PO4_surfacewater_drained"] + self.output["PO4_surfacewater_ro"]

    def mapFertilizers(self, allInputs):
        self._mapEnumMap(allInputs["n_fertiliser_quantities"])
        self._mapEnumMap(allInputs["p_fertiliser_quantities"])
        self._mapEnumMap(allInputs["k_fertiliser_quantities"])
        self.output["magnesium_from_fertilizer"] = allInputs["magnesium_from_fertilizer"]
        self._mapEnumMap(allInputs["ca_fertiliser_quantities"])
        self._mapEnumMap(allInputs["zn_fertiliser_quantities"])
        self._convertEnumMap(allInputs["liquid_manure_quantities"], self._LIQUID_MANURE_FACTORS)
        self._mapEnumMap(allInputs["solid_manure_quantities"])
        #TODO: Is this the best place for that?
        self.output["fert_n_ammonia_liquid_as_nh3"] = self.output["fert_n_ammonia_liquid"] * MA_NH3/MA_N
        self.output["fert_ca_limestone_as_limestone"] = self.output["fert_ca_limestone"] * Ca_TO_LIMESTONE_FACTOR
        self.output["fert_ca_carbonation_limestone_as_limestone"] = self.output["fert_ca_carbonation_limestone"] * Ca_TO_LIMESTONE_FACTOR
        self.output["fert_ca_seaweed_limestone_as_seaweed_lime"] = self.output["fert_ca_seaweed_limestone"] * Ca_TO_LIMEALGAE_FACTOR
        self.output["fert_zn_zinc_sulfate_as_zincsulfate"] = \
            self.output["fert_zn_zinc_sulfate"] * Zn_TO_ZINCOXIDE_FACTOR / (0.478 - 0.00478 * Zn_TO_ZINCOXIDE_FACTOR)
        self.output["fert_zn_zinc_oxide_as_zincoxide"] = self.output["fert_zn_zinc_oxide"] * Zn_TO_ZINCOXIDE_FACTOR
        self.output["fert_zn_other_as_zincsulfate"] = \
            self.output["fert_zn_other"] * Zn_TO_ZINCOXIDE_FACTOR / (0.478 - 0.00478 * Zn_TO_ZINCOXIDE_FACTOR)
        self.output["magnesium_from_fertilizer_as_mgso4"] = self.output["magnesium_from_fertilizer"] * (1-allInputs["magnesium_as_dolomite"]) * MG_TO_MGSULFATE_FACTOR
        self.output["magnesium_from_fertilizer_as_dolomite"] = self.output["magnesium_from_fertilizer"] * allInputs["magnesium_as_dolomite"] * MG_TO_DOLOMITE_FACTOR

    def mapOtherOrganicFertilizers(self, allInputs):
        self._mapEnumMap(allInputs["compost_quantities"])
        self._mapEnumMap(allInputs["sludge_quantities"])

    def mapHMModel(self, hmOutput, allInputs):
        for key, hmMap in hmOutput.items():
            prefix = key.replace("m_hm_", "") + "_"
            for k, v in hmMap.items():
                if allInputs["cultivation_type"].startswith("greenhouse_hydroponic"):
                    v = 0.0
                self.output[prefix + k.name] = v

    def mapPackModel(self, packOutput):
        for key, value in packOutput.items():
            self.output[key.replace("m_Pack_", "")] = value

    def mapLucModel(self, lucOuput, allInputs):
        for key, value in lucOuput.items():
            self.output[key.replace("m_LUC_", "")] = value
        #FIXME: Probably not the right place
        lu_value = 10000.0 / allInputs["crop_cycle_per_year"]

        if allInputs["water_use_total"] > 0:
            lu_type = "irr"
        else:
            lu_type = "non-irr"

        if self.output["luc_crop_type"] == "annual":
            if self._is_flooded_crop(allInputs["crop"]):
                # Fix F7: flooded rice gets the ecoinvent flooded-crop land flows
                # ("Occupation / Transformation, annual crop, flooded crop"), like every
                # other annual crop it had no occupation at all in the legacy code.
                lu_type = "flooded"
                self.output["occupation_annual_flooded"] = lu_value
            elif allInputs["cultivation_type"] != "open_ground":
                lu_type = "greenhouse"
                self.output["occupation_annual_greenhouse"] = lu_value
            elif allInputs["organic_certified"] == "yes":
                self.output["occupation_annual_organic_" + lu_type] = lu_value
            else:
                self.output["occupation_annual_" + lu_type] = lu_value

            self.output["transformation_from_annual_" + lu_type] = 10000.0
            self.output["transformation_to_annual_" + lu_type] = 10000.0

        elif self.output["luc_crop_type"] == "perennial":
            self.output["occupation_peren_" + lu_type] = lu_value
            self.output["transformation_from_peren_" + lu_type] = 10000.0 / allInputs["orchard_lifetime"]
            self.output["transformation_to_peren_" + lu_type] = 10000.0 / allInputs["orchard_lifetime"]

    @staticmethod
    def _is_flooded_crop(crop):
        return dataloader.table("crop_types.csv", numeric=False)[crop]["flooded"] == "yes"

    def mapCODWasteWater(self, allInputs):  # m3 * mg/L(==g/m3) * 0.001 -> kg
        self.output["cod_in_waste_water"] = allInputs["eol_waste_water_to_nature"] * allInputs["cod_in_waste_water"] \
                                            * 0.001
        self.output["doc_in_waste_water"] = self.output["cod_in_waste_water"] / 2.7
        self.output["toc_in_waste_water"] = self.output["cod_in_waste_water"] / 2.7
        self.output["bod5_in_waste_water"] = self.output["cod_in_waste_water"] * 0.5

    def mapPesticides(self, allInputs):
        for k,v in allInputs["specified_pesticides"].items():
            self.output[k.replace("part_", "pesti_")] = v
            self.output[k.replace("part_", "pestikg_")] = v / 1000.0
        if ("pest_remains" in allInputs):
            self.output["pest_remains"] = allInputs["pest_remains"]
            self.output["pest_remains_kg"] = allInputs["pest_remains"] / 1000.0
        if ("remains_herbicides" in allInputs):
            self.output["remains_herbicides"] = allInputs["remains_herbicides"]
            self.output["remains_herbicides_kg"] = allInputs["remains_herbicides"] / 1000.0
        if ("remains_fungicides" in allInputs):
            self.output["remains_fungicides"] = allInputs["remains_fungicides"]
            self.output["remains_fungicides_kg"] = allInputs["remains_fungicides"] / 1000.0
        if ("remains_insecticides" in allInputs):
            self.output["remains_insecticides"] = allInputs["remains_insecticides"]
            self.output["remains_insecticides_kg"] = allInputs["remains_insecticides"] / 1000.0

    def mapMachineries(self, allInputs):
        if ("remains_machinery_diesel" in allInputs):
            self.output["remains_machinery_diesel"] = allInputs["remains_machinery_diesel"] * 45.00450045
        self._convertEnumMap(allInputs["plantprotection_quantities"], self._PLANTPROTECTION_FACTORS)
        self._convertEnumMap(allInputs["soilcultivation_quantities"], self._SOILCULTIVATION_FACTORS)
        self._convertEnumMap(allInputs["sowingplanting_quantities"], self._SOWINGPLANTING_FACTORS)
        self._convertEnumMap(allInputs["fertilisation_quantities"], self._FERTILISATION_FACTORS)
        self._convertEnumMap(allInputs["harvesting_quantities"], self._HARVESTING_FACTORS)
        self._convertEnumMap(allInputs["otherworkprocesses_quantities"], self._OTHERWORK_FACTORS)

    def _mapEnumMap(self, enumdict):
        for k,v in enumdict.items():
            self.output[k.value] = v

    def _convertEnumMap(self, enumdict, factors):
        for k,v in enumdict.items():
            self.output[k.value] = v * factors[k]

    _DIRECT_OUTPUT_MAPPING = {
        # FIXME: No system_boundary input anymore, use ecospold name metadata instead?
        # "system_boundary":identity,
        "record_entry_by":identity,
        "collection_method":identity,
        "data_treatment_extrapolations":identity,
        "data_treatment_uncertainty":identity,
        "comment":identity,

        "CO2_from_yield": identity,
        "energy_gross_calorific_value": identity,
        "pest_horticultural_oil": identity,

        "fert_other_kaolin": identity,
        "fert_other_manganese_sulfate": identity,
        "fert_other_gypsum": identity,
        "fert_other_sulfite": identity,
        "fert_other_portafer": identity,
        "fert_other_borax": identity,

        "total_machinery_gazoline": lambda x: x / 0.022075,

        "energy_electricity_low_voltage_at_grid": identity,
        "energy_electricity_photovoltaic_produced_locally": identity,
        "energy_electricity_wind_power_produced_locally": identity,
        "energy_diesel_excluding_diesel_used_in_tractor": lambda x: x * 45.00450045,
        # kg -> MJ
        "energy_lignite_briquette": lambda x: x / 0.111,
        "energy_hard_coal_briquette": lambda x: x / 0.0318,
        "energy_fuel_oil_light": lambda x: x / 0.02342,
        "energy_fuel_oil_heavy": lambda x: x / 0.025,
        "energy_natural_gas": lambda x: x / 0.0272, # Nm3 -> MJ
        "energy_wood_pellets_humidity_10_percent": lambda x: x / 0.0587,
        "energy_wood_chips_fresh_humidity_40_percent": lambda x: x / 0.0545,
        "energy_wood_logs": lambda x: x / 0.0643,
        "energy_heat_district_heating": identity,
        "energy_heat_solar_collector": identity,

        "utilities_wateruse_ground": identity,
        "utilities_wateruse_surface": identity,
        "utilities_wateruse_non_conventional_sources": lambda x: x * 1000.0, #m3 -> kg

        "materials_fleece": lambda x: x / 0.017,
        "materials_silage_foil": identity,
        "materials_covering_sheet": identity,
        "materials_bird_net": identity,

        "eol_waste_water_to_treatment_facility": identity,
        "eol_waste_water_to_nature": identity
    }

    # m3 -> kg of liquid manure (liquid_manure_density_kg_per_m3 in data/model_parameters.csv)
    _LIQUID_MANURE_FACTORS = {
        manure_type: dataloader.param("liquid_manure_density_kg_per_m3") for manure_type in LiquidManureType
    }

    _PLANTPROTECTION_FACTORS = {
        Plantprotection.spraying: 1.0 / 1.76,
        Plantprotection.flaming: 46.35,
        Plantprotection.other: 45.00450045
    }

    _SOILCULTIVATION_FACTORS = {
        Soilcultivation.decompactation: 45.00450045,
        Soilcultivation.tillage_chisel: 1.0 / 15.5,
        Soilcultivation.tillage_spring_tine_weeder: 1.0 / 1.6,
        Soilcultivation.tillage_rotary_harrow: 1.0 / 11.5,
        Soilcultivation.tillage_sprint_tine_harrow: 1.0 / 4.4,
        Soilcultivation.tillage_hoeing_earthing_up: 1.0 / 3.6,
        Soilcultivation.tillage_plough: 1.0 / 26.1,
        Soilcultivation.tillage_roll: 1.0 / 3.18,
        Soilcultivation.tillage_rotary_cultivator: 1.0 / 14.1,
        Soilcultivation.other: 45.00450045,
    }

    _SOWINGPLANTING_FACTORS = {
        Sowingplanting.sowing: 1.0 / 3.82,
        Sowingplanting.planting_seedlings: 1.0 / 16.8,
        Sowingplanting.planting_potatoes: 1.0 / 8.9,
        Sowingplanting.other: 45.00450045,
    }

    _FERTILISATION_FACTORS = {
        Fertilisation.fertilizing_broadcaster: 1.0 / 5.29,
        Fertilisation.liquid_manure_vacuum_tanker: 1.0 / 0.217,
        Fertilisation.solid_manure: 1.0 / 0.531,
        Fertilisation.other: 45.00450045,
    }

    _HARVESTING_FACTORS = {
        Harvesting.chopping_maize: 1.0 / 52.8,
        Harvesting.threshing_combine_harvester: 1.0 / 33.3,
        Harvesting.picking_up_forage_self_propelled_loader: 1.0 / 0.106,
        Harvesting.beets_complete_havester: 1.0 / 28.1,
        Harvesting.potatoes_complete_havester: 1.0 / 28.1,
        Harvesting.making_hay_rotary_tedder: 1.0 / 1.92,
        Harvesting.loading_bales: 1.0 / 0.0811,
        Harvesting.mowing_motor_mower: 1.0 / 3.0,
        Harvesting.mowing_rotary_mower: 1.0 / 4.31,
        Harvesting.removing_potatoes_haulms: 1.0 / 4.79,
        Harvesting.windrowing_rotary_swather: 1.0 / 2.94,
        Harvesting.other: 45.00450045,
    }

    _OTHERWORK_FACTORS = {
        OtherWorkProcesses.baling: 1.0 / 0.743,
        OtherWorkProcesses.chopping: 1.0 / 52.8,
        OtherWorkProcesses.mulching: 1.0 / 3.51,
        OtherWorkProcesses.transport_tractor_trailer: 1.0 / 0.0436,
        OtherWorkProcesses.other: 45.00450045,
    }

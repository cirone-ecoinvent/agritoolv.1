import dateutil.relativedelta as relativedelta
from datetime import date
from functools import lru_cache

from defaultMatrixEvapoTranspiration import EVAPO_TRANSPI_PER_CROP_PER_COUNTRY
from defaultMatrixNUptake import NITROGEN_UPTAKE_PER_CROP_PER_COUNTRY
from defaultMatrixSeed import NB_SEEDS_PER_PARTIAL_CROP_PER_COUNTRY, \
    NB_PLANTED_TREES_PER_PARTIAL_CROP_PER_COUNTRY, \
    NB_SEEDLINGS_PER_PARTIAL_CROP_PER_COUNTRY
from defaultMatrixTotalManure import TOTAL_MANURE_LIQUID_PER_CROP_PER_COUNTRY, \
    TOTAL_MANURE_SOLID_PER_CROP_PER_COUNTRY
from defaultMatrixTotalMineralFert import NITROGEN_FROM_MINERAL_FERT_PER_CROP_PER_COUNTRY
from defaultMatrixTotalPesticides import TOTAL_PESTICIDES_PER_CROP_PER_COUNTRY
from defaultMatrixYieldPerCropCycle import YIELD_PER_CROP_CYCLE_PER_CROP_PER_COUNTRY
from defaultTables import CLAY_CONTENT_PER_COUNTRY, SOIL_CARBON_CONTENT_PER_COUNTRY, \
    ROOTING_DEPTH_PER_CROP, FERT_N_RATIO_PER_COUNTRY, FERT_P_RATIO_PER_COUNTRY, FERT_K_RATIO_PER_COUNTRY, \
    MANURE_LIQUID_RATIO_PER_COUNTRY, MANURE_SOLID_RATIO_PER_COUNTRY, MANURE_LIQUID_N_FRACTION_PER_COUNTRY, \
    YEARLY_PRECIPITATION_AS_SNOW_PER_COUNTRY, \
    WATER_CONTENT_FM_RATIO_PER_CROP, IRR_TECH_RATIO_PER_COUNTRY, \
    LAND_USE_CATEGORY_PER_CROP, CROP_FACTOR_PER_CROP, SAND_CONTENT_PER_COUNTRY, \
    SOIL_ERODIBILITY_FACTOR_PER_SOIL_TEXTURE, SOIL_ERODIBILITY_FACTOR_PER_COUNTRY, \
    ENERGY_GROSS_CALORIFIC_VALUE_PER_CROP_PARTIAL, \
    SOIL_WITH_PH_UNDER_OR_7_PER_COUNTRY, CARBON_CONTENT_PER_CROP, IRR_WATERUSE_RATIO_PER_COUNTRY, \
    ANNUAL_PRECIPITATION_PER_COUNTRY, EI_IRR_RATIO_TO_RIVER, EI_IRR_RATIO_TO_GROUNDWATER, EI_IRR_RATIO_TO_AIR, \
    N_UPTAKE_PER_KG_MAIN_PRODUCT_PER_CROP, N_UPTAKE_OF_TREE_RESIDUES_PER_CROP, LEGUME_CROPS, \
    N_UPTAKE_PER_KG_MAIN_PRODUCT_OTHER_CROPS, PK_PER_KG_MAIN_PRODUCT_PER_CROP, \
    IFA_MINERAL_FERTILISER_PER_CROP_PER_COUNTRY, ORCHARD_LIFETIME_PER_CROP_PER_COUNTRY
from directMappingEnums import PlasticDisposal, Plantprotection, Soilcultivation, \
    Sowingplanting, Fertilisation, Harvesting, OtherWorkProcesses, Biowaste
from models.atomicmass import MA_CO2, MA_C
from models.erosionmodel import TillageMethod, AntiErosionPractice
from models.fertilisermodel import CaFertiliserType, ZnFertiliserType
import dataloader
from models.hmmodel import PesticideType, METAL_COLUMNS
from models.irrigationmodel import irrigation_efficiency
from models.manuremodel import ManureModel
from models.modelEnums import SoilTexture
from models.otherorganicfertilisermodel import CompostType, SludgeType
from models.pmodel import LandUseCategory

TREE_BASED_CROPS = ["almond", "apple", "apricot", "banana", "blueberry", "cashew", "cocoa", "coconut", "coffee_arabica",
                    "coffee_robusta", "cranberry", "grape", "lemon", "citruslime", "mandarin", "mango", "mulberry",
                    "olive", "orange_fresh", "orange_processing", "palmtree", "peach", "pear", "pomegranate",
                    "pineapple", "sugarcane", "tea"]

SEEDLINGS_BASED_CROPS = ["asparagus_green", "asparagus_white", "bellpepper", "cabbage_red", "cabbage_white", "chilli",
                         "eggplant", "ginger", "mint", "onion", "strawberry_fresh", "strawberry_processing",
                         "raspberry", "tomato_fresh", "tomato_processing"]


class DefaultValuesWrapper(object):
    def __init__(self, inputMapping, generatorMap):
        self.inputMapping = inputMapping
        self._generatorMap = generatorMap

    # TODO: Cache the generated values
    def __getattr__(self, name):
        try:
            res = self.inputMapping[name]
        except KeyError:
            res = self._generatorMap[name].generateDefault(name, self)
        return res;

    def __getitem__(self, name):
        return self.__getattr__(name)

    def __contains__(self, name):
        return name in self.inputMapping or name in self._generatorMap


class SimpleValueDefaultGenerator(object):
    def __init__(self, value):
        self._value = value

    def generateDefault(self, field, generators):
        return self._value


class ParameterDefaultGenerator(object):
    """Default = scalar parameter of data/model_parameters.csv."""
    def __init__(self, name):
        self._name = name

    def generateDefault(self, field, generators):
        return dataloader.param(self._name)


class TableLookupDefaultGenerator(object):
    def __init__(self, keyField, table):
        self._keyField = keyField
        self._table = table

    def generateDefault(self, field, generators):
        return self._table[generators[self._keyField]]


class CountryMapLookupDefaultGenerator(object):
    def __init__(self, table):
        self._table = table

    def generateDefault(self, field, generators):
        if generators["country"] in self._table:
            return self._table[generators["country"]]
        else:
            return self._table["GLO"]


class ZeroMapDefaultGenerator(object):
    def __init__(self, enumClass):
        self._enumClass = enumClass

    def generateDefault(self, attrName, mapping):
        return {k: 0.0 for k in self._enumClass}


class RatiosToValuesConvertor(object):
    def __init__(self, ratiosField, totalField):
        self._ratiosField = ratiosField
        self._totalField = totalField

    def generateDefault(self, field, generators):
        total = generators[self._totalField]
        return {k: v * total for k, v in generators[self._ratiosField].items()}


class ClimateDefaultGenerator(object):
    def generateDefault(self, field, generators):
        if generators["climate_zone_1"] == "cool_climate":
            return "snow_winter_continental"
        elif generators["climate_zone_1"] == "temperate_climate":
            return "warm_summer_dry_warm"
        else:
            return "equatorial_summer_dry"


class AnnualPrecipitationDefaultGenerator(TableLookupDefaultGenerator):
    def __init__(self):
        super().__init__("country", ANNUAL_PRECIPITATION_PER_COUNTRY)

    def generateDefault(self, field, generators):
        if generators["cultivation_type"] != "open_ground":
            return 0.0
        else:
            return TableLookupDefaultGenerator.generateDefault(self, field, generators)


class CropCyclePerYearDefaultGenerator(object):
    def generateDefault(self, field, generators):
        try:
            previousHarvestDate = generators["harvest_date_previous_crop"];
            previousHarvestDate = date(previousHarvestDate[0], previousHarvestDate[1], previousHarvestDate[2]);
            harvestDate = generators["harvesting_date_main_crop"];
            harvestDate = date(harvestDate[0], harvestDate[1], harvestDate[2]);
            dateDiff = relativedelta.relativedelta(harvestDate, previousHarvestDate);
            if dateDiff.years < 0 or dateDiff.months < 0 or dateDiff.days < 0 or (
                            dateDiff.years + dateDiff.months + dateDiff.days) == 0:
                return 1.0
            else:
                # If remaining days are more than 4 weeks, consider a month, if more than 2 weeks, consider half a month
                return 1.0 / (dateDiff.years + dateDiff.months / 12.0 + (dateDiff.days // 14.0) / 24.0);
        except KeyError:
            return 1.0


class WaterUseDefaultGenerator(object):
    def generateDefault(self, field, generators):
        default_evapo_transpiration = CropCountryMatrixLookupDefaultGenerator(
            EVAPO_TRANSPI_PER_CROP_PER_COUNTRY).generateDefault("", generators);
        irrigation_efficiency_ratio = irrigation_efficiency(generators["irrigation_types_proportions"])
        return default_evapo_transpiration / irrigation_efficiency_ratio * generators[
            "yield_main_product_per_crop_cycle"] / 1000.0;


class HeavyMetalExportWithHarvestGenerator(object):
    """Heavy metals exported with the harvested products [mg/(ha*crop cycle)], without the
    allocation factor (applied in hmmodel). SALCAheavymetal 2023 (Nemecek et al., Appendix 7)
    Eq. 4, concentrations from Table 1 (decision L10):

    * main product: dry yield x concentration of the product mapped to the crop in
      data/hm_crop_product_mapping_salca2023.csv ("main product, mean" when not in Table 1);
    * co-products (template fields yield_BP1..3_per_crop_cycle, kg fresh matter): fresh mass x
      DM x concentration of the row in data/hm_coproduct_mapping.csv ("co-product, mean").
    The pesticide term of Eq. 4 is computed in hmmodel.
    """
    def generateDefault(self, field, generators):
        product = dataloader.table("hm_crop_product_mapping_salca2023.csv", numeric=False)[generators["crop"]]["salca2023_main_product"]
        main = dataloader.hm_entry(product)
        dry_yield = generators["yield_main_product_dry_per_crop_cycle"]
        export = {element: dry_yield * main[column] for element, column in METAL_COLUMNS.items()}
        coproduct = dataloader.hm_entry(
            dataloader.table("hm_coproduct_mapping.csv", numeric=False)["any"]["salca2023_product"])
        for field_name in ("yield_BP1_per_crop_cycle", "yield_BP2_per_crop_cycle", "yield_BP3_per_crop_cycle"):
            fresh = generators[field_name]
            if fresh in ("", None):
                continue
            for element, column in METAL_COLUMNS.items():
                export[element] += float(fresh) * coproduct["dm"] * coproduct[column]
        return export



class SoilTextureDefaultGenerator(object):
    def generateDefault(self, field, generators):
        clay_content = generators["clay_content"]
        sand_content = generators["sand_content"]
        if (clay_content < 0.18 and sand_content > 0.65):
            return SoilTexture.coarse
        elif ((0.18 < clay_content and clay_content < 0.35 and sand_content > 0.15)
              or (clay_content < 0.18 and 0.15 < sand_content and sand_content < 0.65)):
            return SoilTexture.medium
        elif (clay_content < 0.35 and sand_content < 0.15):
            return SoilTexture.medium_fine
        elif (0.35 < clay_content and clay_content < 0.60):
            return SoilTexture.fine
        elif (clay_content > 0.60):
            return SoilTexture.very_fine
        else:
            return SoilTexture.unknown


class ErodibilityDefaultGenerator(object):
    """K factor of the country from the WFLDB 2017 soil types (decision L27). Countries without WFLDB soil
    types (MA, CS) keep the legacy lookup by soil texture, whose sand content is the share of sandy soils
    (legacy, undocumented, provisional)."""
    def generateDefault(self, field, generators):
        if generators["country"] in SOIL_ERODIBILITY_FACTOR_PER_COUNTRY:
            return SOIL_ERODIBILITY_FACTOR_PER_COUNTRY[generators["country"]]
        return SOIL_ERODIBILITY_FACTOR_PER_SOIL_TEXTURE[generators["soil_texture"]]


class PerCropCyclePrecipitationDefaultGenerator(object):
    def generateDefault(self, field, generators):  # mm/year -> m3/(ha*crop cycle)
        return generators["average_annual_precipitation"] * 10.0 / generators["crop_cycle_per_year"]


class PerYearYieldDefaultGenerator(object):
    def generateDefault(self, field, generators):
        return generators["yield_main_product_per_crop_cycle"] * generators["crop_cycle_per_year"]


# legacy, undocumented, provisional: default slope 3 % (0 % for rice)
class SlopePerCropGenerator(object):
    def generateDefault(self, field, generators):
        if (generators["crop"] == "rice"):
            return 0.00
        else:
            return 0.03


class KnownSlopePctGenerator(object):
    """Slope in % for the phosphorus run-off rule (Fix F8), None when unknown.

    The template has no slope field: the slope is unknown for every crop except flooded rice,
    whose field is level by definition (0 %), so its run-off is zero (user decision 2026-10-09).
    """
    def generateDefault(self, field, generators):
        if generators["crop"] == "rice":
            return 0.0
        return None


class DryContentGenerator(object):
    def generateDefault(self, field, generators):
        return 1 - generators["yield_main_product_water_content"]


class DryYieldGenerator(object):
    def generateDefault(self, field, generators):
        return generators["yield_main_product_dry_content"] * generators["yield_main_product_per_crop_cycle"]


class CO2FromYieldGenerator(object):
    def generateDefault(self, field, generators):
        return generators["yield_main_product_carbon_content"] * MA_CO2 / MA_C * generators[
            "yield_main_product_dry_per_crop_cycle"]


class EnergyGrossCalorificValueGenerator(object):
    def generateDefault(self, field, generators):
        if (generators["crop"] in ENERGY_GROSS_CALORIFIC_VALUE_PER_CROP_PARTIAL):
            return ENERGY_GROSS_CALORIFIC_VALUE_PER_CROP_PARTIAL[generators["crop"]] * generators[
                "yield_main_product_dry_per_crop_cycle"]
        else:
            return generators["CO2_from_yield"] * 11.5


class EolPlasticDisposalGenerator(object):
    def generateDefault(self, field, generators):
        return generators["materials_fleece"] \
               + generators["materials_silage_foil"] \
               + generators["materials_covering_sheet"] \
               + generators["materials_bird_net"];


class EolWaterWasteGenerator(object):
    def generateDefault(self, field, generators):
        return generators["utilities_wateruse_ground"] \
               + generators["utilities_wateruse_surface"] \
               + generators["utilities_wateruse_non_conventional_sources"];


class OrchardLifetimeDefaultGenerator(object):
    """Years. Perennial crops: ORCHARD_LIFETIME_PER_CROP_PER_COUNTRY (ecoinvent 3.12 datasets or FC values, decision
    L50), the country value else GLO. Other crops have no orchard lifetime: since decision L51 the model reads it only
    for the crops with planting amortised over the plantation lifetime."""
    def generateDefault(self, field, generators):
        crop = generators["crop"]
        if crop not in ORCHARD_LIFETIME_PER_CROP_PER_COUNTRY:
            raise KeyError("orchard_lifetime: no default for %s (not in orchard_lifetime_crop_mapping.csv)" % crop)
        table = ORCHARD_LIFETIME_PER_CROP_PER_COUNTRY[crop]
        return table.get(generators["country"], table["GLO"])


class SeedQuantitiesDefaultGenerator(object):
    def generateDefault(self, field, generators):
        crop = generators["crop"]
        if crop in TREE_BASED_CROPS:
            value_field = "nb_planted_trees"
        elif crop in SEEDLINGS_BASED_CROPS:
            value_field = "nb_seedlings"
        else:
            value_field = "seeds"
        try:
            return {crop: generators[value_field]}
        except KeyError:
            return {crop: 0.0}


class CropCountryMatrixLookupDefaultGenerator(object):
    def __init__(self, table):
        self._table = table

    def generateDefault(self, field, generators):
        currentCropTable = self._table[generators["crop"]]
        if (generators["country"] in currentCropTable):
            return currentCropTable[generators["country"]]
        else:
            return currentCropTable["GLO"]


class PlantingDefaultGenerator(CropCountryMatrixLookupDefaultGenerator):
    """Seedlings or trees per ha (decision L47). For the plantings amortised over the plantation lifetime
    (planting_amortised_over_lifetime of crop_types.csv: trees, asparagus) the table holds the ecoinvent 3.12 plantings
    per ha and year, multiplied here by the orchard lifetime in use, so that the yearly planting of outputMapping.py
    (number / orchard_lifetime) equals the ecoinvent input; for the other crops the table holds the number per ha and
    crop cycle."""
    def generateDefault(self, field, generators):
        value = super().generateDefault(field, generators)
        if dataloader.table("crop_types.csv", numeric=False)[generators["crop"]]["planting_amortised_over_lifetime"] \
                == "yes":
            value *= generators["orchard_lifetime"]
        return value


class NitrogenUptakeGenerator(object):
    """kg N/(ha and crop cycle). Crops of n_uptake_crop_parameters.csv: yield per crop cycle x N per kg of main
    product incl. residues (WFLDB 2017 / GRUDAF 2009, decision L28); tree crops: yield per crop cycle x N per kg of
    main product + N of a fixed amount of residues per ha (decision L32). Crops of
    n_uptake_other_crop_parameters.csv: yield per crop cycle x N per kg of main product (Ludemann et al. 2023 or
    GRUDAF 2009, residues of the field crops from IPCC 2019; decision L41). Other crops (mulberry): legacy matrix
    (legacy, undocumented, provisional). Legumes (column legume of data/crop_types.csv):
    only legume_uptake_share of this uptake, the rest is fixed from the air (WFLDB Guidelines v3.0 section 3.9.7.2,
    decision L30); the default mineral N and manure follow from it."""
    def generateDefault(self, field, generators):
        uptake = self._uptake(generators)
        if generators["crop"] in LEGUME_CROPS:
            return dataloader.param("legume_uptake_share") * uptake
        return uptake

    @staticmethod
    def _uptake(generators):
        if generators["crop"] in N_UPTAKE_PER_KG_MAIN_PRODUCT_PER_CROP:
            return (generators["yield_main_product_per_crop_cycle"] * N_UPTAKE_PER_KG_MAIN_PRODUCT_PER_CROP[generators["crop"]]
                    + N_UPTAKE_OF_TREE_RESIDUES_PER_CROP.get(generators["crop"], 0.0))
        if generators["crop"] in N_UPTAKE_PER_KG_MAIN_PRODUCT_OTHER_CROPS:
            return (generators["yield_main_product_per_crop_cycle"]
                    * N_UPTAKE_PER_KG_MAIN_PRODUCT_OTHER_CROPS[generators["crop"]])
        currentCropTable = NITROGEN_UPTAKE_PER_CROP_PER_COUNTRY[generators["crop"]]
        if (generators["country"] in currentCropTable):
            return currentCropTable[generators["country"]]
        else:
            return currentCropTable["GLO"]


@lru_cache(maxsize=None)
def _level2_reference(crop, country, nutrient):
    """Nutrient need and manure of the crop and country at the default yield with the default manure, the reference
    of the level 2 factors (decisions L33, L34): (N need, organic N) for "n", (P2O5 or K2O need, P2O5 or K2O of the
    manure) for "p2o5" and "k2o", kg/(ha and crop cycle); see MineralNitrogenDefaultGenerator.need and
    MineralPhosphorusPotassiumDefaultGenerator.balance. One reference per nutrient: the default manure of the crops
    without level 1 coefficients follows their level 2 mineral N (decision L40)."""
    reference = DefaultValuesWrapper({"crop": crop, "country": country}, DEFAULTS_VALUES_GENERATORS)
    if nutrient == "n":
        return MineralNitrogenDefaultGenerator.need(reference)
    return MineralPhosphorusPotassiumDefaultGenerator.balance(reference, nutrient)


def _level2(crop, country, nutrient, need, manure):
    """Level 2 mineral fertiliser (WFLDB Guidelines v3.0 section 3.6.1, decisions L33, L34), None without an IFA rate:
    the level 1 nutrient input is corrected with k = (IFA rate + manure) / need at the reference (default yield and
    default manure), mineral fertiliser = max(0, k x need - manure). At the reference it equals the IFA rate."""
    ifa = IFA_MINERAL_FERTILISER_PER_CROP_PER_COUNTRY.get(crop, {}).get(country, {}).get(nutrient)
    if ifa is None:
        return None
    need_reference, manure_reference = _level2_reference(crop, country, nutrient)
    if not need_reference:
        return None
    k = (ifa + manure_reference) / need_reference
    return max(0.0, k * need - manure)


class MineralNitrogenDefaultGenerator(object):
    """kg N/(ha and crop cycle). Crops with a computed N uptake, level 1: mineral share of the N input (WFLDB
    Guidelines v3.0 section 3.6.2, total N input = N uptake) x N uptake (decision L28); level 2 where IFA gives a
    rate for the crop and country (decision L33): k x N uptake - organic N, which is the IFA rate x N uptake / N
    uptake at the default yield. Other crops: the IFA rate x yield / default yield where IFA gives a rate (decision
    L34), else the legacy matrix."""
    def generateDefault(self, field, generators):
        need, organic_n = self.need(generators)
        level2 = _level2(generators["crop"], generators["country"], "n", need, organic_n)
        if level2 is not None:
            return level2
        if generators["crop"] in N_UPTAKE_PER_KG_MAIN_PRODUCT_PER_CROP:
            return self.level1(generators)
        return CropCountryMatrixLookupDefaultGenerator(
            NITROGEN_FROM_MINERAL_FERT_PER_CROP_PER_COUNTRY).generateDefault(field, generators)

    @staticmethod
    def need(generators):
        """(N need, organic N), kg/(ha and crop cycle): (N uptake, organic share of the N uptake) for the crops with a
        computed N uptake; for the other crops (yield, 0), the need being taken proportional to the yield with an
        unknown N content, which cancels in the level 2 factor (decision L34); their default manure is proportional
        to the yield as well, so it cancels too (decision L40)."""
        if generators["crop"] in N_UPTAKE_PER_KG_MAIN_PRODUCT_PER_CROP:
            uptake = generators["nitrogen_uptake_by_crop"]
            return uptake, (1.0 - dataloader.param("mineral_n_share_of_n_uptake")) * uptake
        return generators["yield_main_product_per_crop_cycle"], 0.0

    @staticmethod
    def level1(generators):
        return dataloader.param("mineral_n_share_of_n_uptake") * generators["nitrogen_uptake_by_crop"]


class ManureDefaultGenerator(object):
    """Total liquid manure [m3/ha] or solid manure [kg/ha] (decision L29). The available N (GRUDAF Nverf) of the
    manure is the organic share of the N input (WFLDB Guidelines v3.0 section 3.6.2), split with the country's share
    of manure N applied as liquid manure and divided by the available N per m3 (diluted) or per kg of the manure mix
    in use. Crops with a computed N uptake: (1 - mineral share) x N uptake. Crops without level 1 coefficients:
    (1 - mineral share) / mineral share x the level 2 mineral N (IFA rate x yield / default yield, decisions L34,
    L40). Other crops: legacy matrix."""
    def __init__(self, liquid, legacy_table):
        self._liquid = liquid
        self._legacy = CropCountryMatrixLookupDefaultGenerator(legacy_table)

    def generateDefault(self, field, generators):
        organic_n = self.organic_n(generators)
        if organic_n is None:
            return self._legacy.generateDefault(field, generators)
        liquid_fraction = MANURE_LIQUID_N_FRACTION_PER_COUNTRY[generators["country"]]
        if self._liquid:
            n_per_unit = generators["liquid_manure_part_before_dilution"] * ManureModel.mix_content(
                generators["liquid_manure_proportions"], "n_available")
            n_manure = organic_n * liquid_fraction
        else:
            n_per_unit = ManureModel.mix_content(generators["solid_manure_proportions"], "n_available") / 1000.0
            n_manure = organic_n * (1.0 - liquid_fraction)
        return n_manure / n_per_unit if n_per_unit else 0.0

    @staticmethod
    def organic_n(generators):
        """Available N of the default manure, kg N/(ha and crop cycle); None where the legacy matrix applies. Not the
        mineral N of the template: the default manure follows the default mineral N."""
        mineral_share = dataloader.param("mineral_n_share_of_n_uptake")
        if generators["crop"] in N_UPTAKE_PER_KG_MAIN_PRODUCT_PER_CROP:
            return (1.0 - mineral_share) * generators["nitrogen_uptake_by_crop"]
        mineral_n = _level2(generators["crop"], generators["country"], "n",
                            *MineralNitrogenDefaultGenerator.need(generators))
        if mineral_n is None:
            return None
        return (1.0 - mineral_share) / mineral_share * mineral_n


class MineralPhosphorusPotassiumDefaultGenerator(object):
    """kg P2O5 or kg K2O/(ha and crop cycle). Crops of PK_PER_KG_MAIN_PRODUCT_PER_CROP, level 1 (decision L31): the
    P2O5 (K2O) taken off the field with the main product, yield per crop cycle x content (WFLDB Guidelines v3.0
    section 3.6.1), minus the P2O5 (K2O) of the manure in use (template or default; GRUDAF 2009 Table 39), 0 when the
    manure brings more (Guidelines section 3.6.2); level 2 where IFA gives a rate for the crop and country (decision
    L33): max(0, k x P2O5 (K2O) taken off - manure in use). Other crops: max(0, k x yield - manure in use) where IFA
    gives a rate (decision L34), which is the IFA rate at the default yield and default manure, else 0."""
    def __init__(self, nutrient):
        self._nutrient = nutrient

    def generateDefault(self, field, generators):
        need, manure = self.balance(generators, self._nutrient)
        level2 = _level2(generators["crop"], generators["country"], self._nutrient, need, manure)
        if level2 is not None:
            return level2
        if generators["crop"] in PK_PER_KG_MAIN_PRODUCT_PER_CROP:
            return max(0.0, need - manure)
        return 0.0

    @staticmethod
    def balance(generators, nutrient):
        """(P2O5 or K2O need, P2O5 or K2O of the manure in use), kg/(ha and crop cycle). Need: taken off with the main
        product for the crops of PK_PER_KG_MAIN_PRODUCT_PER_CROP; for the other crops the yield, the need being taken
        proportional to it with an unknown content, which cancels in the level 2 factor (decision L34)."""
        need = generators["yield_main_product_per_crop_cycle"]
        if generators["crop"] in PK_PER_KG_MAIN_PRODUCT_PER_CROP:
            need *= PK_PER_KG_MAIN_PRODUCT_PER_CROP[generators["crop"]][nutrient]
        # mix_content of the quantities: kg per m3 of undiluted liquid manure x m3, kg per t x kg of solid manure
        manure = (generators["liquid_manure_part_before_dilution"]
                  * ManureModel.mix_content(generators["liquid_manure_quantities"], nutrient)
                  + ManureModel.mix_content(generators["solid_manure_quantities"], nutrient) / 1000.0)
        return need, manure

    @classmethod
    def level1(cls, generators, nutrient):
        """Level 1 of the crops of PK_PER_KG_MAIN_PRODUCT_PER_CROP: P2O5 (K2O) taken off minus manure in use."""
        taken_off, manure = cls.balance(generators, nutrient)
        return max(0.0, taken_off - manure)


class FlatRatioRepartitionGenerator(object):
    def __init__(self, enumClass):
        self._enumClass = enumClass

    def generateDefault(self, field, generators):
        return {k: 1.0 / len(self._enumClass) for k in self._enumClass}


class SafeDefaultGenerator(object):
    def __init__(self, field, defaultValue):
        self._field = field
        self._defaultValue = defaultValue

    def generateDefault(self, field, generators):
        try:
            return generators[self._field]
        except KeyError:
            return self._defaultValue


# Castor bean: Tree, estimated to be 0 (see ALCIG engine)
# Chickpea: Not much crop residues (https://www.saskatchewan.ca/business/agriculture-natural-resources-and-industry/agribusiness-farmers-and-ranchers/crops-and-irrigation/pulse-crop-bean-chickpea-faba-bean-lentils/chickpea/adaptation-and-varieties)
# Coriander: pdf Coriander_1 in documentation file (juste take the straw which is the main crop residue: https://books.google.ch/books?id=gR22BgAAQBAJ&pg=PA155&lpg=PA155&dq=crop+residue+coriander&source=bl&ots=NyhFs8bbXZ&sig=xUQcF__tZ61vf3pWtNgib9kKcbc&hl=en&sa=X&ved=0ahUKEwiFkIG7rrzYAhUDuRQKHbiiADIQ6AEILDAA#v=onepage&q=crop%20residue%20coriander&f=false)
# Ginger: root, estimated to be the same as cassava, turmenic, potato ? (see ALCIG engine)
# Millet: residue = straw/stover ; pdf Millet_2 in documentation file in google drive.
# Sesame seed: http://www.arccjournals.com/uploads/articles/D33414.pdf
# Turmenic: root, estimated to be the same as cassava, ginger, potato ? (see ALCIG engine)
# Pomegranate: Tree, estimated to be 0 (see ALCIG engine)
# legacy, undocumented, provisional: crop-residue N coefficients and fixed values
class NitrogenFromCropResiduesDefaultGenerator(object):
    def generateDefault(self, field, generators):
        crop = generators["crop"]
        if (crop == "carrot"):  # (YieldDM * slope + intercept*1000) * (Nag*(1-FracRemove)+Rbg-bio*Nbg)
            return (generators["yield_main_product_dry_per_crop_cycle"] * 1.07 + 1540.0) * (0.016 + 0.2 * 0.014)
        elif (crop == "linseed"):
            return (generators["yield_main_product_dry_per_crop_cycle"] * 1.13 + 850.0) * (0.008 + 0.19 * 0.008)
        elif (crop == "maizegrain"):
            return (generators["yield_main_product_dry_per_crop_cycle"] * 1.03 + 610.0) * (0.006 + 0.22 * 0.007)
        elif (crop == "oat"):
            return (generators["yield_main_product_dry_per_crop_cycle"] * 0.91 + 890.0) * (0.007 * 0.8 + 0.25 * 0.008)
        elif (crop == "peanut"):
            return (generators["yield_main_product_dry_per_crop_cycle"] * 1.07 + 1540.0) * (0.016 + 0.2 * 0.014)
        elif (crop == "potato"):
            return (generators["yield_main_product_dry_per_crop_cycle"] * 0.1 + 1060.0) * (0.019 + 0.2 * 0.014)
        elif (crop == "rapeseed"):
            return (generators["yield_main_product_dry_per_crop_cycle"] * 1.5) * (0.011 + 0.19 * 0.017)
        elif (crop == "rice"):
            return (generators["yield_main_product_dry_per_crop_cycle"] * 0.95 + 2460.0) * (0.007)
        elif (crop == "soybean"):
            return (generators["yield_main_product_dry_per_crop_cycle"] * 0.93 + 1350.0) * (0.008 + 0.19 * 0.008)
        elif (crop == "sweetcorn"):
            return (generators["yield_main_product_dry_per_crop_cycle"] * 1.03 + 610.0) * (0.006 + 0.22 * 0.007)
        elif (crop == "wheat"):
            return (generators["yield_main_product_dry_per_crop_cycle"] * 1.61 + 400.0) * (0.006 * 0.8 + 0.23 * 0.009)
        # Other formula
        elif (crop == "sugarbeet"):
            return generators["yield_main_product_dry_per_crop_cycle"] * (0.5 * 0.016 + 0.2 * 0.014)
        elif (crop == "sugarcane"):
            return generators["yield_main_product_dry_per_crop_cycle"] / 6.0 * 0.43 * 0.004
        elif (crop == "bellpepper"):
            return 52.33
        elif (crop == "cabbage_red"):
            return 180.0
        elif (crop == "cabbage_white"):
            return 180.0
        elif (crop == "chilli"):
            return 37.20
        elif (crop == "coconut"):
            return 44.0
        elif (crop == "coriander"):
            return 18.732
        elif (crop == "eggplant"):
            return 81.20
        elif (crop == "guar"):
            return 35.0
        elif (crop == "lentil"):
            return 76.87
        elif (crop == "palmtree"):
            return 159.0
        elif (crop == "pearl_millet"):
            return 18.0
        elif (crop == "sesame_seed"):
            return 12.6
        else:
            return 0.0


# legacy, undocumented, provisional: scalar default values of this table (e.g. 180 wet days, 700 m, slope length 50 m, 0.5 undiluted slurry, plastic EoL 50/50)
DEFAULTS_VALUES_GENERATORS = {
    "yield_BP1_per_crop_cycle": SimpleValueDefaultGenerator(""),
    "yield_BP2_per_crop_cycle": SimpleValueDefaultGenerator(""),
    "yield_BP3_per_crop_cycle": SimpleValueDefaultGenerator(""),
    # Cross-models defaults
    "average_annual_precipitation": AnnualPrecipitationDefaultGenerator(),
    "climate_zone_1": SimpleValueDefaultGenerator("temperate_climate"),
    "climate_zone_specific": ClimateDefaultGenerator(),
    "nb_wet_days_per_year": SimpleValueDefaultGenerator(180),
    "mean_elevation_m": SimpleValueDefaultGenerator(700),
    "clay_content": TableLookupDefaultGenerator("country", CLAY_CONTENT_PER_COUNTRY),
    "crop_cycle_per_year": CropCyclePerYearDefaultGenerator(),
    "precipitation_per_crop_cycle": PerCropCyclePrecipitationDefaultGenerator(),
    "water_use_total": WaterUseDefaultGenerator(),
    # FAOSTAT yield is per area harvested, i.e. per crop cycle (decision L24)
    "yield_main_product_per_crop_cycle": CropCountryMatrixLookupDefaultGenerator(
        YIELD_PER_CROP_CYCLE_PER_CROP_PER_COUNTRY),
    "yield_main_product_per_year": PerYearYieldDefaultGenerator(),
    "yield_main_product_dry_per_crop_cycle": DryYieldGenerator(),
    "pest_horticultural_oil": SimpleValueDefaultGenerator(0.0),
    # Fertiliser defaults
    "nitrogen_from_mineral_fert": MineralNitrogenDefaultGenerator(),
    "p2O5_from_mineral_fert": MineralPhosphorusPotassiumDefaultGenerator("p2o5"),
    "k2O_from_mineral_fert": MineralPhosphorusPotassiumDefaultGenerator("k2o"),
    "n_fertiliser_proportions": TableLookupDefaultGenerator("country", FERT_N_RATIO_PER_COUNTRY),
    "p_fertiliser_proportions": TableLookupDefaultGenerator("country", FERT_P_RATIO_PER_COUNTRY),
    "k_fertiliser_proportions": TableLookupDefaultGenerator("country", FERT_K_RATIO_PER_COUNTRY),
    "n_fertiliser_quantities": RatiosToValuesConvertor("n_fertiliser_proportions", "nitrogen_from_mineral_fert"),
    "p_fertiliser_quantities": RatiosToValuesConvertor("p_fertiliser_proportions", "p2O5_from_mineral_fert"),
    "k_fertiliser_quantities": RatiosToValuesConvertor("k_fertiliser_proportions", "k2O_from_mineral_fert"),
    "ca_from_mineral_fert": SimpleValueDefaultGenerator(0.0),
    "ca_fertiliser_proportions": FlatRatioRepartitionGenerator(CaFertiliserType),
    "ca_fertiliser_quantities": RatiosToValuesConvertor("ca_fertiliser_proportions", "ca_from_mineral_fert"),
    "zn_from_mineral_fert": SimpleValueDefaultGenerator(0.0),
    "zn_fertiliser_proportions": FlatRatioRepartitionGenerator(ZnFertiliserType),
    "zn_fertiliser_quantities": RatiosToValuesConvertor("zn_fertiliser_proportions", "zn_from_mineral_fert"),
    "soil_with_ph_under_or_7": TableLookupDefaultGenerator("country", SOIL_WITH_PH_UNDER_OR_7_PER_COUNTRY),
    # Manure defaults
    "liquid_manure_part_before_dilution": SimpleValueDefaultGenerator(0.5),
    "total_manureliquid": ManureDefaultGenerator(True, TOTAL_MANURE_LIQUID_PER_CROP_PER_COUNTRY),
    "total_manuresolid": ManureDefaultGenerator(False, TOTAL_MANURE_SOLID_PER_CROP_PER_COUNTRY),
    "liquid_manure_proportions": TableLookupDefaultGenerator("country", MANURE_LIQUID_RATIO_PER_COUNTRY),
    "solid_manure_proportions": TableLookupDefaultGenerator("country", MANURE_SOLID_RATIO_PER_COUNTRY),
    "liquid_manure_quantities": RatiosToValuesConvertor("liquid_manure_proportions", "total_manureliquid"),
    "solid_manure_quantities": RatiosToValuesConvertor("solid_manure_proportions", "total_manuresolid"),
    # Other organic fertilisers defaults
    "total_composttype": SimpleValueDefaultGenerator(0.0),
    "total_sewagesludge": SimpleValueDefaultGenerator(0.0),
    "compost_proportions": FlatRatioRepartitionGenerator(CompostType),
    "sludge_proportions": FlatRatioRepartitionGenerator(SludgeType),
    "compost_quantities": RatiosToValuesConvertor("compost_proportions", "total_composttype"),
    "sludge_quantities": RatiosToValuesConvertor("sludge_proportions", "total_sewagesludge"),
    # Seed defaults
    "unsafe_seeds": CropCountryMatrixLookupDefaultGenerator(NB_SEEDS_PER_PARTIAL_CROP_PER_COUNTRY),
    "seeds": SafeDefaultGenerator("unsafe_seeds", 0.0),
    "nb_seedlings": PlantingDefaultGenerator(NB_SEEDLINGS_PER_PARTIAL_CROP_PER_COUNTRY),
    "nb_planted_trees": PlantingDefaultGenerator(NB_PLANTED_TREES_PER_PARTIAL_CROP_PER_COUNTRY),
    "orchard_lifetime": OrchardLifetimeDefaultGenerator(),
    "seed_quantities": SeedQuantitiesDefaultGenerator(),
    # lu_defaults
    "organic_certified": SimpleValueDefaultGenerator("no"),
    "cultivation_type": SimpleValueDefaultGenerator("open_ground"),
    # Erosion defaults
    # DEPRECATED
    "yearly_precipitation_as_snow": TableLookupDefaultGenerator("country", YEARLY_PRECIPITATION_AS_SNOW_PER_COUNTRY),
    "slope": SlopePerCropGenerator(),
    "known_slope_pct": KnownSlopePctGenerator(),
    "slope_length": SimpleValueDefaultGenerator(50.0),
    "tillage_method": SimpleValueDefaultGenerator(TillageMethod.unknown),
    "anti_erosion_practice": SimpleValueDefaultGenerator(AntiErosionPractice.unknown),
    "sand_content": TableLookupDefaultGenerator("country", SAND_CONTENT_PER_COUNTRY),
    "soil_texture": SoilTextureDefaultGenerator(),
    "soil_erodibility_factor": ErodibilityDefaultGenerator(),
    "crop_factor": TableLookupDefaultGenerator("crop", CROP_FACTOR_PER_CROP),
    # CO2 model defaults
    "part_of_urea_in_UAN": SimpleValueDefaultGenerator(0.5),
    "magnesium_from_fertilizer": SimpleValueDefaultGenerator(0.0),
    "magnesium_as_dolomite": SimpleValueDefaultGenerator(1.0),
    # Irrigation defaults
    "irrigation_types_proportions": TableLookupDefaultGenerator("country", IRR_TECH_RATIO_PER_COUNTRY),
    "irrigation_types_quantities": RatiosToValuesConvertor("irrigation_types_proportions", "water_use_total"),
    "irrigation_water_use_proportions": TableLookupDefaultGenerator("country", IRR_WATERUSE_RATIO_PER_COUNTRY),
    "irrigation_water_use_quantities": RatiosToValuesConvertor("irrigation_water_use_proportions", "water_use_total"),
    "ecoinvent_water_ratio_to_air": CountryMapLookupDefaultGenerator(EI_IRR_RATIO_TO_AIR),
    "ecoinvent_water_ratio_to_water_river": CountryMapLookupDefaultGenerator(EI_IRR_RATIO_TO_RIVER),
    "ecoinvent_water_ratio_to_water_groundwater": CountryMapLookupDefaultGenerator(EI_IRR_RATIO_TO_GROUNDWATER),
    # N model defaults
    "bulk_density_of_soil": ParameterDefaultGenerator("bulk_density_kg_m3"),
    "c_per_n_ratio": ParameterDefaultGenerator("soil_cn_ratio"),
    "considered_soil_volume": ParameterDefaultGenerator("soil_volume_m3"),
    "drained_part": SimpleValueDefaultGenerator(0.0),
    "organic_carbon_content": TableLookupDefaultGenerator("country", SOIL_CARBON_CONTENT_PER_COUNTRY),
    "nitrogen_uptake_by_crop": NitrogenUptakeGenerator(),
    "norg_per_ntotal_ratio": ParameterDefaultGenerator("norg_ntot_ratio"),
    "rooting_depth": TableLookupDefaultGenerator("crop", ROOTING_DEPTH_PER_CROP),
    "nitrogen_from_crop_residues": NitrogenFromCropResiduesDefaultGenerator(),
    # Fix F2: SOC change of the land-use / land-management block (kg C/ha per cycle,
    # negative = loss) and whether the land came from forest or grassland (C:N 15 vs 11).
    # The legacy template and LUC module do not provide them: 0 and "no" unless supplied.
    "soc_change_kg_c": SimpleValueDefaultGenerator(0.0),
    "luc_from_forest_or_grassland": SimpleValueDefaultGenerator("no"),
    # P defaults (topsoil P content, enrichment factor and delivery ratio are read by the
    # P model from data/model_parameters.csv since Fix F8)
    "land_use_category": TableLookupDefaultGenerator("crop", LAND_USE_CATEGORY_PER_CROP),
    # HM defaults
    "hm_export_with_harvest": HeavyMetalExportWithHarvestGenerator(),
    "pest_total": CropCountryMatrixLookupDefaultGenerator(TOTAL_PESTICIDES_PER_CROP_PER_COUNTRY),
    "hm_pesticides_quantities": ZeroMapDefaultGenerator(PesticideType),
    # Packaging rules
    # Pesticides rules
    "specified_pesticides": SimpleValueDefaultGenerator({}),
    # Direct outputs
    "yield_main_product_water_content": TableLookupDefaultGenerator("crop", WATER_CONTENT_FM_RATIO_PER_CROP),
    "yield_main_product_dry_content": DryContentGenerator(),
    "yield_main_product_carbon_content": TableLookupDefaultGenerator("crop", CARBON_CONTENT_PER_CROP),
    "CO2_from_yield": CO2FromYieldGenerator(),
    "energy_gross_calorific_value": EnergyGrossCalorificValueGenerator(),
    "total_plantprotection": SimpleValueDefaultGenerator(0.0),
    "total_soilcultivation": SimpleValueDefaultGenerator(0.0),
    "total_sowingplanting": SimpleValueDefaultGenerator(0.0),
    "total_fertilisation": SimpleValueDefaultGenerator(0.0),
    "total_harvesting": SimpleValueDefaultGenerator(0.0),
    "total_otherworkprocesses": SimpleValueDefaultGenerator(0.0),
    "total_machinery_gazoline": SimpleValueDefaultGenerator(0.0),
    "plantprotection_proportions": SimpleValueDefaultGenerator({Plantprotection.other: 1.0}),
    "soilcultivation_proportions": SimpleValueDefaultGenerator({Soilcultivation.other: 1.0}),
    "sowingplanting_proportions": SimpleValueDefaultGenerator({Sowingplanting.other: 1.0}),
    "fertilisation_proportions": SimpleValueDefaultGenerator({Fertilisation.other: 1.0}),
    "harvesting_proportions": SimpleValueDefaultGenerator({Harvesting.other: 1.0}),
    "otherworkprocesses_proportions": SimpleValueDefaultGenerator({OtherWorkProcesses.other: 1.0}),
    "plantprotection_quantities": RatiosToValuesConvertor("plantprotection_proportions", "total_plantprotection"),
    "soilcultivation_quantities": RatiosToValuesConvertor("soilcultivation_proportions", "total_soilcultivation"),
    "sowingplanting_quantities": RatiosToValuesConvertor("sowingplanting_proportions", "total_sowingplanting"),
    "fertilisation_quantities": RatiosToValuesConvertor("fertilisation_proportions", "total_fertilisation"),
    "harvesting_quantities": RatiosToValuesConvertor("harvesting_proportions", "total_harvesting"),
    "otherworkprocesses_quantities": RatiosToValuesConvertor("otherworkprocesses_proportions",
                                                             "total_otherworkprocesses"),
    "utilities_wateruse_ground": SimpleValueDefaultGenerator(0.0),
    "utilities_wateruse_surface": SimpleValueDefaultGenerator(0.0),
    "utilities_wateruse_non_conventional_sources": SimpleValueDefaultGenerator(0.0),
    "materials_fleece": SimpleValueDefaultGenerator(0.0),
    "materials_silage_foil": SimpleValueDefaultGenerator(0.0),
    "materials_covering_sheet": SimpleValueDefaultGenerator(0.0),
    "materials_bird_net": SimpleValueDefaultGenerator(0.0),
    "greenhouse_plastic_tunnel": SimpleValueDefaultGenerator(0.0),
    "greenhouse_glass_roof": SimpleValueDefaultGenerator(0.0),
    "greenhouse_plastic_roof": SimpleValueDefaultGenerator(0.0),
    "total_eol_plastic_disposal_fleece_and_other": EolPlasticDisposalGenerator(),
    "plastic_disposal_proportions": SimpleValueDefaultGenerator(
        {PlasticDisposal.landfill: 0.5, PlasticDisposal.incineration: 0.5}),
    "plastic_disposal_quantities": RatiosToValuesConvertor("plastic_disposal_proportions",
                                                           "total_eol_plastic_disposal_fleece_and_other"),
    "total_biowaste": SimpleValueDefaultGenerator(0.0),
    "biowaste_proportions": SimpleValueDefaultGenerator({Biowaste.other: 1.0}),
    "biowaste_quantities": RatiosToValuesConvertor("biowaste_proportions", "total_biowaste"),
    "eol_waste_water_to_treatment_facility": SimpleValueDefaultGenerator(0.0),
    "eol_waste_water_to_nature": EolWaterWasteGenerator(),
    "cod_in_waste_water": SimpleValueDefaultGenerator(0.0)
}

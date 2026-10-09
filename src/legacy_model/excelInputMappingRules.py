from directMappingEnums import PlasticDisposal, Plantprotection, Soilcultivation, \
    Sowingplanting, Fertilisation, Harvesting, OtherWorkProcesses, Biowaste
from inputMappings import SimpleInputMappingRule, MapMappingRule, \
    InputAsEnumMappingRule, InputMappingRule
from models.erosionmodel import TillageMethod, AntiErosionPractice
from models.fertilisermodel import NFertiliserType, PFertiliserType, KFertiliserType, CaFertiliserType, ZnFertiliserType
from models.hmmodel import PesticideType
from models.irrigationmodel import IrrigationType, WaterUseType
from models.manuremodel import LiquidManureType, SolidManureType
from models.otherorganicfertilisermodel import CompostType, SludgeType

_N_ENUM_TO_FIELD = {
                NFertiliserType.ammonium_nitrate:"ratio_fertnmin_ammonium_nitrate",
                NFertiliserType.urea:"ratio_fertnmin_urea",
                NFertiliserType.ureaAN:"ratio_fertnmin_urea_an",
                NFertiliserType.mono_ammonium_phosphate:"ratio_fertnmin_mono_ammonium_phosphate",
                NFertiliserType.di_ammonium_phosphate:"ratio_fertnmin_di_ammonium_phosphate",
                NFertiliserType.an_phosphate:"ratio_fertnmin_an_phosphate",
                NFertiliserType.lime_ammonium_nitrate:"ratio_fertnmin_lime_ammonium_nitrate",
                NFertiliserType.ammonium_sulphate:"ratio_fertnmin_ammonium_sulphate",
                NFertiliserType.potassium_nitrate:"ratio_fertnmin_potassium_nitrate",
                NFertiliserType.ammonia_liquid:"ratio_fertnmin_ammonia_liquid"
                 }

_P_ENUM_TO_FIELD = {
                PFertiliserType.triple_superphosphate:"ratio_fertpmin_triple_superphosphate",
                PFertiliserType.superphosphate:"ratio_fertpmin_superphosphate",
                PFertiliserType.mono_ammonium_phosphate:"ratio_fertpmin_mono_ammonium_phosphate",
                PFertiliserType.di_ammonium_phosphate:"ratio_fertpmin_di_ammonium_phosphate",
                PFertiliserType.an_phosphate:"ratio_fertpmin_an_phosphate",
                PFertiliserType.hypophosphate_raw_phosphate:"ratio_fertpmin_hypophosphate_raw_phosphate",
                PFertiliserType.ground_basic_slag:"ratio_fertpmin_ground_basic_slag"
                 }

_K_ENUM_TO_FIELD = {
                KFertiliserType.potassium_salt:"ratio_fertkmin_potassium_salt_kcl",
                KFertiliserType.potassium_sulphate:"ratio_fertkmin_potassium_sulphate_k2so4",
                KFertiliserType.potassium_nitrate:"ratio_fertkmin_potassium_nitrate",
                KFertiliserType.patent_potassium:"ratio_fertkmin_patent_potassium"
                 }

_CA_ENUM_TO_FIELD = {
    CaFertiliserType.ca_limestone: "ratio_fertotherca_limestone",
    CaFertiliserType.ca_carbonation_limestone: "ratio_fertotherca_carbonation_limestone",
    CaFertiliserType.ca_seaweed_limestone: "ratio_fertotherca_seaweed_limestone"
}

_ZN_ENUM_TO_FIELD = {
    ZnFertiliserType.zn_zinc_sulfate: "ratio_fertotherzn_zinc_sulfate",
    ZnFertiliserType.zn_zinc_oxide: "ratio_fertotherzn_zinc_oxide",
    ZnFertiliserType.zn_other: "ratio_fertotherzn_other"
}

_LIQUID_MANURE_ENUM_TO_FIELD = {
                LiquidManureType.cattle:"ratio_manureliquid_cattle",
                LiquidManureType.pig:"ratio_manureliquid_pig",
                LiquidManureType.laying_hens:"ratio_manureliquid_laying_hen",
                LiquidManureType.other:"ratio_manureliquid_other"
                                }

_SOLID_MANURE_ENUM_TO_FIELD = {
                SolidManureType.cattle:"ratio_manuresolid_cattle",
                SolidManureType.pigs:"ratio_manuresolid_pig",
                SolidManureType.sheep_goats:"ratio_manuresolid_sheep_goat",
                SolidManureType.laying_hen_litter:"ratio_manuresolid_laying_hen",
                SolidManureType.horses:"ratio_manuresolid_horses",
                SolidManureType.other:"ratio_manuresolid_other"
                               }

_COMPOST_ENUM_TO_FIELD = {
                CompostType.compost:"ratio_composttype_compost",
                CompostType.meat_and_bone_meal:"ratio_composttype_meat_and_bone_meal",
                CompostType.castor_oil_shell_coarse:"ratio_composttype_castor_oil_shell_coarse",
                CompostType.vinasse:"ratio_composttype_vinasse",
                CompostType.dried_poultry_manure:"ratio_composttype_dried_poultry_manure",
                CompostType.stone_meal:"ratio_composttype_stone_meal",
                CompostType.feather_meal:"ratio_composttype_feather_meal",
                CompostType.horn_meal:"ratio_composttype_horn_meal",
                CompostType.horn_shavings_fine:"ratio_composttype_horn_shavings_fine"
                }
_SLUDGE_ENUM_TO_FIELD = {
                SludgeType.sewagesludge_liquid:"ratio_sewagesludge_liquid",
                SludgeType.sewagesludge_dehydrated:"ratio_sewagesludge_dehydrated",
                SludgeType.sewagesludge_dried:"ratio_sewagesludge_dried"
                 }

_IRR_ENUM_TO_FIELD = {
                    IrrigationType.surface_irrigation_no_energy:"ratio_irr_surface_no_energy",
                    IrrigationType.surface_irrigation_electricity:"ratio_irr_surface_electricity",
                    IrrigationType.surface_irrigation_diesel:"ratio_irr_surface_diesel",
                    IrrigationType.sprinkler_irrigation_electricity:"ratio_irr_sprinkler_electricity",
                    IrrigationType.sprinkler_irrigation_diesel:"ratio_irr_sprinkler_diesel",
                    IrrigationType.drip_irrigation_electricity:"ratio_irr_drip_electricity",
                    IrrigationType.drip_irrigation_diesel:"ratio_irr_drip_diesel"
                     }

_WATER_USED_ENUM_TO_FIELD = {
                             WaterUseType.groundwater:"ratio_wateruse_ground",
                             WaterUseType.surfacewater:"ratio_wateruse_surface",
                             WaterUseType.nonconventional:"ratio_wateruse_non_conventional_sources"
                             }

_PLANTPROTECTION_RATIOS_ENUM_TO_FIELD = {
                                         Plantprotection.spraying:"ratio_plantprotection_spraying",
                                         Plantprotection.flaming:"ratio_plantprotection_flaming",
                                         Plantprotection.other:"ratio_plantprotection_other"
                                         }

_SOILCULTIVATION_RATIOS_ENUM_TO_FIELD = {
                                         Soilcultivation.decompactation:"ratio_soilcultivation_decompactation",
                                         Soilcultivation.tillage_chisel:"ratio_soilcultivation_tillage_chisel",
                                         Soilcultivation.tillage_spring_tine_weeder:"ratio_soilcultivation_tillage_spring_tine_weeder",
                                         Soilcultivation.tillage_rotary_harrow:"ratio_soilcultivation_tillage_rotary_harrow",
                                         Soilcultivation.tillage_sprint_tine_harrow:"ratio_soilcultivation_tillage_sprint_tine_harrow",
                                         Soilcultivation.tillage_hoeing_earthing_up:"ratio_soilcultivation_tillage_hoeing_earthing_up",
                                         Soilcultivation.tillage_plough:"ratio_soilcultivation_tillage_plough",
                                         Soilcultivation.tillage_roll:"ratio_soilcultivation_tillage_roll",
                                         Soilcultivation.tillage_rotary_cultivator:"ratio_soilcultivation_tillage_rotary_cultivator",
                                         Soilcultivation.other:"ratio_soilcultivation_other",
                                         }

_SOWINGPLANTING_RATIOS_ENUM_TO_FIELD = {
                                        Sowingplanting.sowing:"ratio_sowingplanting_sowing",
                                        Sowingplanting.planting_seedlings:"ratio_sowingplanting_planting_seedlings",
                                        Sowingplanting.planting_potatoes:"ratio_sowingplanting_planting_potatoes",
                                        Sowingplanting.other:"ratio_sowingplanting_other",
                                         }

_FERTILISATION_RATIOS_ENUM_TO_FIELD = {
                                       Fertilisation.fertilizing_broadcaster:"ratio_fertilisation_fertilizing_broadcaster",
                                       Fertilisation.liquid_manure_vacuum_tanker:"ratio_fertilisation_liquid_manure_vacuum_tanker",
                                       Fertilisation.solid_manure:"ratio_fertilisation_solid_manure",
                                       Fertilisation.other:"ratio_fertilisation_other",
                                         }

_HARVESTING_RATIOS_ENUM_TO_FIELD = {
                                    Harvesting.chopping_maize:"ratio_harvesting_chopping_maize",
                                    Harvesting.threshing_combine_harvester:"ratio_harvesting_threshing_combine_harvester",
                                    Harvesting.picking_up_forage_self_propelled_loader:"ratio_harvesting_picking_up_forage_self_propelled_loader",
                                    Harvesting.beets_complete_havester:"ratio_harvesting_beets_complete_havester",
                                    Harvesting.potatoes_complete_havester:"ratio_harvesting_potatoes_complete_havester",
                                    Harvesting.making_hay_rotary_tedder:"ratio_harvesting_making_hay_rotary_tedder",
                                    Harvesting.loading_bales:"ratio_harvesting_loading_bales",
                                    Harvesting.mowing_motor_mower:"ratio_harvesting_mowing_motor_mower",
                                    Harvesting.mowing_rotary_mower:"ratio_harvesting_mowing_rotary_mower",
                                    Harvesting.removing_potatoes_haulms:"ratio_harvesting_removing_potatoes_haulms",
                                    Harvesting.windrowing_rotary_swather:"ratio_harvesting_windrowing_rotary_swather",
                                    Harvesting.other:"ratio_harvesting_other",
                                         }

_OTHERWORK_RATIOS_ENUM_TO_FIELD = {
                                   OtherWorkProcesses.baling:"ratio_otherworkprocesses_baling",
                                   OtherWorkProcesses.chopping:"ratio_otherworkprocesses_chopping",
                                   OtherWorkProcesses.mulching:"ratio_otherworkprocesses_mulching",
                                   OtherWorkProcesses.transport_tractor_trailer:"ratio_otherworkprocesses_transport_tractor_trailer",
                                   OtherWorkProcesses.other:"ratio_otherworkprocesses_other",
                                         }

_HM_PESTICIDES_ENUM_TO_FIELD = {
                                PesticideType.cu: "part_fungicides_copper_cu",
                                PesticideType.mancozeb:"part_fungicides_mancozeb",
                                PesticideType.metiram:"part_fungicides_metiram",
                                PesticideType.propineb:"part_fungicides_propineb",
                                PesticideType.zineb:"part_fungicides_zineb",
                                PesticideType.ziram:"part_fungicides_ziram"
                                }

_WASTE_PLASTIC_RATIOS_ENUM_TO_FIELD = {
                                   PlasticDisposal.landfill:"ratio_eol_landfill",
                                   PlasticDisposal.incineration:"ratio_eol_incineration"
                                    }

_BIOWASTE_ENUM_TO_FIELD = {
    Biowaste.incineration: "ratio_biowaste_incineration",
    Biowaste.anae_digestion: "ratio_biowaste_anae_digestion",
    Biowaste.composting: "ratio_biowaste_composting",
    Biowaste.other: "ratio_biowaste_other"
}


class RegroupPesticides(InputMappingRule):
    def mapField(self, attrName, mapping):
        res = {}
        for k,v in mapping.originalInputs.items():
            if (k.startswith("part_herbicides") or k.startswith("part_fungicides") or k.startswith("part_insecticides")):
                res[k] = v
        return res


EXCEL_INPUT_MAPPING_RULES = {
                    #Cross-models rules
                    "nitrogen_from_mineral_fert": SimpleInputMappingRule("total_fertnmin"),
                    "p2O5_from_mineral_fert": SimpleInputMappingRule("total_fertpmin"),
                    "water_use_total": SimpleInputMappingRule("total_wateruse"),
                    "drained_part": SimpleInputMappingRule("drainage"),
                    #Fertiliser rules
                    "n_fertiliser_proportions": MapMappingRule(_N_ENUM_TO_FIELD),
                    "p_fertiliser_proportions": MapMappingRule(_P_ENUM_TO_FIELD),
                    "k2O_from_mineral_fert": SimpleInputMappingRule("total_fertkmin"),
                    "k_fertiliser_proportions": MapMappingRule(_K_ENUM_TO_FIELD),
                    "ca_from_mineral_fert": SimpleInputMappingRule("total_fertotherca"),
    "ca_fertiliser_proportions": MapMappingRule(_CA_ENUM_TO_FIELD),
    "zn_from_mineral_fert": SimpleInputMappingRule("total_fertotherzn"),
    "zn_fertiliser_proportions": MapMappingRule(_ZN_ENUM_TO_FIELD),
                    #Manure rules
                    "liquid_manure_proportions": MapMappingRule(_LIQUID_MANURE_ENUM_TO_FIELD),
                    "solid_manure_proportions": MapMappingRule(_SOLID_MANURE_ENUM_TO_FIELD),
                    #Other organic fertiliser rules
                    "compost_proportions": MapMappingRule(_COMPOST_ENUM_TO_FIELD),
                    "sludge_proportions": MapMappingRule(_SLUDGE_ENUM_TO_FIELD),
                    #Erosion model rules
                    "tillage_method": InputAsEnumMappingRule("tillage_method", TillageMethod),
                    "anti_erosion_practice": InputAsEnumMappingRule("anti_erosion_practice", AntiErosionPractice),
                    #CO2 model rules
                    "magnesium_from_fertilizer": SimpleInputMappingRule("fert_other_total_mg"),
                    "magnesium_as_dolomite": SimpleInputMappingRule("fert_other_dolomite_in_mg"),
                    #Irrigation rules
                    "irrigation_types_proportions": MapMappingRule(_IRR_ENUM_TO_FIELD),
                    "irrigation_water_use_proportions": MapMappingRule(_WATER_USED_ENUM_TO_FIELD),
                    #N model rules
                    #P model rules
                    #HM model rules
                    "hm_pesticides_quantities": MapMappingRule(_HM_PESTICIDES_ENUM_TO_FIELD),
                    #Packaging rules
                    #Pesticides rules
                    "specified_pesticides": RegroupPesticides(),
                    #Machineries rules
                    "plantprotection_proportions": MapMappingRule(_PLANTPROTECTION_RATIOS_ENUM_TO_FIELD),
                    "soilcultivation_proportions": MapMappingRule(_SOILCULTIVATION_RATIOS_ENUM_TO_FIELD),
                    "sowingplanting_proportions": MapMappingRule(_SOWINGPLANTING_RATIOS_ENUM_TO_FIELD),
                    "fertilisation_proportions": MapMappingRule(_FERTILISATION_RATIOS_ENUM_TO_FIELD),
                    "harvesting_proportions": MapMappingRule(_HARVESTING_RATIOS_ENUM_TO_FIELD),
                    "otherworkprocesses_proportions": MapMappingRule(_OTHERWORK_RATIOS_ENUM_TO_FIELD),
                    #Waste rules
    "plastic_disposal_proportions": MapMappingRule(_WASTE_PLASTIC_RATIOS_ENUM_TO_FIELD),
    "biowaste_proportions": MapMappingRule(_BIOWASTE_ENUM_TO_FIELD)
                   }

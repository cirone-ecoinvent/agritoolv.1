from enum import Enum

import dataloader
from models.atomicmass import N_TO_NH3_FACTOR
from models.modelEnums import HeavyMetalType

class CompostType(Enum):
    compost="composttype_compost"
    meat_and_bone_meal="composttype_meat_and_bone_meal"
    castor_oil_shell_coarse="composttype_castor_oil_shell_coarse"
    vinasse="composttype_vinasse"
    dried_poultry_manure="composttype_dried_poultry_manure"
    stone_meal="composttype_stone_meal"
    feather_meal="composttype_feather_meal"
    horn_meal="composttype_horn_meal"
    horn_shavings_fine="composttype_horn_shavings_fine"
    
class SludgeType(Enum):
    sewagesludge_liquid="sewagesludge_liquid"
    sewagesludge_dehydrated="sewagesludge_dehydrated"
    sewagesludge_dried="sewagesludge_dried"

class OtherOrganicFertModel(object):
    """Inputs:
      compost_quantities: map CompostType -> kg fert/ha
      sludge_quantities: map SludgeType -> kg fert/ha

    Outputs:
      computeP2O5:
        P2O5_total_otherfert: kg P2O5/ha
      computeN:
        N_total_otherfert: kg N/ha
      computeNH3:
        nh3_total_otherfert: kg NH3/ha
      computeHeavyMetal:
        hm_total_otherfert : map HeavyMetalType -> mg i/ha (i:hm type)
    """
    
    _input_variables = ["compost_quantities",
                        "sludge_quantities"
                       ]
    
    _COMPOST_DM = { CompostType.compost: 0.5,
                    CompostType.meat_and_bone_meal: 0.95,
                    CompostType.castor_oil_shell_coarse: 0.9,
                    CompostType.vinasse: 0.5,
                    CompostType.dried_poultry_manure: 1.0,
                    CompostType.stone_meal: 0.1,
                    CompostType.feather_meal: 0.95,
                    CompostType.horn_meal: 0.95,
                    CompostType.horn_shavings_fine: 0.95
                    }
    _SLUDGE_DM = {
                    SludgeType.sewagesludge_liquid: 0.057,
                    SludgeType.sewagesludge_dehydrated: 0.26,
                    SludgeType.sewagesludge_dried: 0.93
                    }
    
    #src: Freiermuth 2006, table 13 * TS if not specified
    #kg/t FM
    _N_CONCENTRATION_ORG_COMPOST = {CompostType.compost: 7.0,#Walther Ryser 2001, Tab. 48
                                CompostType.meat_and_bone_meal: 90.0 * 0.95,#Tiermehl
                                CompostType.castor_oil_shell_coarse: 10.0,
                                CompostType.vinasse: 7.0 * 0.5,
                                CompostType.dried_poultry_manure: 45.0,
                                CompostType.stone_meal: 0.0 * 0.0,#Strange assumption based on a strange PDF :p
                                CompostType.feather_meal: 137.0 * 0.95,#Hornmehl
                                CompostType.horn_meal: 137.0 * 0.95,#Hornmehl
                                CompostType.horn_shavings_fine: 137.0 * 0.95#Hornmehl
                                }
    
    _N_CONCENTRATION_ORG_SLUDGE = {
                                SludgeType.sewagesludge_liquid: 2.5, #Walther Ryser 2001, Tab. 48
                                SludgeType.sewagesludge_dehydrated: 9.7, #Walther Ryser 2001, Tab. 48
                                SludgeType.sewagesludge_dried: 8.4 #Walther Ryser 2001, Tab. 48
                                }
    
    #src: Walther Ryser 2001, Tab. 48
    #kg/t FM
    _P205_CONCENTRATION_IN_LIQUID_SEWAGE_SLUDGE = 3.5

    # TAN content [kg N/t FM] and NH3 emission fraction of TAN per fertiliser type are read
    # from data/organic_fertiliser_nh3.csv (Agribalyse Tab. 67 x Tab. 154, as in the legacy code).
    _NH3_TABLE = "organic_fertiliser_nh3.csv"

    @classmethod
    def _tan_content(cls, fert_type):
        """TAN (soluble N) content [kg N/t FM] of a compost or sludge type."""
        return dataloader.table(cls._NH3_TABLE)[fert_type.value]["tan_kg_n_per_t_fm"]

    @classmethod
    def _nh3_emission_fraction(cls, fert_type):
        """Share of TAN emitted as NH3-N after spreading [kg NH3-N/kg TAN]."""
        return dataloader.table(cls._NH3_TABLE)[fert_type.value]["ef_nh3_n_fraction"]

    #src: Freiermuth 2006, table 13 if not specified
    # g/t TS (i.e. mg/kg)
    _HM_COMPOST_VALUES = { CompostType.compost: [0.36, 57.7, 183.5, 49.0, 16.3, 22.3, 0.12],
                        CompostType.meat_and_bone_meal: [0.6, 208.0, 125.0, 3.8, 34.0, 5.9, 0.6],#Tiermehl
                        CompostType.castor_oil_shell_coarse: [0.2, 22.5, 110.0, 8.5, 8.5, 10.5, 0.05],
                        CompostType.vinasse: [0.0, 30.54, 42.11, 22.94, 5.74, 0.0, 0.0], #No data for cd, cr, hg
                        CompostType.dried_poultry_manure: [0.25, 39.6, 468.4, 2.24, 7.9, 5.5, 0.2],#src WLFDB, #same as manure "Litter from deep pits from laying hens" (but different DM)
                        CompostType.stone_meal: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], #Strange assumption based on a strange PDF :P
                        CompostType.feather_meal: [0.2, 7.3, 135.3, 8.3, 2.8, 65.0, 0.1],#Hornmehl
                        CompostType.horn_meal: [0.2, 7.3, 135.3, 8.3, 2.8, 65.0, 0.1],#Hornmehl
                        CompostType.horn_shavings_fine: [0.2, 7.3, 135.3, 8.3, 2.8, 65.0, 0.1]
                        }#Hornmehl
    _HM_SLUDGE_VALUES = {
                        SludgeType.sewagesludge_liquid: [1.7, 341.0, 929.0, 94.0, 32.0, 74.0, 1.7], #Klärschlamm
                        SludgeType.sewagesludge_dehydrated: [1.7, 341.0, 929.0, 94.0, 32.0, 74.0, 1.7], #Klärschlamm
                        SludgeType.sewagesludge_dried: [1.7, 341.0, 929.0, 94.0, 32.0, 74.0, 1.7], #Klärschlamm
                    }
    
    def __init__(self, inputs):
        #TODO: Should we log usage of default value?
        for key in OtherOrganicFertModel._input_variables:
            setattr(self, key, inputs[key])
            
    def computeP2O5(self):
        return self.sludge_quantities[SludgeType.sewagesludge_liquid] * self._P205_CONCENTRATION_IN_LIQUID_SEWAGE_SLUDGE / 1000.0

    def computeN(self):
        return (sum(v * self._N_CONCENTRATION_ORG_COMPOST[k] for k,v in self.compost_quantities.items()) \
              + sum(v * self._N_CONCENTRATION_ORG_SLUDGE[k] for k,v in self.sludge_quantities.items())) / 1000.0
    
    def computeNH3(self):
        """NH3 [kg NH3/ha] after spreading of compost and sewage sludge.

        NH3-N = sum(quantity [kg FM] / 1000 * TAN [kg N/t FM] * EF); converted to kg NH3 with
        17/14 (Fix F5: the legacy code returned kg NH3-N and summed it with kg NH3).
        """
        nh3_as_n = sum(v * self._tan_content(k) * self._nh3_emission_fraction(k)
                       for quantities in (self.compost_quantities, self.sludge_quantities)
                       for k, v in quantities.items()) / 1000.0
        return nh3_as_n * N_TO_NH3_FACTOR

    def computeSolubleN(self):
        """Soluble (ammoniacal) N applied with compost and sludge [kg N/ha] (Fix F3)."""
        return sum(v * self._tan_content(k)
                   for quantities in (self.compost_quantities, self.sludge_quantities)
                   for k, v in quantities.items()) / 1000.0

    def computeHeavyMetal(self):
        total_hm_values = dict.fromkeys(HeavyMetalType,0.0)
        self._add_hm_values_for_fert_type(total_hm_values, self.compost_quantities, self._COMPOST_DM, self._HM_COMPOST_VALUES)
        self._add_hm_values_for_fert_type(total_hm_values, self.sludge_quantities, self._SLUDGE_DM, self._HM_SLUDGE_VALUES)
        return total_hm_values
    
    def _add_hm_values_for_fert_type(self,total_hm_values, fert_quantities, fert_dm,fert_hm_map):
        for fertKey,fertQuantity in fert_quantities.items():
            for hm_element_index,hm_element_value in enumerate(fert_hm_map[fertKey]):
                total_hm_values[HeavyMetalType(hm_element_index)] += hm_element_value * fert_dm[fertKey] * fertQuantity
    

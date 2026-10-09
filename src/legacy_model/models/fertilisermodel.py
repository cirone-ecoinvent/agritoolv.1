from enum import Enum

import dataloader
from models.atomicmass import N_TO_NH3_FACTOR
from models.modelEnums import HeavyMetalType


class NFertiliserType(Enum):
    ammonium_nitrate="fert_n_ammonium_nitrate"
    urea="fert_n_urea"
    ureaAN="fert_n_ureaAN"
    mono_ammonium_phosphate="fert_n_mono_ammonium_phosphate"
    di_ammonium_phosphate="fert_n_di_ammonium_phosphate"
    an_phosphate="fert_n_an_phosphate"
    lime_ammonium_nitrate="fert_n_lime_ammonium_nitrate"
    ammonium_sulphate="fert_n_ammonium_sulphate"
    potassium_nitrate="fert_n_potassium_nitrate"
    ammonia_liquid="fert_n_ammonia_liquid"

class PFertiliserType(Enum):
    triple_superphosphate="fert_p_triple_superphosphate"
    superphosphate="fert_p_superphosphate"
    mono_ammonium_phosphate="fert_p_mono_ammonium_phosphate"
    di_ammonium_phosphate="fert_p_di_ammonium_phosphate"
    an_phosphate="fert_p_an_phosphate"
    hypophosphate_raw_phosphate="fert_p_hypophosphate_raw_phosphate"
    ground_basic_slag="fert_p_ground_basic_slag"


class KFertiliserType(Enum):
    potassium_salt="fert_k_potassium_salt"
    potassium_sulphate="fert_k_potassium_sulphate"
    potassium_nitrate="fert_k_potassium_nitrate"
    patent_potassium="fert_k_patent_potassium"


class CaFertiliserType(Enum):
    ca_limestone="fert_ca_limestone"
    ca_carbonation_limestone="fert_ca_carbonation_limestone"
    ca_seaweed_limestone="fert_ca_seaweed_limestone"


class ZnFertiliserType(Enum):
    zn_zinc_sulfate = "fert_zn_zinc_sulfate"
    zn_zinc_oxide = "fert_zn_zinc_oxide"
    zn_other = "fert_zn_other"

class FertModel(object):
    """Inputs:
      n_fertiliser_quantities: map NFertiliserType -> kg N/ha
      p_fertiliser_quantities: map PFertiliserType -> kg P2O5/ha
      k_fertiliser_quantities: map KFertiliserType -> kg K2O/ha
      ca_fertiliser_quantities: map CaFertiliserType -> kg Ca/ha
      zn_fertiliser_quantities: map ZnFertiliserType -> kg Zn/ha
      soil_with_ph_under_or_7: ratio
      climate_zone_1: text
      cultivation_type: text

    Outputs:
      computeNH3:
        nh3_total_mineral_fert: kg NH3/ha
      computeHeavyMetal:
        hm_total_mineral_fert : map HeavyMetalType -> mg i/ha (i:hm type)
    """

    _input_variables = ["n_fertiliser_quantities",
                        "p_fertiliser_quantities",
                        "k_fertiliser_quantities",
                        "ca_fertiliser_quantities",
                        "zn_fertiliser_quantities",
                        "soil_with_ph_under_or_7",
                        "climate_zone_1",
                        "cultivation_type"
                        ]

    _EF_NH3N_MIN_N_FERT_PH_UNDER_OR_SEVEN = {"cool_climate": {
        NFertiliserType.ammonium_nitrate: 0.01,
        NFertiliserType.urea: 0.13,
        NFertiliserType.ureaAN: 0.08,
        NFertiliserType.mono_ammonium_phosphate: 0.04,
        NFertiliserType.di_ammonium_phosphate: 0.04,
        NFertiliserType.an_phosphate: 0.04,  # Other complex NK, NPK fertilizers
        NFertiliserType.lime_ammonium_nitrate: 0.01,  # Calcium ammonium nitrate (CAN)
        NFertiliserType.ammonium_sulphate: 0.07,
        NFertiliserType.potassium_nitrate: 0.04,  # Other complex NK, NPK fertilizers
        NFertiliserType.ammonia_liquid: 0.02  # Anhydrous ammonia
    }, "temperate_climate": {
        NFertiliserType.ammonium_nitrate: 0.01,
        NFertiliserType.urea: 0.13,
        NFertiliserType.ureaAN: 0.08,
        NFertiliserType.mono_ammonium_phosphate: 0.04,
        NFertiliserType.di_ammonium_phosphate: 0.04,
        NFertiliserType.an_phosphate: 0.06,  # Other complex NK, NPK fertilizers
        NFertiliserType.lime_ammonium_nitrate: 0.01,  # Calcium ammonium nitrate (CAN)
        NFertiliserType.ammonium_sulphate: 0.08,
        NFertiliserType.potassium_nitrate: 0.06,  # Other complex NK, NPK fertilizers
        NFertiliserType.ammonia_liquid: 0.02  # Anhydrous ammonia
    }, "warm_climate": {
        NFertiliserType.ammonium_nitrate: 0.02,
        NFertiliserType.urea: 0.16,
        NFertiliserType.ureaAN: 0.10,
        NFertiliserType.mono_ammonium_phosphate: 0.05,
        NFertiliserType.di_ammonium_phosphate: 0.05,
        NFertiliserType.an_phosphate: 0.05,  # Other complex NK, NPK fertilizers
        NFertiliserType.lime_ammonium_nitrate: 0.01,  # Calcium ammonium nitrate (CAN)
        NFertiliserType.ammonium_sulphate: 0.09,
        NFertiliserType.potassium_nitrate: 0.05,  # Other complex NK, NPK fertilizers
        NFertiliserType.ammonia_liquid: 0.02  # Anhydrous ammonia
    }}

    _EF_NH3N_MIN_N_FERT_PH_OVER_SEVEN = {"cool_climate": {
        NFertiliserType.ammonium_nitrate: 0.03,
        NFertiliserType.urea: 0.14,
        NFertiliserType.ureaAN: 0.08,
        NFertiliserType.mono_ammonium_phosphate: 0.07,
        NFertiliserType.di_ammonium_phosphate: 0.07,
        NFertiliserType.an_phosphate: 0.07,  # Other complex NK, NPK fertilizers
        NFertiliserType.lime_ammonium_nitrate: 0.01,  # Calcium ammonium nitrate (CAN)
        NFertiliserType.ammonium_sulphate: 0.14,
        NFertiliserType.potassium_nitrate: 0.07,  # Other complex NK, NPK fertilizers
        NFertiliserType.ammonia_liquid: 0.03  # Anhydrous ammonia
    }, "temperate_climate": {
        NFertiliserType.ammonium_nitrate: 0.03,
        NFertiliserType.urea: 0.14,
        NFertiliserType.ureaAN: 0.08,
        NFertiliserType.mono_ammonium_phosphate: 0.08,
        NFertiliserType.di_ammonium_phosphate: 0.08,
        NFertiliserType.an_phosphate: 0.08,  # Other complex NK, NPK fertilizers
        NFertiliserType.lime_ammonium_nitrate: 0.01,  # Calcium ammonium nitrate (CAN)
        NFertiliserType.ammonium_sulphate: 0.14,
        NFertiliserType.potassium_nitrate: 0.08,  # Other complex NK, NPK fertilizers
        NFertiliserType.ammonia_liquid: 0.03  # Anhydrous ammonia
    }, "warm_climate": {
        NFertiliserType.ammonium_nitrate: 0.03,
        NFertiliserType.urea: 0.17,
        NFertiliserType.ureaAN: 0.10,
        NFertiliserType.mono_ammonium_phosphate: 0.10,
        NFertiliserType.di_ammonium_phosphate: 0.10,
        NFertiliserType.an_phosphate: 0.10,  # Other complex NK, NPK fertilizers
        NFertiliserType.lime_ammonium_nitrate: 0.02,  # Calcium ammonium nitrate (CAN)
        NFertiliserType.ammonium_sulphate: 0.17,
        NFertiliserType.potassium_nitrate: 0.10,  # Other complex NK, NPK fertilizers
        NFertiliserType.ammonia_liquid: 0.04  # Anhydrous ammonia
    }}

    # Heavy-metal contents of mineral fertilisers (Fix F4c): Freiermuth 2006 Tab. 6 in
    # data/hm_mineral_fertiliser_mg_per_kg_nutrient.csv (mg per kg N, P2O5, K2O or CaO; no Hg
    # data -> 0), rows assigned to the legacy fertiliser types by data/hm_fertiliser_row_mapping.csv
    # (generic means for compound and "other" fertilisers; Zn fertilisers stoichiometric).
    _HM_TABLE = "hm_mineral_fertiliser_mg_per_kg_nutrient.csv"
    _HM_ROW_MAPPING = "hm_fertiliser_row_mapping.csv"
    _ELEMENTAL_ZINC_ROW = "elemental_zinc"
    _MG_PER_KG = 1000000.0

    def __init__(self, inputs):
        #TODO: Should we log usage of default value?
        for key in FertModel._input_variables:
            setattr(self, key, inputs[key])

    def computeNH3(self):
        return N_TO_NH3_FACTOR * sum(self._compute_nh3_as_n().values())

    def _compute_nh3_as_n(self):
        return {fertKey: fertValue * self._compute_nh3_as_n_for_fert(fertKey) for fertKey, fertValue in
                self.n_fertiliser_quantities.items()}

    def _compute_nh3_as_n_for_fert(self,fert):
        climate = self.climate_zone_1
        soil_ph_under_or_7 = self.soil_with_ph_under_or_7
        if self.cultivation_type.startswith("greenhouse_hydroponic"):
            climate = "temperate_climate"
            soil_ph_under_or_7 = 1.0
        Ef_low_ph = self._EF_NH3N_MIN_N_FERT_PH_UNDER_OR_SEVEN[climate][fert]
        Ef_high_ph = self._EF_NH3N_MIN_N_FERT_PH_OVER_SEVEN[climate][fert]
        return soil_ph_under_or_7 * Ef_low_ph + (1.0 - soil_ph_under_or_7) * Ef_high_ph

    def computeHeavyMetal(self):
        """Heavy-metal input with mineral fertilisers, map HeavyMetalType -> mg/ha.

        kg nutrient x input_to_row_factor x mg/kg nutrient of the Tab. 6 row (keyed by metal
        name, so that each metal lands in its own column); Zn fertilisers: kg Zn x 1e6 mg/kg.
        """
        total_hm_values = dict.fromkeys(HeavyMetalType, 0.0)
        for quantities in (self.n_fertiliser_quantities, self.p_fertiliser_quantities,
                           self.k_fertiliser_quantities, self.ca_fertiliser_quantities,
                           self.zn_fertiliser_quantities):
            self._add_hm_values_for_fert_type(total_hm_values, quantities)
        return total_hm_values

    def _add_hm_values_for_fert_type(self, total_hm_values, fert_quantities):
        mapping = dataloader.table(self._HM_ROW_MAPPING)
        contents = dataloader.table(self._HM_TABLE)
        for fert_type, quantity in fert_quantities.items():
            row = mapping[fert_type.value]
            kg_reference_nutrient = quantity * row["input_to_row_factor"]
            if row["tab6_row"] == self._ELEMENTAL_ZINC_ROW:
                total_hm_values[HeavyMetalType.zn] += kg_reference_nutrient * self._MG_PER_KG
                continue
            content = contents[row["tab6_row"]]
            for element in HeavyMetalType:
                total_hm_values[element] += kg_reference_nutrient * (content.get(element.name.capitalize()) or 0.0)

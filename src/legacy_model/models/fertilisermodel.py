from enum import Enum

import dataloader
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
      magnesium_from_fertilizer: kg Mg/ha
      soil_with_ph_under_or_7: ratio
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
                        "magnesium_from_fertilizer",
                        "soil_with_ph_under_or_7",
                        "cultivation_type"
                        ]

    # NH3 after mineral N fertiliser application: EMEP/EEA 2023 3.D Tier 2, Table 3-2 (decision L38,
    # data/emep2023_3d_table3_2.csv, g NH3 per kg N applied on soils of normal pH <= 7.0 and of high
    # pH > 7.0, no climate classes), rows assigned to the legacy fertiliser types by
    # data/emep2023_fertiliser_type_mapping.csv.
    _NH3_EF_TABLE = "emep2023_3d_table3_2.csv"
    _NH3_EF_MAPPING = "emep2023_fertiliser_type_mapping.csv"
    _G_PER_KG = 1000.0

    # Heavy-metal contents of mineral fertilisers: SALCAheavymetal 2023 Table 1 (decision L10,
    # data/hm_salca2023_table1.csv, mg per kg N, P2O5, K2O, Ca or Mg, Hg included), rows assigned
    # to the legacy fertiliser types by data/hm_fertiliser_row_mapping.csv; Zn fertilisers are
    # stoichiometric (1 kg Zn = 1e6 mg Zn).
    _HM_ROW_MAPPING = "hm_fertiliser_row_mapping.csv"
    _ELEMENTAL_ZINC_ROW = "elemental_zinc"
    _MAGNESIUM_KEY = "magnesium_from_fertilizer"
    _MG_PER_KG = 1000000.0

    def __init__(self, inputs):
        #TODO: Should we log usage of default value?
        for key in FertModel._input_variables:
            setattr(self, key, inputs[key])

    def computeNH3(self):
        """NH3 after mineral N fertiliser application, kg NH3/ha (EMEP/EEA 2023 3.D Tier 2, Eq. (4)).

        Sum over the N fertiliser types of kg N x (p x EF normal pH + (1 - p) x EF high pH), with
        p = soil_with_ph_under_or_7, the share of soils with pH <= 7.0.
        """
        share_normal_ph = self.soil_with_ph_under_or_7
        if self.cultivation_type.startswith("greenhouse_hydroponic"):
            # legacy, undocumented, provisional: hydroponic greenhouses count as normal pH
            share_normal_ph = 1.0
        total = 0.0
        for fert_type, quantity in self.n_fertiliser_quantities.items():
            ef_normal_ph, ef_high_ph = self.nh3_emission_factors(fert_type)
            total += quantity * (share_normal_ph * ef_normal_ph + (1.0 - share_normal_ph) * ef_high_ph)
        return total

    @classmethod
    def nh3_emission_factors(cls, fert_type):
        """kg NH3 per kg N applied of an NFertiliserType, (normal pH, high pH)."""
        emep_type = dataloader.table(cls._NH3_EF_MAPPING, numeric=False)[fert_type.value]["emep_fertiliser_type"]
        row = dataloader.table(cls._NH3_EF_TABLE)[emep_type]
        return row["ef_normal_ph"] / cls._G_PER_KG, row["ef_high_ph"] / cls._G_PER_KG

    def computeHeavyMetal(self):
        """Heavy-metal input with mineral fertilisers, map HeavyMetalType -> mg/ha.

        kg nutrient x input_to_row_factor x mg/kg nutrient of the Table 1 row, for N, P, K, Ca and
        Zn fertilisers and for the Mg applied (magnesium_from_fertilizer, kg Mg).
        """
        total_hm_values = dict.fromkeys(HeavyMetalType, 0.0)
        for quantities in (self.n_fertiliser_quantities, self.p_fertiliser_quantities,
                           self.k_fertiliser_quantities, self.ca_fertiliser_quantities,
                           self.zn_fertiliser_quantities):
            for fert_type, quantity in quantities.items():
                self._add_hm_values(total_hm_values, fert_type.value, quantity)
        self._add_hm_values(total_hm_values, self._MAGNESIUM_KEY, self.magnesium_from_fertilizer)
        return total_hm_values

    def _add_hm_values(self, total_hm_values, mapping_key, quantity):
        row = dataloader.table(self._HM_ROW_MAPPING)[mapping_key]
        kg_reference_nutrient = quantity * row["input_to_row_factor"]
        if row["salca2023_row"] == self._ELEMENTAL_ZINC_ROW:
            total_hm_values[HeavyMetalType.zn] += kg_reference_nutrient * self._MG_PER_KG
            return
        content = dataloader.hm_entry(row["salca2023_row"])
        for element in HeavyMetalType:
            total_hm_values[element] += kg_reference_nutrient * content[element.name.capitalize()]

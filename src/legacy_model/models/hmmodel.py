from enum import Enum

import dataloader
from models.atomicmass import MA_Zn
from models.modelEnums import HeavyMetalType


class PesticideType(Enum):
        cu="copper_cu" #fungicide
        mancozeb="mancozeb" #fungicide
        metiram="metiram" #fungicide
        propineb="propineb" #fungicide
        zineb="zineb" #fungicide
        ziram="ziram" #fungicide

class LandUseCategoryForHM(Enum):
        permanent_grassland=1
        arable_land=2
        horticultural_crops=3

# Column names of the heavy-metal CSV tables, in the order of HeavyMetalType
METAL_COLUMNS = {HeavyMetalType.cd: "Cd", HeavyMetalType.cu: "Cu", HeavyMetalType.zn: "Zn",
                 HeavyMetalType.pb: "Pb", HeavyMetalType.ni: "Ni", HeavyMetalType.cr: "Cr",
                 HeavyMetalType.hg: "Hg"}


class HmModel(object):
    """Heavy-metal balance, SALCA-heavy metal (Freiermuth 2006) as in Quantis (2019) section 2.7,
    written in the SALCAheavymetal 2023 form (Nemecek et al. 2023, ESM7 Eq. 3-7) - Fix F4:

      A_i      = M_agro,i / (M_agro,i + m_dep,i x t)            (0 when M_agro,i = 0)
      harvest  = export_i x A_i
      leaching = m_leach,i x t x A_i   (split ground / surface water by the drained share)
      erosion  = c_soil,i x Ser x t x 1.86 x 0.2 x A_i
      soil     = M_agro,i - harvest - leaching - erosion

    Identical to Msoil = (inputs + deposition - unallocated outputs) x A_i of Freiermuth 2006:
    the allocation factor is applied exactly once to each output.

    Inputs:
      crop_cycle_per_year: ratio (occupation period t = 1 / crop_cycle_per_year years)
      hm_from_manure : map HeavyMetalType -> mg i/(ha*crop cycle)
      hm_from_mineral_fert : map HeavyMetalType -> mg i/(ha*crop cycle)
      hm_from_other_organic_fert : map HeavyMetalType -> mg i/(ha*crop cycle)
      hm_from_seed: map HeavyMetalType -> mg i/(ha*crop cycle)
      hm_pesticides_quantities: map PesticideType -> g a.i./(ha*crop cycle)
      hm_export_with_harvest: map HeavyMetalType -> mg i/(ha*crop cycle) in the harvested product
      drained_part: ratio (decision D5: template "drainage")
      eroded_soil: kg/(ha*year)
      hm_land_use_category: LandUseCategoryForHM

    Outputs (kg i/(ha*crop cycle), map HeavyMetalType -> value):
        m_hm_heavymetal_to_soil: balance without the harvest export ("heavy_metal_uptake" off)
        m_hm_heavymetal_to_soil_minus_uptake: balance with the harvest export (default)
        m_hm_heavymetal_to_ground_water, m_hm_heavymetal_to_surface_water

    Parameters (data/): hm_deposition_mg_per_ha_yr.csv, hm_leaching_mg_per_ha_yr.csv (Ni NA -> 0),
    hm_soil_content_mg_per_kg.csv, hm_pesticide_fungicides.csv, model_parameters.csv
    (hm_accumulation_factor 1.86, hm_erosion_factor 0.2, hm_pesticide_soil_fraction 0.95).
    """

    _input_variables = ['crop_cycle_per_year',
                        'hm_from_manure',
                        'hm_from_mineral_fert',
                        'hm_from_other_organic_fert',
                        'hm_from_seed',
                        'hm_pesticides_quantities',
                        'hm_export_with_harvest',
                        'drained_part',
                        'eroded_soil',
                        'hm_land_use_category'
                        ]

    def __init__(self, inputs):
        #TODO: Should we log usage of default value?
        for key in HmModel._input_variables:
            setattr(self, key, inputs[key])

    def compute(self):
        t = self._duration_years()
        deposition = dataloader.single_metal_row("hm_deposition_mg_per_ha_yr.csv", METAL_COLUMNS.values())
        leaching_rate = dataloader.single_metal_row("hm_leaching_mg_per_ha_yr.csv", METAL_COLUMNS.values())
        soil_content = dataloader.metal_row("hm_soil_content_mg_per_kg.csv",
                                            self.hm_land_use_category.name, METAL_COLUMNS.values())
        accumulation = dataloader.param("hm_accumulation_factor")
        erosion_factor = dataloader.param("hm_erosion_factor")
        pesticides = self._compute_pesticides()  # mg/ha

        hm_to_gw, hm_to_sw = {}, {}
        hm_to_soil, hm_to_soil_minus_uptake = {}, {}
        self.last_allocation = {}
        for element, column in METAL_COLUMNS.items():
            agro_input = self._compute_agro_input(pesticides, element)  # mg/ha
            allocation = agro_input / (agro_input + deposition[column] * t) if agro_input > 0 else 0.0
            self.last_allocation[element] = allocation
            harvest = self.hm_export_with_harvest[element] * allocation
            leaching = leaching_rate[column] * t * allocation
            erosion = soil_content[column] * self.eroded_soil * t * accumulation * erosion_factor * allocation
            soil = agro_input - leaching - erosion
            hm_to_soil[element] = soil / 1000000.0
            hm_to_soil_minus_uptake[element] = (soil - harvest) / 1000000.0
            hm_to_gw[element] = leaching * (1.0 - self.drained_part) / 1000000.0
            hm_to_sw[element] = (leaching * self.drained_part + erosion) / 1000000.0

        return {'m_hm_heavymetal_to_soil': hm_to_soil,
                'm_hm_heavymetal_to_ground_water': hm_to_gw,
                'm_hm_heavymetal_to_surface_water': hm_to_sw,
                'm_hm_heavymetal_to_soil_minus_uptake': hm_to_soil_minus_uptake}

    def _duration_years(self):
        return 1.0 / self.crop_cycle_per_year

    def _compute_agro_input(self, pesticides, element):
        """Total agricultural input of a metal [mg/ha]; atmospheric deposition excluded."""
        return    self.hm_from_manure[element] \
                + self.hm_from_mineral_fert[element]\
                + self.hm_from_other_organic_fert[element]\
                + self.hm_from_seed[element] \
                + pesticides[element]

    def _compute_pesticides(self):
        """Cu and Zn reaching the soil with fungicides [mg/ha]: g a.i. x metal share x
        hm_pesticide_soil_fraction x 1000 (data/hm_pesticide_fungicides.csv)."""
        table = dataloader.table("hm_pesticide_fungicides.csv")
        soil_fraction = dataloader.param("hm_pesticide_soil_fraction")
        hm_values = dict.fromkeys(HeavyMetalType, 0.0)
        for pest, grams in self.hm_pesticides_quantities.items():
            row = table[pest.value]
            if row["molar_mass_g_per_mol"] is None:
                metal_share = 1.0  # elemental metal (copper)
            else:
                metal_share = MA_Zn / row["molar_mass_g_per_mol"] * row["metal_atoms_per_molecule"]
            element = HeavyMetalType[row["metal"].lower()]
            hm_values[element] += grams * metal_share * soil_fraction * 1000.0
        return hm_values

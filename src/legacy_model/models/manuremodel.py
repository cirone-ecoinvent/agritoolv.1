from enum import Enum

import dataloader
from models.atomicmass import N_TO_NH3_FACTOR
from models.modelEnums import HeavyMetalType


class LiquidManureType(Enum):
    cattle = "liquid_manure_cattle"
    pig = "liquid_manure_pig"
    laying_hens = "liquid_manure_laying_hen"
    other = "liquid_manure_other"

class SolidManureType(Enum):
    cattle = "solid_manure_cattle"
    horses = "solid_manure_horses"
    laying_hen_litter = "solid_manure_laying_hen"
    pigs = "solid_manure_pig"
    sheep_goats = "solid_manure_sheep_goat"
    other = "solid_manure_other"


class ManureTypeForHM(Enum):
    cattle_liquid=1,
    cattle_low_excrement=2,#liquid
    cattle_stackable=3,#solid
    cattle_loose_housing=4,#solid
    pig_liquid=5,
    pig_solid=6,
    laying_hen_manure=7,#liquid
    laying_hen_litter=8#solid #( + broiler)

class ManureModel(object):
    """Inputs:
      liquid_manure_part_before_dilution: ratio
      liquid_manure_quantities: map LiquidManureType -> m3/ha
      solid_manure_quantities: map SolidManureType -> kg/ha

    Outputs:
      computeP2O5: tuple of:
        P2O5 contents liquid manure: kg P2O5/ha
        P2O5 contents solid manure: kg P2O5/ha
      computeN:
        N_total_manure: kg N/ha
      computeNH3:
        nh3_total_manure: kg NH3/ha
      computeHeavyMetal:
        hm_total_manure : map HeavyMetalType -> mg i/ha (i:hm type)
    """

    _input_variables = ["liquid_manure_part_before_dilution",
                        "liquid_manure_quantities",
                        "solid_manure_quantities"
                       ]

    _P205_CONCENTRATION_IN_LIQUID_MANURE = {LiquidManureType.cattle: 1.5,
                                            LiquidManureType.pig: 3.5,#mean fattening pigs + piglets
                                            LiquidManureType.laying_hens: 17.0,
                                            LiquidManureType.other: 3.40798 #Sumprod of concentration with world proportions
                                           }

    _P205_CONCENTRATION_IN_SOLID_MANURE = {SolidManureType.cattle: 2.7,
                                           SolidManureType.horses: 5.0,
                                           SolidManureType.laying_hen_litter: 25.0,#mean with broiler
                                           SolidManureType.pigs: 7.0,
                                           SolidManureType.sheep_goats: 3.3,
                                           SolidManureType.other: 7.40504 #Sumprod of concentration with world proportions
                                          }

    _N_CONCENTRATION_IN_LIQUID_MANURE = {LiquidManureType.cattle: 4.6,
                                         LiquidManureType.pig: 5.35,#mean fattening pigs + piglets
                                         LiquidManureType.laying_hens: 21.0,
                                         LiquidManureType.other: 6.33529 #Sumprod of concentration with world proportions
                                        }

    _N_CONCENTRATION_IN_SOLID_MANURE = {SolidManureType.cattle: 5.1,
                                        SolidManureType.horses: 6.8,
                                        SolidManureType.laying_hen_litter: 30.5,#mean with broiler
                                        SolidManureType.pigs: 7.8,
                                        SolidManureType.sheep_goats: 8.0,
                                        SolidManureType.other: 10.40797 #Sumprod of concentration with world proportions
                                       }
    # TAN content and NH3 emission fraction per manure type: data/manure_nh3.csv
    # (kg N per m3 for liquid manure, per t for solid manure).
    _NH3_TABLE = "manure_nh3.csv"

    @classmethod
    def _nh3_n_per_unit(cls, manure_type):
        """NH3-N emitted per m3 (liquid) or per t (solid) of manure [kg N]."""
        return dataloader.table(cls._NH3_TABLE)[manure_type.value]["nh3_n_kg_per_unit"]

    @classmethod
    def _tan_per_unit(cls, manure_type):
        """TAN (soluble N) per m3 or per t of manure [kg N]; None when not separable."""
        return dataloader.table(cls._NH3_TABLE)[manure_type.value]["tan_kg_n_per_unit"]

    # Heavy metals (Fix F4d): contents and dry-matter shares of the Freiermuth 2006 Tab. 7
    # manure classes in data/hm_manure_mg_per_kg_dm.csv; the legacy input types are
    # redistributed to those classes by data/hm_manure_class_mapping.csv (legacy shares).
    _HM_TABLE = "hm_manure_mg_per_kg_dm.csv"
    _HM_CLASS_MAPPING = "hm_manure_class_mapping.csv"
    _MG_PER_KG = 1000000.0

    def __init__(self, inputs):
        #TODO: Should we log usage of default value?
        for key in ManureModel._input_variables:
            setattr(self, key, inputs[key])

    def computeP2O5(self):
        return (self._sum_prod(self._P205_CONCENTRATION_IN_LIQUID_MANURE, self.liquid_manure_quantities)
                    * self.liquid_manure_part_before_dilution,
                self._sum_prod(self._P205_CONCENTRATION_IN_SOLID_MANURE, self.solid_manure_quantities)/ 1000.0)

    def computeN(self):
        return self._sum_prod(self._N_CONCENTRATION_IN_LIQUID_MANURE, self.liquid_manure_quantities) \
                    * self.liquid_manure_part_before_dilution \
                + self._sum_prod(self._N_CONCENTRATION_IN_SOLID_MANURE, self.solid_manure_quantities)/ 1000.0

    def computeNH3(self):
        """NH3 [kg NH3/ha] after spreading: TAN x emission fraction per manure type."""
        nh3_as_n = self._sum_per_unit(self._nh3_n_per_unit)
        return nh3_as_n * N_TO_NH3_FACTOR

    def computeSolubleN(self):
        """Soluble (ammoniacal) N applied with manure [kg N/ha] (Fix F3).

        TAN content per manure type from data/manure_nh3.csv; for the "other" categories the
        TAN is not separable from the legacy sum-product and the total N is used instead.
        """
        def soluble(manure_type):
            tan = self._tan_per_unit(manure_type)
            if tan is not None:
                return tan
            table = (self._N_CONCENTRATION_IN_LIQUID_MANURE if isinstance(manure_type, LiquidManureType)
                     else self._N_CONCENTRATION_IN_SOLID_MANURE)
            return table[manure_type]
        return self._sum_per_unit(soluble)

    def _sum_per_unit(self, value_per_unit):
        """sum(quantity x value_per_unit(type)): liquid m3 x dilution share, solid kg -> t."""
        liquid = sum(v * value_per_unit(k) for k, v in self.liquid_manure_quantities.items()) \
                 * self.liquid_manure_part_before_dilution
        solid = sum(v * value_per_unit(k) for k, v in self.solid_manure_quantities.items()) / 1000.0
        return liquid + solid

    def _sum_prod(self, reference, factors):
        return sum(v*factors[k] for k,v in reference.items())

    def computeHeavyMetal(self):
        """Heavy-metal input with manure, map HeavyMetalType -> mg/ha (Fix F4d,
        reference_models.hm_input_manure): kg FM x class share x DM x mg/kg DM.

        Liquid manure: m3 x undiluted share x density (liquid_manure_density_kg_per_m3) -> kg FM;
        solid manure: kg FM as entered. The legacy code multiplied tonnes instead of kg and
        therefore returned g/ha, 1000 times too low.
        """
        kg_fresh_matter = self._fresh_matter_kg()
        contents = dataloader.table(self._HM_TABLE)
        hm_element_values = dict.fromkeys(HeavyMetalType, 0.0)
        for row in dataloader.rows(self._HM_CLASS_MAPPING):
            kg_fm = kg_fresh_matter.get(row["legacy_manure_type"], 0.0) * float(row["share"])
            if kg_fm == 0.0:
                continue
            manure_class = contents[row["tab7_manure_class"]]
            kg_dm = kg_fm * manure_class["dm_fraction"]
            for element in HeavyMetalType:
                hm_element_values[element] += kg_dm * (manure_class.get(element.name.capitalize()) or 0.0)
        return hm_element_values

    def _fresh_matter_kg(self):
        """Fresh matter applied per legacy manure type [kg/ha]."""
        density = dataloader.param("liquid_manure_density_kg_per_m3")
        result = {k.value: v * self.liquid_manure_part_before_dilution * density
                  for k, v in self.liquid_manure_quantities.items()}
        result.update({k.value: v for k, v in self.solid_manure_quantities.items()})
        return result

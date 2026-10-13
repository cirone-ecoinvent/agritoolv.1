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

    # Contents per manure type (kg per m3 of undiluted liquid manure, per t of solid manure),
    # decision L12: N, P2O5 and TAN (soluble N) from GRUDAF 2009 Table 39, NH3-N = TAN x
    # spreading EF of EMEP/EEA 2023 3.B Table 3-9, combined with the weights of
    # data/manure_type_composition.csv. The "other" types are world mixes of the specific types
    # of the same form (decision L13): FAOSTAT manure N applied to soils per livestock item,
    # grouped by data/manure_other_faostat_mapping.csv and converted to volume (mass) shares.
    # The default shares per country use the same mapping with the FAOSTAT N of the country
    # (decision L29).
    _COMPOSITION_TABLE = "manure_type_composition.csv"
    _CONTENT_TABLE = "grudaf2009_table39.csv"
    _EF_TABLE = "emep2023_3b_table3_9.csv"
    _FAOSTAT_MAPPING = "manure_other_faostat_mapping.csv"
    _FAOSTAT_TABLE = "faostat_manure_n_applied_world.csv"
    _FAOSTAT_COUNTRY_TABLE = "faostat_manure_n_applied_country.csv"
    _OTHER_TYPES = {LiquidManureType.other: LiquidManureType, SolidManureType.other: SolidManureType}

    @classmethod
    def _application_ef(cls, livestock, manure_type):
        """EMEP/EEA 2023 3.B Table 3-9 spreading EF (fraction of TAN) of one row."""
        for row in dataloader.rows(cls._EF_TABLE):
            if row["livestock"] == livestock and row["manure_type"] == manure_type:
                return float(row["ef_application"])
        raise KeyError("No row %s / %s in %s" % (livestock, manure_type, cls._EF_TABLE))

    @classmethod
    def _content(cls, manure_type, quantity):
        """Content per m3 or per t of manure [kg]; quantity is n_total, p2o5, tan, nh3_n or
        n_available (GRUDAF Nverf, plant-available N: mean of the range of Table 39)."""
        if manure_type in cls._OTHER_TYPES:
            return sum(share * cls._content(component, quantity)
                       for component, share in cls._other_shares(manure_type).items())
        contents = dataloader.table(cls._CONTENT_TABLE)
        total = 0.0
        found = False
        for row in dataloader.rows(cls._COMPOSITION_TABLE):
            if row["manure_type"] != manure_type.value:
                continue
            found = True
            content = contents[row["grudaf_row_id"]]
            if quantity == "tan":
                value = content["n_soluble"]
            elif quantity == "nh3_n":
                value = content["n_soluble"] * cls._application_ef(row["emep_livestock"],
                                                                  row["emep_manure_type"])
            elif quantity == "n_available":
                value = (content["n_available_min"] + content["n_available_max"]) / 2.0
            else:
                value = content[quantity]
            total += float(row["weight"]) * value
        if not found:
            raise KeyError("Manure type %s not in %s" % (manure_type.value, cls._COMPOSITION_TABLE))
        return total

    @classmethod
    def _other_shares(cls, other_type):
        """Volume (liquid) or mass (solid) shares of the specific types in an "other" mix.

        FAOSTAT gives the world manure N per livestock item; the N share of each type is
        divided by its N content per unit and normalised, so that the shares refer to m3 or t.
        """
        enum = cls._OTHER_TYPES[other_type]
        form = "liquid" if enum is LiquidManureType else "solid"
        faostat = dataloader.table(cls._FAOSTAT_TABLE)
        n_applied = {}
        for row in dataloader.rows(cls._FAOSTAT_MAPPING):
            if row["form"] == form:
                component = enum(row["manure_type"])
                n_applied[component] = (n_applied.get(component, 0.0)
                                        + faostat[row["faostat_item"]]["n_applied_mean_2021_2023_kg"])
        return cls._unit_shares(n_applied)

    @classmethod
    def _unit_shares(cls, n_per_type):
        """Volume (liquid) or mass (solid) shares from the N per manure type: N / N content per
        m3 or t, normalised."""
        units = {k: v / cls._content(k, "n_total") for k, v in n_per_type.items()}
        total_units = sum(units.values())
        return {k: v / total_units for k, v in units.items()}

    @classmethod
    def _country_n(cls, country):
        """FAOSTAT manure N applied to soils of a country per manure type, {enum: {type: kg N}}.

        Items are grouped by data/manure_other_faostat_mapping.csv. WFLDB rule (Guidelines v3.0
        section 3.6.2): an item mapped to both forms (cattle, buffalo, pigs, laying hens) is half
        liquid and half solid, the other items are solid only; items not in the mapping (camels,
        llamas) are left out.
        """
        n_item = {row["item"]: float(row["n_applied_mean_kg"])
                  for row in dataloader.rows(cls._FAOSTAT_COUNTRY_TABLE) if row["country"] == country}
        if not n_item:
            raise KeyError("Country %s not in %s" % (country, cls._FAOSTAT_COUNTRY_TABLE))
        mapping = {}
        for row in dataloader.rows(cls._FAOSTAT_MAPPING):
            mapping.setdefault(row["faostat_item"], []).append(row)
        n_per_type = {LiquidManureType: dict.fromkeys(LiquidManureType, 0.0),
                      SolidManureType: dict.fromkeys(SolidManureType, 0.0)}
        for item, rows in mapping.items():
            for row in rows:
                enum = LiquidManureType if row["form"] == "liquid" else SolidManureType
                n_per_type[enum][enum(row["manure_type"])] += n_item.get(item, 0.0) / len(rows)
        return n_per_type

    @classmethod
    def country_shares(cls, country):
        """Default shares of the manure types in a country (decision L29): liquid volume shares
        and solid mass shares, ({LiquidManureType: share}, {SolidManureType: share})."""
        n_per_type = cls._country_n(country)
        return tuple(cls._unit_shares(n_per_type[enum]) for enum in (LiquidManureType, SolidManureType))

    @classmethod
    def liquid_n_fraction(cls, country):
        """Share of the country's manure N applied as liquid manure (decision L29)."""
        n_per_type = cls._country_n(country)
        liquid = sum(n_per_type[LiquidManureType].values())
        return liquid / (liquid + sum(n_per_type[SolidManureType].values()))

    @classmethod
    def mix_content(cls, proportions, quantity):
        """Content per m3 of undiluted liquid manure or per t of solid manure [kg] of a mix of
        manure types, {type: share}; quantity as for _content."""
        return sum(share * cls._content(manure_type, quantity)
                   for manure_type, share in proportions.items() if share)

    # Heavy metals: contents [mg/kg DM] and dry-matter shares of the farmyard-manure rows of
    # SALCAheavymetal 2023 Table 1 (decision L10); the legacy input types are redistributed to
    # those rows by data/hm_manure_class_mapping.csv.
    _HM_CLASS_MAPPING = "hm_manure_class_mapping.csv"
    _MG_PER_KG = 1000000.0

    def __init__(self, inputs):
        #TODO: Should we log usage of default value?
        for key in ManureModel._input_variables:
            setattr(self, key, inputs[key])

    def computeP2O5(self):
        def p2o5(manure_type):
            return self._content(manure_type, "p2o5")
        return (sum(v * p2o5(k) for k, v in self.liquid_manure_quantities.items())
                    * self.liquid_manure_part_before_dilution,
                sum(v * p2o5(k) for k, v in self.solid_manure_quantities.items()) / 1000.0)

    def computeN(self):
        return self._sum_per_unit(lambda manure_type: self._content(manure_type, "n_total"))

    def computeNH3(self):
        """NH3 [kg NH3/ha] after spreading: TAN x emission fraction per manure type."""
        nh3_as_n = self._sum_per_unit(lambda manure_type: self._content(manure_type, "nh3_n"))
        return nh3_as_n * N_TO_NH3_FACTOR

    def computeSolubleN(self):
        """Soluble (ammoniacal) N applied with manure [kg N/ha] (Fix F3).

        TAN content per manure type (GRUDAF 2009 Table 39, decisions L12 and L13).
        """
        return self._sum_per_unit(lambda manure_type: self._content(manure_type, "tan"))

    def _sum_per_unit(self, value_per_unit):
        """sum(quantity x value_per_unit(type)): liquid m3 x dilution share, solid kg -> t."""
        liquid = sum(v * value_per_unit(k) for k, v in self.liquid_manure_quantities.items()) \
                 * self.liquid_manure_part_before_dilution
        solid = sum(v * value_per_unit(k) for k, v in self.solid_manure_quantities.items()) / 1000.0
        return liquid + solid

    def computeHeavyMetal(self):
        """Heavy-metal input with manure, map HeavyMetalType -> mg/ha (Fix F4d,
        reference_models.hm_input_manure): kg FM x class share x DM x mg/kg DM.

        Liquid manure: m3 x undiluted share x density (liquid_manure_density_kg_per_m3) -> kg FM;
        solid manure: kg FM as entered. The legacy code multiplied tonnes instead of kg and
        therefore returned g/ha, 1000 times too low.
        """
        kg_fresh_matter = self._fresh_matter_kg()
        hm_element_values = dict.fromkeys(HeavyMetalType, 0.0)
        for row in dataloader.rows(self._HM_CLASS_MAPPING):
            kg_fm = kg_fresh_matter.get(row["legacy_manure_type"], 0.0) * float(row["share"])
            if kg_fm == 0.0:
                continue
            manure_class = dataloader.hm_entry(row["salca2023_class"])
            kg_dm = kg_fm * manure_class["dm"]
            for element in HeavyMetalType:
                hm_element_values[element] += kg_dm * manure_class[element.name.capitalize()]
        return hm_element_values

    def _fresh_matter_kg(self):
        """Fresh matter applied per legacy manure type [kg/ha]."""
        density = dataloader.param("liquid_manure_density_kg_per_m3")
        result = {k.value: v * self.liquid_manure_part_before_dilution * density
                  for k, v in self.liquid_manure_quantities.items()}
        result.update({k.value: v for k, v in self.solid_manure_quantities.items()})
        return result

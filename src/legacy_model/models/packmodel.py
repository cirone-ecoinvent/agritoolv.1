from models.fertilisermodel import NFertiliserType
class PackModel(object):
    """Inputs:
        nitrogen_from_mineral_fert: kg N/ha
        p2O5_from_mineral_fert: kg P2O5/ha
        k2O_from_mineral_fert: kg K2O/ha
        magnesium_from_fertilizer: kg Mg/ha
        ca_from_mineral_fert: kg Ca/ha
        zn_from_mineral_fert: kg Zn/ha
        n_fertiliser_quantities: Map NFertiliserType -> kg N/ha
        pest_total: g/ha
        pest_horticultural_oil: kg / ha

    Outputs:
      m_Pack_wfldb_packaging_liquid: kg/ha
      m_Pack_wfldb_packaging_solid: kg/ha
      m_Pack_ecoinvent_packaging_liquid: kg/ha
      m_Pack_ecoinvent_packaging_solid: kg/ha
    """

    _input_variables = ["nitrogen_from_mineral_fert",
                        "p2O5_from_mineral_fert",
                        "k2O_from_mineral_fert",
                        "magnesium_from_fertilizer",
                        "ca_from_mineral_fert",
                        "zn_from_mineral_fert",
                        "n_fertiliser_quantities",
                        "pest_total",
                        "pest_horticultural_oil"
                        ]

    _DILUTION_FACTOR = 2.0;
    _ECOINVENT_FERT_DILUTION_FACTOR = 2.0;
    _ECOINVENT_PEST_DILUTION_FACTOR = 3.0;

    def __init__(self, inputs):
        #TODO: Should we log usage of default value?
        for key in PackModel._input_variables:
            setattr(self, key, inputs[key])

    def compute(self):
        totalFert = self._computeTotalFertilisers();
        fert_solid,fert_liquid = self._computeFertilisers(totalFert)
        pest_solid,pest_liquid = self._computePesticides()

        return {"m_Pack_wfldb_packaging_liquid": (
            (pest_liquid + fert_liquid) * self._DILUTION_FACTOR + self.pest_horticultural_oil),
            "m_Pack_wfldb_packaging_solid": (pest_solid + fert_solid) * self._DILUTION_FACTOR,
                "m_Pack_ecoinvent_packaging_liquid": pest_liquid * self._ECOINVENT_PEST_DILUTION_FACTOR
                                                     + fert_liquid * self._ECOINVENT_FERT_DILUTION_FACTOR
                                                     + self.pest_horticultural_oil,
                "m_Pack_ecoinvent_packaging_solid": pest_solid * self._ECOINVENT_PEST_DILUTION_FACTOR
                                                    + fert_solid * self._ECOINVENT_FERT_DILUTION_FACTOR}

    def _computeTotalFertilisers(self):
        return self.nitrogen_from_mineral_fert \
                + self.p2O5_from_mineral_fert \
                + self.k2O_from_mineral_fert \
                + self.magnesium_from_fertilizer \
                + self.ca_from_mineral_fert \
                + self.zn_from_mineral_fert

    def _computeFertilisers(self, totalFert):
        liquid = self.n_fertiliser_quantities[NFertiliserType.ammonia_liquid]
        solid = totalFert - liquid
        return (solid ,liquid)

    def _computePesticides(self):
        solid = 0.0
        liquid = self.pest_total
        return (solid / 1000.0,liquid /1000.0)

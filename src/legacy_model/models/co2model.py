import dataloader
from models.atomicmass import MA_CO2, MA_UREA, \
    Ca_TO_LIMESTONE_FACTOR, LIMESTONE_TO_CO2_FACTOR, MA_C, MA_N, MA_DOLOMITE
from models.fertilisermodel import NFertiliserType, CaFertiliserType

CAN_COMPOSITION_TABLE = "can_composition.csv"

# CaMg(CO3)2 -> 2 CO2 (IPCC 2006 Vol. 4 ch. 11 Eq. 11.12: 0.13 t C per t of dolomite, x 44/12)
DOLOMITE_TO_CO2_FACTOR = 2 * MA_CO2 / MA_DOLOMITE


def can_co2_per_kg_n():
    """kg fossil CO2 per kg N of calcium ammonium nitrate, from the carbonate of its dolomite filler
    (decision L67; composition in data/can_composition.csv, ecoinvent technical correction CPSTC-520).

    Per kg of N, so it does not depend on the Master Data 3.12 nitrogen content of the product.
    """
    composition = dataloader.table(CAN_COMPOSITION_TABLE)
    dolomite = composition["dolomite"]["kg_per_kg_product"]
    nitrogen = composition["nitrogen"]["kg_per_kg_product"]
    return dolomite * DOLOMITE_TO_CO2_FACTOR / nitrogen


class Co2Model(object):
    """CO2 of lime and urea, IPCC 2006 Vol. 4 ch. 11 Eq. 11.12 and 11.13 (no refinement in 2019), with the
    stoichiometric factors (decision L67).

    Inputs:
      n_fertiliser_quantities: map NFertiliserType -> kg N/ha
      part_of_urea_in_UAN: share of the N of UAN counted as urea N (default 1.0, IPCC 2006 p. 11.32)
      ca_fertiliser_quantities: map CaFertiliserType -> kg Ca/ha
      dolomite_applied: kg dolomite (CaMg(CO3)2, product) / ha

    Outputs:
      m_co2_CO2_from_fertilisers: kg CO2/ha, fossil (urea, UAN, limestone, carbonation lime, dolomite, the
        dolomite of calcium ammonium nitrate)
      m_co2_CO2_non_fossil_from_fertilisers: kg CO2/ha, non-fossil (seaweed lime, decision L17)

    The carbon of lime from algae is biogenic: Master Data 3.12 "limestone, from algae" has
    carbon content, fossil 0 and carbon content, non-fossil 0.107 (CaCO3 of the algae).
    Oxides and hydroxides of lime (CaO, Ca(OH)2) contain no inorganic carbon and give no CO2 (IPCC 2006
    p. 11.27, Step 1); the model has no such fertiliser type.
    """
    _input_variables = ["n_fertiliser_quantities",
                        "part_of_urea_in_UAN",
                        "ca_fertiliser_quantities",
                        "dolomite_applied"
                        ]

    #2 N -> 1 UREA -> 1 C -> 1 CO2
    _UREA_N_TO_CO2_FACTOR = MA_UREA/(MA_N*2) * MA_C/MA_UREA * MA_CO2/MA_C #1.57
    _CA_TO_CO2_FACTOR = Ca_TO_LIMESTONE_FACTOR * LIMESTONE_TO_CO2_FACTOR #(_CO2)/ 40.078

    def __init__(self, inputs):
        for key in Co2Model._input_variables:
            setattr(self, key, inputs[key])

    def compute(self):
        co2 = self._compute_co2()
        return {'m_co2_CO2_from_fertilisers': co2,
                'm_co2_CO2_non_fossil_from_fertilisers': self._compute_CO2_from_seaweed_lime()}

    def _compute_co2(self):
        return self._compute_CO2_from_urea() + self._compute_CO2_from_lime() \
            + self._compute_CO2_from_calcium_ammonium_nitrate()

    def _compute_CO2_from_urea(self):
        return self._UREA_N_TO_CO2_FACTOR * (self.n_fertiliser_quantities[NFertiliserType.urea] + self.part_of_urea_in_UAN * self.n_fertiliser_quantities[NFertiliserType.ureaAN])

    def _compute_CO2_from_lime(self):
        return self._CA_TO_CO2_FACTOR * \
               (self.ca_fertiliser_quantities[CaFertiliserType.ca_limestone] + \
                self.ca_fertiliser_quantities[CaFertiliserType.ca_carbonation_limestone]) \
               + self._compute_CO2_from_dolomite()

    def _compute_CO2_from_seaweed_lime(self):
        # kg Ca -> CaCO3 -> CO2 as for limestone, but non-fossil carbon (decision L17)
        return self._CA_TO_CO2_FACTOR * self.ca_fertiliser_quantities[CaFertiliserType.ca_seaweed_limestone]

    def _compute_CO2_from_dolomite(self):
        return DOLOMITE_TO_CO2_FACTOR * self.dolomite_applied

    def _compute_CO2_from_calcium_ammonium_nitrate(self):
        # lime applied in mixture with fertilisers is counted (IPCC 2006 p. 11.27, Step 1)
        return can_co2_per_kg_n() * self.n_fertiliser_quantities[NFertiliserType.lime_ammonium_nitrate]

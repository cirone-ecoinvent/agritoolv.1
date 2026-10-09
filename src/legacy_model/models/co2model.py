from models.atomicmass import MG_TO_DOLOMITE_FACTOR, MA_CO2, MA_UREA, \
    Ca_TO_LIMESTONE_FACTOR, LIMESTONE_TO_CO2_FACTOR, MA_C, MA_N, MA_DOLOMITE
from models.fertilisermodel import NFertiliserType, CaFertiliserType


class Co2Model(object):
    """Inputs:
      #TODO: Should we directly receive a CO2 value from the fert module?
      n_fertiliser_quantities: map NFertiliserType -> kg N/ha
      part_of_urea_in_UAN: ratio
      ca_fertiliser_quantities: map CaFertiliserType -> kg Ca/ha
      magnesium_from_fertilizer: kg Mg / ha
      magnesium_as_dolomite: ratio

    Outputs:
      m_co2_CO2_from_fertilisers: kg/ha
    """
    _input_variables = ["n_fertiliser_quantities",
                        "part_of_urea_in_UAN",
                        "ca_fertiliser_quantities",
                        "magnesium_from_fertilizer",
                        "magnesium_as_dolomite"
                        ]

    #2 N -> 1 UREA -> 1 C -> 1 CO2
    _UREA_N_TO_CO2_FACTOR = MA_UREA/(MA_N*2) * MA_C/MA_UREA * MA_CO2/MA_C #1.57
    _CA_TO_CO2_FACTOR = Ca_TO_LIMESTONE_FACTOR * LIMESTONE_TO_CO2_FACTOR #(_CO2)/ 40.078

    _DOLOMITE_TO_CO2_FACTOR = 2*MA_CO2 / MA_DOLOMITE
    _MG_TO_CO2_FACTOR = MG_TO_DOLOMITE_FACTOR * _DOLOMITE_TO_CO2_FACTOR  # (_CO2)*2/24.305

    def __init__(self, inputs):
        #TODO: Should we log usage of default value?
        for key in Co2Model._input_variables:
            setattr(self, key, inputs[key])

    def compute(self):
        co2 = self._compute_co2()
        return {'m_co2_CO2_from_fertilisers': co2}

    def _compute_co2(self):
        co2_from_urea = self._compute_CO2_from_urea()
        co2_from_lime = self._compute_CO2_from_lime()
        return co2_from_urea + co2_from_lime;

    def _compute_CO2_from_urea(self):
        return self._UREA_N_TO_CO2_FACTOR * (self.n_fertiliser_quantities[NFertiliserType.urea] + self.part_of_urea_in_UAN * self.n_fertiliser_quantities[NFertiliserType.ureaAN]);

    def _compute_CO2_from_lime(self):
        return self._CA_TO_CO2_FACTOR * \
               (self.ca_fertiliser_quantities[CaFertiliserType.ca_limestone] + \
                self.ca_fertiliser_quantities[CaFertiliserType.ca_carbonation_limestone] + \
                self.ca_fertiliser_quantities[CaFertiliserType.ca_seaweed_limestone]) \
               + self._compute_CO2_from_magnesium();

    def _compute_CO2_from_magnesium(self):
        return self._MG_TO_CO2_FACTOR * self.magnesium_from_fertilizer * self.magnesium_as_dolomite;

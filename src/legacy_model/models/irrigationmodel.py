from enum import Enum

class IrrigationType(Enum):
    surface_irrigation_no_energy="surface_irrigation_no_energy"
    surface_irrigation_electricity="surface_irrigation_electricity"
    surface_irrigation_diesel="surface_irrigation_diesel"
    sprinkler_irrigation_electricity="sprinkler_irrigation_electricity"
    sprinkler_irrigation_diesel="sprinkler_irrigation_diesel"
    drip_irrigation_electricity="drip_irrigation_electricity"
    drip_irrigation_diesel="drip_irrigation_diesel"

class WaterUseType(Enum):
    groundwater="wateruse_ground"
    surfacewater="wateruse_surface"
    nonconventional="wateruse_non_conventional_sources"

class IrrigationModel(object):
    """Inputs:
        water_use_total: m3/ha
        irrigation_types_proportions: map IrrigationType -> ratio. Sum should be 1

    Outputs:
      m_Irr_wfldb_water_to_air:m3/ha
      m_Irr_wfldb_water_to_water_river: m3/ha
      m_Irr_wfldb_water_to_water_groundwater: m3/ha
    """

    _input_variables = ["water_use_total",
                        "irrigation_types_proportions"
                       ]

    _IRRIGATION_EFFICIENCY_FACTOR_SURFACE = 0.45
    _IRRIGATION_EFFICIENCY_FACTOR_SPRINKLER = 0.75
    _IRRIGATION_EFFICIENCY_FACTOR_DRIP = 0.9

    def __init__(self, inputs):
        #TODO: Should we log usage of default value?
        for key in IrrigationModel._input_variables:
            setattr(self, key, inputs[key])

    def compute(self):
        irrigation_efficiency_ratio = self._compute_irrigation_efficiency_ratio()
        evapotranspiration = self._compute_evapotranspiration(irrigation_efficiency_ratio)
        total_remaining_water = self._compute_remaining_water_after_evapotranspiration(evapotranspiration);
        water_to_water_river,water_to_water_groundwater = self._split_water_between_river_and_ground(total_remaining_water)

        return {"m_Irr_wfldb_water_to_air": evapotranspiration,
                "m_Irr_wfldb_water_to_water_river": water_to_water_river,
                "m_Irr_wfldb_water_to_water_groundwater": water_to_water_groundwater
                }

    def _compute_irrigation_efficiency_ratio(self):
        return self._compute_surface_irrigation_ratio() + self._compute_sprinkler_irrigation_ratio() + self._compute_drip_irrigation_ratio();

    def _compute_surface_irrigation_ratio(self):
        return (self.irrigation_types_proportions[IrrigationType.surface_irrigation_diesel]
                + self.irrigation_types_proportions[IrrigationType.surface_irrigation_electricity]
                + self.irrigation_types_proportions[IrrigationType.surface_irrigation_no_energy]) * self._IRRIGATION_EFFICIENCY_FACTOR_SURFACE

    def _compute_sprinkler_irrigation_ratio(self):
        return (self.irrigation_types_proportions[IrrigationType.sprinkler_irrigation_electricity]
                + self.irrigation_types_proportions[IrrigationType.sprinkler_irrigation_diesel]) * self._IRRIGATION_EFFICIENCY_FACTOR_SPRINKLER

    def _compute_drip_irrigation_ratio(self):
        return (self.irrigation_types_proportions[IrrigationType.drip_irrigation_electricity]
                + self.irrigation_types_proportions[IrrigationType.drip_irrigation_diesel]) * self._IRRIGATION_EFFICIENCY_FACTOR_DRIP

    def _compute_evapotranspiration(self,irrigation_efficiency_ratio):
        return self.water_use_total * irrigation_efficiency_ratio;

    def _compute_remaining_water_after_evapotranspiration(self, evapotranspiration):
        return self.water_use_total - evapotranspiration;

    def _split_water_between_river_and_ground(self, total_remaining_water):
        river = 0.2 * total_remaining_water
        ground = 0.8 * total_remaining_water
        return (river,ground)

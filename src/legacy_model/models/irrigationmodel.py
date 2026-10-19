from enum import Enum

import dataloader

class IrrigationType(Enum):
    surface_irrigation_no_energy="surface_irrigation_no_energy"
    surface_irrigation_electricity="surface_irrigation_electricity"
    surface_irrigation_diesel="surface_irrigation_diesel"
    sprinkler_irrigation_electricity="sprinkler_irrigation_electricity"
    sprinkler_irrigation_diesel="sprinkler_irrigation_diesel"
    drip_irrigation_electricity="drip_irrigation_electricity"
    drip_irrigation_diesel="drip_irrigation_diesel"

# Irrigation technique of each type, as named in data/model_parameters.csv (irrigation_efficiency_*)
IRRIGATION_TECHNIQUE = {
    IrrigationType.surface_irrigation_no_energy: "surface",
    IrrigationType.surface_irrigation_electricity: "surface",
    IrrigationType.surface_irrigation_diesel: "surface",
    IrrigationType.sprinkler_irrigation_electricity: "sprinkler",
    IrrigationType.sprinkler_irrigation_diesel: "sprinkler",
    IrrigationType.drip_irrigation_electricity: "localized",
    IrrigationType.drip_irrigation_diesel: "localized",
}


def irrigation_efficiency(irrigation_types_proportions):
    """Average irrigation efficiency factor EFirr of the technique mix: sum of share x EFirr of the
    technique, WFLDB Guidelines v3.0 section 3.5.2 Tab. 3 (data/model_parameters.csv, decision L44)."""
    return sum(share * dataloader.param("irrigation_efficiency_" + IRRIGATION_TECHNIQUE[irrigation_type])
               for irrigation_type, share in irrigation_types_proportions.items())

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

    # legacy, undocumented, provisional: river / groundwater split

    def __init__(self, inputs):
        #TODO: Should we log usage of default value?
        for key in IrrigationModel._input_variables:
            setattr(self, key, inputs[key])

    def compute(self):
        irrigation_efficiency_ratio = irrigation_efficiency(self.irrigation_types_proportions)
        evapotranspiration = self._compute_evapotranspiration(irrigation_efficiency_ratio)
        total_remaining_water = self._compute_remaining_water_after_evapotranspiration(evapotranspiration);
        water_to_water_river,water_to_water_groundwater = self._split_water_between_river_and_ground(total_remaining_water)

        return {"m_Irr_wfldb_water_to_air": evapotranspiration,
                "m_Irr_wfldb_water_to_water_river": water_to_water_river,
                "m_Irr_wfldb_water_to_water_groundwater": water_to_water_groundwater
                }

    def _compute_evapotranspiration(self,irrigation_efficiency_ratio):
        return self.water_use_total * irrigation_efficiency_ratio;

    def _compute_remaining_water_after_evapotranspiration(self, evapotranspiration):
        return self.water_use_total - evapotranspiration;

    def _split_water_between_river_and_ground(self, total_remaining_water):
        river = 0.2 * total_remaining_water
        ground = 0.8 * total_remaining_water
        return (river,ground)

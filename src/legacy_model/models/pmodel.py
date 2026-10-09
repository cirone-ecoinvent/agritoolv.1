from enum import Enum

import dataloader
from models.atomicmass import P_TO_PO4_FACTOR


class LandUseCategory(Enum):
    arable_land='Arable land'
    fruit_trees='Fruit trees'
    grassland_intensive='Grassland intensive'
    grassland_extensive='Grassland extensive'
    summer_alpine_pastures='Summer alpine pastures'
    vegetables='Vegetables'
    viticulture='Viticulture'


class PModel(object):
    """Phosphorus emissions to water, SALCA-P (Prasuhn 2006) as in Quantis (2019) section 2.5,
    with the drainage and slope rules of SALCAfieldP (Nemecek et al. 2023, ESM5) - Fix F8.

    Inputs:
      crop_cycle_per_year: ratio (occupation period t = 1 / crop_cycle_per_year years)
      drained_part: ratio, share of the field with drainage (decision D5: template "drainage")
      eroded_soil: kg soil/(ha*year)
      known_slope_pct: % slope when known, None when unknown (run-off factor s = 1)
      land_use_category: LandUseCategory
      p2o5_in_liquid_manure: kg P2O5/(ha*crop cycle)
      p2o5_in_liquid_sludge: kg P2O5/(ha*crop cycle)
      p2O5_from_mineral_fert: kg P2O5/(ha*crop cycle)
      p2o5_in_solid_manure: kg P2O5/(ha*crop cycle)

    Outputs:
      m_P_PO4_groundwater: kg PO4/(ha*crop cycle)
      m_P_PO4_surfacewater_drained : kg PO4/(ha*crop cycle)
      m_P_PO4_surfacewater_ro: kg PO4/(ha*crop cycle)
      m_P_P_surfacewater_erosion: kg P/(ha*crop cycle)

    Parameters (data/): p_landuse_classes.csv (average yearly losses per land-use class),
    model_parameters.csv (fertilisation corrections, drainage factor, slope threshold, topsoil
    P content, enrichment factor, delivery ratio).
    """

    _input_variables = ["crop_cycle_per_year",
                        "drained_part",
                        "eroded_soil",
                        "known_slope_pct",
                        "land_use_category",
                        "p2o5_in_liquid_manure",
                        "p2o5_in_liquid_sludge",
                        "p2O5_from_mineral_fert",
                        "p2o5_in_solid_manure"
                       ]

    _LAND_USE_TABLE = "p_landuse_classes.csv"

    def __init__(self, inputs):
        #TODO: Should we log usage of default value?
        for key in PModel._input_variables:
            setattr(self, key, inputs[key])

    def compute(self):
        p2o5_liquid_sources = self._compute_p205_in_liquid_sources()
        phosphorus = self._compute_phosphorus_leach_in_ground_water(p2o5_liquid_sources)
        po4gw, po4swd = self._compute_and_split_phosphorus_to_ground_and_surface_waters_phosphates(phosphorus)
        po4swro = self._compute_phosphate_runoff_to_rivers(p2o5_liquid_sources)
        psw_erosion = self._compute_phosphorus_from_erosion_to_rivers()

        return {"m_P_PO4_groundwater": po4gw,
                "m_P_PO4_surfacewater_drained": po4swd,
                "m_P_PO4_surfacewater_ro": po4swro,
                "m_P_P_surfacewater_erosion": psw_erosion}

    def _duration_years(self):
        return 1.0 / self.crop_cycle_per_year

    def _average_loss(self, column):
        """Average yearly P loss [kg P/(ha*yr)] of the land-use class, scaled to the cycle."""
        row = dataloader.table(self._LAND_USE_TABLE)[self.land_use_category.value]
        return row[column] * self._duration_years()

    def _compute_p205_in_liquid_sources(self):
        return self.p2o5_in_liquid_manure + self.p2o5_in_liquid_sludge

    def _compute_phosphorus_leach_in_ground_water(self, p2o5_liquid_sources):
        """Pgw = Pgwl x t x (1 + 0.2/80 x P2O5 slurry) [kg P] (doc 2.5.1)."""
        correction_factor = 1 + dataloader.param("p_corr_slurry_leaching") * p2o5_liquid_sources
        return self._average_loss("p_leaching_kg_p_per_ha_yr") * correction_factor

    def _compute_and_split_phosphorus_to_ground_and_surface_waters_phosphates(self, phosphorus):
        """Leached phosphate: (1 - drained share) to ground water; on the drained share the
        leaching reaches surface water through the drains multiplied by kd = 6 (Prasuhn 2006,
        SALCAfieldP ESM5 Eq. 5). Same split as the legacy code, kd now from the CSV."""
        phosphate = phosphorus * P_TO_PO4_FACTOR
        ground = phosphate * (1 - self.drained_part)
        surface = phosphate * self.drained_part * dataloader.param("p_drainage_factor")
        return (ground, surface)

    def _compute_phosphate_runoff_to_rivers(self, p2o5_liquid_sources):
        """Pro = Prol x t x Fro x s [kg PO4] (doc 2.5.2; SALCAfieldP ESM5 Eq. 2).

        s = 0 when the slope is known and <= p_runoff_slope_threshold_pct (3 %), 1 otherwise
        (also when the slope is unknown). Fro = 1 + 0.2/80 P2O5min + 0.7/80 P2O5sl + 0.4/80 P2O5man.
        """
        if self.known_slope_pct is not None \
                and self.known_slope_pct <= dataloader.param("p_runoff_slope_threshold_pct"):
            return 0.0
        correction_factor = 1 + dataloader.param("p_corr_mineral_runoff") * self.p2O5_from_mineral_fert \
                              + dataloader.param("p_corr_slurry_runoff") * p2o5_liquid_sources \
                              + dataloader.param("p_corr_manure_runoff") * self.p2o5_in_solid_manure
        prunoff = self._average_loss("p_runoff_kg_p_per_ha_yr") * correction_factor
        return prunoff * P_TO_PO4_FACTOR

    def _compute_phosphorus_from_erosion_to_rivers(self):
        """Per = Ser x Pcs x Fr x Ferw [kg P] (doc 2.5.3); Ser is per year, scaled to the cycle."""
        return dataloader.param("p_topsoil_content") * dataloader.param("p_enrichment_factor") \
            * dataloader.param("erosion_delivery_ratio") * self.eroded_soil * self._duration_years()

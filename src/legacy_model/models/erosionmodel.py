from enum import Enum

import math

import dataloader


class TillageMethod(Enum):
    fall_plaw="fall_plaw"
    spring_plow="spring_plow"
    mulch_tillage="mulch_tillage"
    ridge_tillage="ridge_tillage"
    zone_tillage="zone_tillage"
    no_till="no_till"
    unknown="unknown"

class AntiErosionPractice(Enum):
    no_practice="no_practice"
    cross_slope="cross_slope"
    contour_farming="contour_farming"
    strip_cropping_cross_slope="strip_cropping_cross_slope"
    strip_cropping_contour="strip_cropping_contour"
    terraces="terraces"
    unknown="unknown"


def _tillage_factors():
    """C_tillage of Panagos et al. (2015a) Eq. 4a per tillage method (erosion_tillage_mapping.csv, decision L59)."""
    factors = {row["tillage_class"]: float(row["c_tillage"]) for row in dataloader.rows("panagos2015a_tillage_factors.csv")}
    return {TillageMethod(row["tillage_method"]): factors[row["panagos_tillage_class"]]
            for row in dataloader.rows("erosion_tillage_mapping.csv")}


def _practice_slope_classes():
    """P factor of USDA Agriculture Handbook 537, Tables 13-15, per practice (erosion_practice_mapping.csv, decision
    L59): list of (upper slope of the class in %, P) by increasing slope, None for the practices without a factor."""
    classes = {}
    for mapping in dataloader.rows("erosion_practice_mapping.csv"):
        practice = AntiErosionPractice(mapping["anti_erosion_practice"])
        if not mapping["ah537_table"]:
            classes[practice] = None
            continue
        classes[practice] = sorted((float(row["slope_max_pct"]), float(row["p_value"]))
                                   for row in dataloader.rows("ah537_p_factors.csv")
                                   if row["table"] == mapping["ah537_table"] and row["system"] == mapping["ah537_system"])
    return classes


class ErosionModel(object):
    """Inputs:
      rainfall_erosivity: MJ mm/(ha h year)
      slope: ratio
      slope_length: m
      tillage_method: TillageMethod
      anti_erosion_practice: AntiErosionPractice
      soil_erodibility_factor: t h/(MJ*mm)
      crop_factor: number

    Outputs:
      m_Erosion_eroded_soil: kg soil/(ha*year)
    """

    _input_variables = ["rainfall_erosivity",
                        "slope",
                        "slope_length",
                        "tillage_method",
                        "anti_erosion_practice",
                        "soil_erodibility_factor",
                        "crop_factor"
                        ]

    # legacy, undocumented, provisional: slope exponents below
    _POW_FOR_SLOPE_UNDER_1_PERCENT = 0.2
    _POW_FOR_SLOPE_1_TO_3_5_PERCENT = 0.3
    _POW_FOR_SLOPE_3_5_TO_5_PERCENT = 0.4
    _POW_FOR_SLOPE_OVER_5_PERCENT = 0.5

    _TILLAGE_METHOD_FACTOR = _tillage_factors()

    _PRACTICE_SLOPE_CLASSES = _practice_slope_classes()

    def __init__(self, inputs):
        #TODO: Should we log usage of default value?
        for key in ErosionModel._input_variables:
            setattr(self, key, inputs[key])

    def compute(self):
        erosivity_factor = self.rainfall_erosivity  # GloREDa, decision L60
        slope_factor = self._compute_slope_factor()
        tillage_factor = self._compute_tillage_factor()
        practice_factor = self._compute_practice_factor()
        eroded_soil = 1000.0 * erosivity_factor * self.soil_erodibility_factor \
                     * slope_factor * self.crop_factor * tillage_factor * practice_factor;
        return {"m_Erosion_eroded_soil": eroded_soil}

    def _compute_slope_factor(self):
        return (self.slope_length * 3.28083 / 72.6) ** self._compute_pow_for_slope_factor() * (
            65.41 * (math.sin(self.slope)) ** 2 \
            + 4.56 * (math.sin(self.slope)) + 0.065)

    def _compute_pow_for_slope_factor(self):
        if (self.slope < 0.01):
            return self._POW_FOR_SLOPE_UNDER_1_PERCENT
        elif (self.slope < 0.035):
            return self._POW_FOR_SLOPE_1_TO_3_5_PERCENT
        elif (self.slope < 0.05):
            return self._POW_FOR_SLOPE_3_5_TO_5_PERCENT
        else:
            return self._POW_FOR_SLOPE_OVER_5_PERCENT

    def _compute_tillage_factor(self):
        return self._TILLAGE_METHOD_FACTOR[self.tillage_method]

    def _compute_practice_factor(self):
        """AH 537 P of the slope class of the field (decision L59). The printed classes have gaps (1-2, 3-5 %, ...):
        a slope belongs to the first class whose upper limit it does not exceed, so 2.5 % is in 3-5 % and slopes under
        1 % in 1-2 %. Above the last class (25 %) the tables give no factor: P = 1."""
        classes = self._PRACTICE_SLOPE_CLASSES[self.anti_erosion_practice]
        if classes is None:
            return 1.0
        slope_pct = self.slope * 100.0
        for slope_max_pct, p_value in classes:
            if slope_pct <= slope_max_pct:
                return p_value
        return 1.0

from enum import Enum

import math


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
    unknown="unknown"


class ErosionModel(object):
    """Inputs:
      average_annual_precipitation: mm/year
      slope: ratio
      slope_length: m
      tillage_method: TillageMethod
      anti_erosion_practice: AntiErosionPractice
      soil_erodibility_factor: t h/(MJ*mm)
      crop_factor: number
      mean_elevation_m: m
      nb_wet_days_per_year: day/year
      climate_zone_specific: text

    Outputs:
      m_Erosion_eroded_soil: kg soil/(ha*year)
    """

    _input_variables = ["average_annual_precipitation",
                        "slope",
                        "slope_length",
                        "tillage_method",
                        "anti_erosion_practice",
                        "soil_erodibility_factor",
                        "crop_factor",
                        "mean_elevation_m",
                        "nb_wet_days_per_year",
                        "climate_zone_specific"
                        ]

    _POW_FOR_SLOPE_UNDER_1_PERCENT = 0.2
    _POW_FOR_SLOPE_1_TO_3_5_PERCENT = 0.3
    _POW_FOR_SLOPE_3_5_TO_5_PERCENT = 0.4
    _POW_FOR_SLOPE_OVER_5_PERCENT = 0.5

    _TILLAGE_METHOD_FACTOR = {TillageMethod.unknown:1.0,
                              TillageMethod.fall_plaw: 1.0,
                              TillageMethod.spring_plow: 0.9,
                              TillageMethod.mulch_tillage: 0.6,
                              TillageMethod.ridge_tillage: 0.35,
                              TillageMethod.zone_tillage: 0.25,
                              TillageMethod.no_till: 0.25}

    _ANTI_EROSION_PRACTICE_FACTOR = {AntiErosionPractice.unknown: 1,
                                     AntiErosionPractice.no_practice: 1,
                                     AntiErosionPractice.cross_slope: 0.75,
                                     AntiErosionPractice.contour_farming: 0.5,
                                     AntiErosionPractice.strip_cropping_cross_slope: 0.37,
                                     AntiErosionPractice.strip_cropping_contour: 0.25}

    _USUAL_EQUATION = lambda p, e, s: -3172.0 + 7.562 * p

    _EROSITIVITY_FACTOR_FORMULAE = {"polar_frost": lambda p, e, s: 10 ** (-10.66 + 2.43 * math.log10(p)),
                                    "polar_tundra": lambda p, e, s: 10 ** (-10.66 + 2.43 * math.log10(p)),
                                    "snow_winter_continental": lambda p, e, s: 10 ** (1.882 + 0.819 * math.log10(p)),
                                    "snow_humid_continental": lambda p, e, s: 10 ** (-1.259 + 3.862 * math.log10(s)),
                                    "snow_summer_continental": lambda p, e, s: 10 ** (4.416 + 0.0594 * math.log10(p)),
                                    "arid_desert_cold": lambda p, e, s: 0.809 * (p ** 0.957) + 0.000189 * (s ** 6.285),
                                    "warm_humid_hot": lambda p, e, s:
                                    10 ** (0.524 + 0.462 * math.log10(p) + 1.97 * math.log10(s)
                                           - 0.106 * math.log10(e)),
                                    "warm_humid_warm": lambda p, e, s:
                                    10 ** (-7.694 + 4.1407 * math.log10(p) - 2.586 * math.log10(s)),
                                    "warm_humid_cold": lambda p, e, s:
                                    10 ** (-7.694 + 4.1407 * math.log10(p) - 2.586 * math.log10(s)),
                                    "warm_summer_dry_hot": lambda p, e, s: -944.0 + 3.08 * p,
                                    "warm_summer_dry_warm": lambda p, e, s: 98.35 + 0.000355 * (p ** 1.987),
                                    "warm_summer_dry_cold": lambda p, e, s: -944.0 + 3.08 * p,
                                    "warm_winter_dry_hot": _USUAL_EQUATION,
                                    "warm_winter_dry_cool": _USUAL_EQUATION,
                                    "warm_winter_dry_cold": _USUAL_EQUATION,
                                    "snow_humid_hot": lambda p, e, s:
                                    10 ** (-1.99 + 0.737 * math.log10(p) + 2.033 * math.log10(s)),
                                    "snow_humid_warm": lambda p, e, s:
                                    10 ** (-0.5 + 0.266 * math.log10(p) + 3.1 * math.log10(s) - 0.131 * math.log10(e)),
                                    "snow_humid_cold": lambda p, e, s: 10 ** (-1.259 + 3.862 * math.log10(s)),
                                    "snow_summer_dry_hot": lambda p, e, s: 10 ** (1.882 + 0.819 * math.log10(p)),
                                    "snow_summer_dry_warm": lambda p, e, s: 10 ** (2.166 + 0.494 * math.log10(p)),
                                    "snow_summer_dry_cold": lambda p, e, s: 10 ** (4.416 + 0.0594 * math.log10(p)),
                                    "snow_winter_dry_hot": lambda p, e, s: 38.5 + 0.35 * p,
                                    "snow_winter_dry_warm": lambda p, e, s: 38.5 + 0.35 * p,
                                    "snow_winter_dry_cold": lambda p, e, s: 10 ** (1.882 + 0.819 * math.log10(p)),
                                    "arid_steppe_cold": lambda p, e, s:
                                    10 ** (0.0793 + 0.887 * math.log10(p) + 1.892 * math.log10(s)
                                           - 0.429 * math.log10(e)),
                                    "equatorial_humid": _USUAL_EQUATION,
                                    "equatorial_monsonnal": _USUAL_EQUATION,
                                    "equatorial_summer_dry": lambda p, e, s: -669.3 + 7 * p - 2.719 * e,
                                    "equatorial_winter_dry": _USUAL_EQUATION,
                                    "arid_steppe_hot": lambda p, e, s:
                                    10 ** (-7.72 + 1.595 * math.log10(p) + 2.068 * math.log10(s)),
                                    "arid_desert_hot": lambda p, e, s: 0.0438 * (p ** 1.61)}

    def __init__(self, inputs):
        #TODO: Should we log usage of default value?
        for key in ErosionModel._input_variables:
            setattr(self, key, inputs[key])

    def compute(self):
        erosivity_factor = self._compute_erosivity_factor()
        slope_factor = self._compute_slope_factor()
        tillage_factor = self._compute_tillage_factor()
        practice_factor = self._compute_practice_factor()
        eroded_soil = 1000.0 * erosivity_factor * self.soil_erodibility_factor \
                     * slope_factor * self.crop_factor * tillage_factor * practice_factor;
        return {"m_Erosion_eroded_soil": eroded_soil}

    def _compute_erosivity_factor(self):#MJ mm/(ha*h*yr)
        return self._EROSITIVITY_FACTOR_FORMULAE[self.climate_zone_specific] \
            (self.average_annual_precipitation,
             self.mean_elevation_m,
             self.average_annual_precipitation / self.nb_wet_days_per_year)

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
        return self._ANTI_EROSION_PRACTICE_FACTOR[self.anti_erosion_practice]

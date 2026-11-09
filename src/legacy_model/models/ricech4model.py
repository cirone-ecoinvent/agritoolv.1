"""Methane of flooded rice, IPCC 2019 Refinement Tier 1 (decision L66, issue #47).

IPCC (2019) 2019 Refinement to the 2006 IPCC Guidelines for National Greenhouse Gas Inventories, Vol. 4 ch. 5.5
(docs/methodology/19R_V4_Ch05_Cropland.pdf); factors in data/ipcc2019_rice_ch4_factors.csv.

    CH4 [kg CH4/(ha and crop cycle)] = EF_i x t                       (Eq. 5.1 per ha, p. 5.49)
    EF_i = EF_c x SF_w x SF_p x SF_o                                  (Eq. 5.2 (Updated), p. 5.51)
    SF_o = (1 + sum_i ROA_i x CFOA_i)^0.59                            (Eq. 5.3, p. 5.55)

EF_c (Table 5.11) and the default cultivation period t (Table 5.11A) are those of the IPCC rice region of the country
(ipcc2019_rice_region_mapping.csv over the M49 chain country, sub-region, region of olcapestmodel.m49_chain; World
when no row applies). t can be given as rice_cultivation_period_days; it is never derived from crop_cycle_duration,
which runs from harvest to harvest.

SF_w (Table 5.12): disaggregated factor of rice_water_regime; when the regime is not given, the aggregated factor of
irrigated rice (irrigated = yes) or of rainfed and deep-water rice (irrigated = no). Upland rice: SF_w = 0, no CH4.
SF_p (Table 5.13): disaggregated factor of rice_preseason_water_regime; when not given, the aggregated 1.22.
SF_o: the organic inputs of the tool mapped to a class of Table 5.14 in ipcc2019_rice_organic_amendment_mapping.csv
(solid manures and dried poultry manure as farm yard manure, compost as compost), kg fresh matter / 1000 = t/ha;
inputs mapped to 'none' are not counted. Default amounts (manure defaults L29, L40, L42) count like given amounts.

Only flooded crops (column 'flooded' of crop_types.csv: rice) have the output ch4_rice_air.
"""
import dataloader
from models.olcapestmodel import m49_chain

FACTORS_TABLE = "ipcc2019_rice_ch4_factors.csv"
REGION_MAPPING = "ipcc2019_rice_region_mapping.csv"
AMENDMENT_MAPPING = "ipcc2019_rice_organic_amendment_mapping.csv"
WORLD = "World"
NOT_GIVEN = (None, "", "N/A")
AGGREGATED, DISAGGREGATED = "aggregated", "disaggregated_"


def factor(parameter, case):
    """Value of a row of ipcc2019_rice_ch4_factors.csv."""
    for row in dataloader.rows(FACTORS_TABLE):
        if row["parameter"] == parameter and row["case"] == case:
            return float(row["value"])
    raise KeyError("No %s / %s row in %s" % (parameter, case, FACTORS_TABLE))


def _cases(parameter):
    """Regimes of the disaggregated case of a scaling factor (Tables 5.12 and 5.13)."""
    return [row["case"][len(DISAGGREGATED):] for row in dataloader.rows(FACTORS_TABLE)
            if row["parameter"] == parameter and row["case"].startswith(DISAGGREGATED)]


def _regime(value, parameter, input_name):
    if value in NOT_GIVEN:
        return None
    if value not in _cases(parameter):
        raise ValueError("%s must be one of %s or N/A, got %r" % (input_name, ", ".join(_cases(parameter)), value))
    return value


def water_regime(value):
    """rice_water_regime as a case of Table 5.12, or None when not given (N/A)."""
    return _regime(value, "sf_w", "rice_water_regime")


def preseason_water_regime(value):
    """rice_preseason_water_regime as a case of Table 5.13, or None when not given (N/A)."""
    return _regime(value, "sf_p", "rice_preseason_water_regime")


def rice_region(country):
    """IPCC rice region of Tables 5.11 and 5.11A: first row of the region mapping on the M49 chain, else World."""
    regions = dataloader.table(REGION_MAPPING, "m49_code", numeric=False)
    for code in m49_chain(country):
        if code in regions:
            return regions[code]["rice_region"]
    return WORLD


def sf_w(regime, irrigated):
    if regime is not None:
        return factor("sf_w", DISAGGREGATED + regime)
    if irrigated not in ("yes", "no"):
        raise ValueError("irrigated must be 'yes' or 'no', got %r" % (irrigated,))
    return factor("sf_w", "aggregated_irrigated" if irrigated == "yes" else "aggregated_rainfed")


def sf_p(regime):
    return factor("sf_p", AGGREGATED if regime is None else DISAGGREGATED + regime)


def sf_o(amounts):
    """SF_o of Eq. 5.3 from {tool variable: kg fresh matter/ha}; every variable must be in the mapping."""
    mapping = dataloader.table(AMENDMENT_MAPPING, "tool_variable", numeric=False)
    total = 0.0
    for variable, kg in amounts.items():
        if variable not in mapping:
            raise KeyError("Organic input '%s' is not in %s" % (variable, AMENDMENT_MAPPING))
        cfoa_class = mapping[variable]["cfoa_class"]
        if cfoa_class != "none":
            total += kg / 1000.0 * factor("cfoa", cfoa_class)
    return (1.0 + total) ** factor("sf_o_exponent", "none")


def cultivation_period(days, region):
    if days in NOT_GIVEN:
        return factor("cultivation_period", region)
    days = float(days)
    if not days > 0.0:
        raise ValueError("rice_cultivation_period_days must be > 0, got %r" % (days,))
    return days


def is_flooded(crop):
    return dataloader.table("crop_types.csv", numeric=False)[crop]["flooded"] == "yes"


class RiceCh4Model(object):
    """Inputs:
      crop, country
      irrigated: "yes" / "no" (default: yes when water_use_total > 0, as for the land use flows)
      rice_water_regime, rice_preseason_water_regime: case of Table 5.12 / 5.13 or None (N/A)
      rice_cultivation_period_days: days or None (N/A)
      solid_manure_quantities, liquid_manure_quantities, compost_quantities, sludge_quantities: maps of the organic
      inputs (enum -> amount per ha and crop cycle); only those mapped to a Table 5.14 class are counted

    Output: {'ch4_rice_air': kg CH4/(ha and crop cycle)} for flooded crops, {} for the other crops.
    """

    _input_variables = ["crop", "country", "irrigated", "rice_water_regime", "rice_preseason_water_regime",
                        "rice_cultivation_period_days", "solid_manure_quantities", "liquid_manure_quantities",
                        "compost_quantities", "sludge_quantities"]

    def __init__(self, inputs):
        for key in RiceCh4Model._input_variables:
            setattr(self, key, inputs[key])

    def amendments(self):
        """{tool variable: amount per ha and crop cycle} of all organic inputs."""
        out = {}
        for quantities in (self.solid_manure_quantities, self.liquid_manure_quantities, self.compost_quantities,
                           self.sludge_quantities):
            for kind, amount in quantities.items():
                out[kind.value] = amount
        return out

    def factors(self):
        """EF_c, SF_w, SF_p, SF_o, t and the region of the case."""
        region = rice_region(self.country)
        return {"region": region,
                "ef_c": factor("ef_c", region),
                "sf_w": sf_w(water_regime(self.rice_water_regime), self.irrigated),
                "sf_p": sf_p(preseason_water_regime(self.rice_preseason_water_regime)),
                "sf_o": sf_o(self.amendments()),
                "t": cultivation_period(self.rice_cultivation_period_days, region)}

    def ch4(self):
        """kg CH4/(ha and crop cycle); 0 for crops that are not flooded."""
        if not is_flooded(self.crop):
            return 0.0
        f = self.factors()
        return f["ef_c"] * f["sf_w"] * f["sf_p"] * f["sf_o"] * f["t"]

    def compute(self):
        return {"ch4_rice_air": self.ch4()} if is_flooded(self.crop) else {}

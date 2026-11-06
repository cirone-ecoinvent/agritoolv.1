"""Emissions of the pesticide active ingredients with the OLCA-Pest default fractions (decision L65).

Nemecek T. et al. (2022) Operationalising emission and toxicity modelling of pesticides in LCA: the OLCA-Pest project
contribution, Int J LCA 27:527-542 (Table 2, section 3.4), as implemented in the OLCApest mapping tool supplied by FC
(data/external_data/OLCApest mapping tool_AG_updated.xlsx, sheet 'calculation pathway' step 8 and sheet OLCA CALC).

For each active ingredient with the applied amount m, scenario = OLCA-Pest crop archetype of the crop
(pesticide_crop_archetype_mapping.csv) x OLCA-Pest class of the active ingredient (olca_pest_pesticide_class.csv);
the fractions are the primary distribution without buffer zone (olca_pest_default_fractions.csv). A class without a
scenario for the archetype takes the substitute class of olca_pest_scenario_substitution.csv (tree archetypes:
Hrb-pre and Hrb-Avg -> Hrb-post).

    air, non-urban air or from high stacks = f_air x m
    soil, agricultural                    = (f_soil + f_crop + f_off_field x agri) x m
    soil, forestry                        = f_off_field x forest x m
    water, surface water                  = f_off_field x water x m

The crop deposit is added to agricultural soil (step 8 of the tool; Master Data 3.12 has no crop compartment). The
off-field part is split with the shares of agricultural land, forest land and inland waters of the dataset country
(faostat_country_land_shares.csv, FAOSTAT Land Use, redistributed as in the tool); a country without shares takes those
of its M49 sub-region, then region, then the World. The four parts sum to m (to the 1e-9 rounding of the fractions).

Active ingredients ending with '_other' or '_unspecified' are not substances: no emission, as in the legacy writer.
Horticultural oil (Mineral oil) is not a 'part_*' key and keeps its legacy emission (100 % to agricultural soil).
"""
import dataloader

ARCHETYPE_MAPPING = "pesticide_crop_archetype_mapping.csv"
FRACTIONS_TABLE = "olca_pest_default_fractions.csv"
SUBSTITUTION_TABLE = "olca_pest_scenario_substitution.csv"
CLASS_TABLE = "olca_pest_pesticide_class.csv"
LAND_SHARES_TABLE = "faostat_country_land_shares.csv"
COUNTRY_MAPPING = "faostat_country_mapping.csv"
WORLD_M49 = "001"
NOT_A_SUBSTANCE = ("_other", "_unspecified")

# Output key prefix of each compartment (amounts in kg); the Master Data flows are in elementary_flow_alignment.csv.
COMPARTMENT_PREFIXES = {"air": "pestiair_", "soil_agricultural": "pestisoil_", "soil_forestry": "pestiforestry_",
                        "water_surface": "pestiwater_"}


def crop_archetype(crop):
    archetypes = dataloader.table(ARCHETYPE_MAPPING, numeric=False)
    if crop not in archetypes:
        raise KeyError("Crop '%s' is not in %s" % (crop, ARCHETYPE_MAPPING))
    return archetypes[crop]["olca_crop_archetype"]


def scenario(crop, pest_class):
    """OLCA-Pest fractions {scenario_id, crop_archetype, pest_class, f_air, f_soil, f_crop, f_off_field} of a crop
    and a pest class; the class is replaced by its substitute when the archetype has no scenario for it."""
    archetype = crop_archetype(crop)
    for row in dataloader.rows(SUBSTITUTION_TABLE):
        if row["crop_archetype"] == archetype and row["pest_class"] == pest_class:
            pest_class = row["substitute_pest_class"]
    for row in dataloader.rows(FRACTIONS_TABLE):
        if row["crop_archetype"] == archetype and row["pest_class"] == pest_class:
            out = {k: float(row[k]) for k in ("f_air", "f_soil", "f_crop", "f_off_field")}
            out.update(scenario_id=row["scenario_id"], crop_archetype=archetype, pest_class=pest_class)
            return out
    raise KeyError("No %s / %s row in %s" % (archetype, pest_class, FRACTIONS_TABLE))


def land_shares(country):
    """{agri, forest, water, m49_code, area} for a tool country: the FAOSTAT area of its M49 code, else the first of
    its sub-region, region and the World that has shares."""
    mapping = dataloader.table(COUNTRY_MAPPING, numeric=False)
    if country not in mapping:
        raise KeyError("Country '%s' is not in %s" % (country, COUNTRY_MAPPING))
    areas = {row["m49_code"]: row for row in dataloader.rows(LAND_SHARES_TABLE)}
    row = areas.get(mapping[country]["m49_code"])
    chain = [row, areas.get(row["subregion_m49"]), areas.get(row["region_m49"])] if row else []
    for area in chain + [areas[WORLD_M49]]:
        if area and area["agri_share"]:
            return {"agri": float(area["agri_share"]), "forest": float(area["forest_share"]),
                    "water": float(area["water_share"]), "m49_code": area["m49_code"], "area": area["area"]}
    raise KeyError("No land shares for '%s' in %s" % (country, LAND_SHARES_TABLE))


def split(grams, fractions, shares):
    """Emissions [same unit as grams] per compartment of one active ingredient."""
    off_field = fractions["f_off_field"] * grams
    return {"air": fractions["f_air"] * grams,
            "soil_agricultural": (fractions["f_soil"] + fractions["f_crop"]) * grams + off_field * shares["agri"],
            "soil_forestry": off_field * shares["forest"],
            "water_surface": off_field * shares["water"]}


class OlcaPestModel(object):
    """Inputs: specified_pesticides {'part_<herbicides|fungicides|insecticides>_<name>': g a.i./(ha*crop cycle)},
    crop, country.
    Output: {'pesti_<category>_<name>': {compartment: kg/(ha*crop cycle)}} for the compartments of
    COMPARTMENT_PREFIXES."""

    _input_variables = ["specified_pesticides", "crop", "country"]

    def __init__(self, inputs):
        for key in OlcaPestModel._input_variables:
            setattr(self, key, inputs[key])

    def compute(self):
        classes = dataloader.table(CLASS_TABLE, numeric=False)
        shares = land_shares(self.country)
        result = {}
        for key, grams in self.specified_pesticides.items():
            variable = key.replace("part_", "pesti_", 1)
            if variable.endswith(NOT_A_SUBSTANCE):
                continue
            if variable not in classes:
                raise KeyError("Pesticide '%s' is not in %s" % (variable, CLASS_TABLE))
            fractions = scenario(self.crop, classes[variable]["olca_pest_class"])
            result[variable] = split(grams / 1000.0, fractions, shares)
        return result

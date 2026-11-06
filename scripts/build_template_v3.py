"""Build the data-collection template v3 (docs/template_v3_spec.md, branch template/v3-design).

DRAFT for review: the lists marked DRAFT in the Lists sheet do not come from data/ yet (field
operations from the agri-lca-pipeline table, units, energy, materials, wastes, fertiliser labels).
Usage: python scripts/build_template_v3.py <repo> <unsd_csv> <pipeline_config_py> <out.xlsx>
"""
import ast
import csv
import datetime
import re
import sys

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation

REPO, UNSD, PIPE_CFG, OUT = sys.argv[1:5]
FONT = "Arial"
EXAMPLE_ID = "EXAMPLE-wheat-IT"
FIRST_DATA_ROW = 7
N_ROWS = {"Datasets": 50, "Coproducts": 100, "Fertilisers": 300, "Pesticides": 300,
          "Operations": 300, "Energy_water": 200, "Materials": 100, "Wastes": 100, "Sources": 50}

FILL = {"R": PatternFill("solid", fgColor="F4B6B6"), "E": PatternFill("solid", fgColor="FBD89A"),
        "O": PatternFill("solid", fgColor="C6E5C1"), "G": PatternFill("solid", fgColor="BFD7EE"),
        "T": PatternFill("solid", fgColor="E7E6E6")}
INPUT_FILL = PatternFill("solid", fgColor="FFFDE7")
EXAMPLE_FONT = Font(name=FONT, italic=True, color="7F7F7F", size=10)
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def read_csv(path, **kw):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, **kw))


# ---------------------------------------------------------------- lists
lists = {}  # name -> (values, source)
crops = [r["crop"] for r in read_csv(f"{REPO}/data/crop_types.csv")]
lists["crop"] = (crops, "data/crop_types.csv")
countries = sorted(r["Country or Area"] for r in read_csv(UNSD, delimiter=";") if r["ISO-alpha3 Code"])
lists["country"] = (countries, "data/external_data/UNSD — Methodology.csv (M49 countries and areas; to become a table of data/)")
lists["production_system"] = (["open ground", "greenhouse soil heated", "greenhouse soil unheated",
                               "greenhouse hydroponic heated", "greenhouse hydroponic unheated"],
                              "spec 5.1 (legacy cultivation_type)")
lists["yes_no"] = (["yes", "no"], "spec 5.1")
lists["na_zero"] = (["N/A", "0"], "spec section 4 (input-group columns, P3)")
lists["water_unit"] = (["m3/ha", "mm"], "spec 5.12 (T5)")
tillage_label = {"fall_plaw": "fall plough", "spring_plow": "spring plough", "mulch_tillage": "mulch tillage",
                 "ridge_tillage": "ridge tillage", "zone_tillage": "zone tillage", "no_till": "no till",
                 "unknown": "unknown"}
lists["tillage"] = ([tillage_label[r["tillage_method"]] for r in read_csv(f"{REPO}/data/erosion_tillage_mapping.csv")
                     if r["tillage_method"] != "unknown"] + ["unknown"], "data/erosion_tillage_mapping.csv (L59)")
practice_label = {"no_practice": "no practice", "contour_farming": "contour farming",
                  "strip_cropping_contour": "strip cropping on the contour", "terraces": "terraces", "unknown": "unknown"}
lists["anti_erosion_practice"] = ([practice_label[r["anti_erosion_practice"]]
                                   for r in read_csv(f"{REPO}/data/erosion_practice_mapping.csv")
                                   if r["anti_erosion_practice"] in practice_label and r["anti_erosion_practice"] != "unknown"]
                                  + ["unknown"], "data/erosion_practice_mapping.csv without the cross-slope practices (L62)")
lists["fate"] = (["removed", "left on field", "burned"], "spec 5.2 (T11; burned = error until a burning model exists)")

fert_items = (
    ["urea", "ammonium nitrate", "calcium ammonium nitrate", "ammonium sulphate", "urea ammonium nitrate (UAN)",
     "mono-ammonium phosphate (MAP)", "di-ammonium phosphate (DAP)", "ammonium nitrate phosphate (ANP)",
     "potassium nitrate", "triple superphosphate (TSP)", "single superphosphate (SSP)", "potassium chloride (KCl)",
     "potassium sulphate (K2SO4)", "raw phosphate", "basic slag", "patent potassium", "liquid ammonia",
     "mineral N total (products unknown)", "mineral P2O5 total (products unknown)", "mineral K2O total (products unknown)",
     "limestone", "carbonation lime", "seaweed lime", "dolomite", "Mg fertiliser", "zinc sulfate", "zinc oxide",
     "other Zn fertiliser", "borax", "gypsum", "kaolin", "manganese sulfate", "portafer", "sulfite",
     "liquid manure, cattle", "liquid manure, pig", "liquid manure, laying hens", "liquid manure, other",
     "solid manure, cattle", "solid manure, pig", "solid manure, sheep and goats", "solid manure, laying hens",
     "solid manure, horses", "solid manure, other"]
    + [r["fertiliser_type"].replace("composttype_", "").replace("sewagesludge_", "sewage sludge, ").replace("_", " ")
       for r in read_csv(f"{REPO}/data/organic_fertiliser_composition.csv")])
lists["fertiliser_item"] = (fert_items, "spec 5.3; organic types from data/organic_fertiliser_composition.csv; "
                            "mineral products of data/fertiliser_product_basis.csv (labels DRAFT)")
lists["fertiliser_unit"] = (["kg product", "kg N", "kg P2O5", "kg K2O", "kg CaO", "kg Mg", "kg Zn", "m3", "t FM"],
                            "DRAFT (unit table of data/ to be built, P4)")

pest = sorted({r["md312_name"] for r in read_csv(f"{REPO}/data/elementary_flow_alignment.csv")
               if r["model_variable"].startswith("pesti_")}, key=str.lower)
lists["active_ingredient"] = (pest + ["other herbicide", "other fungicide", "other insecticide", "horticultural oil"],
                              "data/elementary_flow_alignment.csv, pesticide rows (Master Data 3.12 names)")
lists["pesticide_unit"] = (["g a.i.", "kg (horticultural oil)"], "spec 5.4")

src = open(PIPE_CFG, encoding="utf-8").read()
m = re.search(r"^FO_DIESEL_INTENSITIES[^=\n]*=\s*", src, re.M)
i = m.end(); depth = 0
for j in range(i, len(src)):
    if src[j] == "{": depth += 1
    elif src[j] == "}":
        depth -= 1
        if depth == 0: break
ops = sorted({k[0] for k in ast.literal_eval(src[i:j + 1])})
lists["operation"] = (ops + ["total diesel (operations without own diesel)", "other operation"],
                      "DRAFT: FO_DIESEL_INTENSITIES of the agri-lca-pipeline (config_new_datasets.py), not yet in data/")
lists["diesel_unit"] = (["l/ha", "kg/ha"], "spec 5.5")

energy = ["electricity, grid", "electricity, on-site photovoltaic", "electricity, on-site wind",
          "diesel, stationary (not tractors)", "petrol", "light fuel oil", "heavy fuel oil", "natural gas",
          "lignite briquettes", "hard coal briquettes", "wood pellets", "wood chips", "wood logs",
          "heat, district", "heat, solar collector",
          "irrigation water source, groundwater", "irrigation water source, surface water", "irrigation water source, other",
          "other water, groundwater", "other water, surface water", "other water, other source"]
lists["energy_item"] = (energy, "DRAFT from spec 5.6")
lists["energy_unit"] = (["kWh", "MJ", "kg", "Nm3", "m3", "%"], "DRAFT (unit table)")
lists["material_item"] = (["fleece", "silage foil", "covering sheet", "bird net", "greenhouse, glass",
                           "greenhouse, plastic", "plastic tunnel", "trellis"], "DRAFT from spec 5.7")
lists["material_unit"] = (["kg", "m2 soil covered", "yes/no/unknown"], "DRAFT (unit table)")
lists["waste_item"] = (["plastic waste", "plastic waste, share to landfill", "plastic waste, share to incineration",
                        "biowaste", "biowaste, share to anaerobic digestion", "biowaste, share to composting",
                        "biowaste, share to incineration", "biowaste, share other", "wastewater to treatment",
                        "wastewater to nature", "COD of wastewater"], "DRAFT from spec 5.8")
lists["waste_unit"] = (["kg", "%", "m3", "mg/l"], "DRAFT (unit table)")
lists["data_source"] = (["field", "statistical", "literature"], "spec 5.9 (facts of the meta model)")

# ---------------------------------------------------------------- sheet definitions
# (key, unit, status, list, help)
GROUPS = [("grp_mineral_fertilisers", "Mineral fertilisers"), ("grp_manure", "Manure"),
          ("grp_compost_sludge", "Compost and sewage sludge"), ("grp_lime_micronutrients", "Lime and micronutrients"),
          ("grp_pesticides", "Pesticides"), ("grp_operations", "Field operations"), ("grp_other_energy", "Other energy"),
          ("grp_materials", "Materials"), ("grp_wastes", "Wastes")]
SHEETS = {
    "Datasets": [
        ("dataset_id", "text", "R", None, "Your identifier of the dataset, unique in the workbook. Used in all other sheets."),
        ("crop", "list", "R", "crop", "Crop of the dataset."),
        ("country", "list", "R", "country", "UN M49 country or area. Defaults fall back to region and World (T1)."),
        ("region", "text", "O", None, "Sub-national region, for documentation only."),
        ("period_start", "year", "R", None, "First year of the data."),
        ("period_end", "year", "R", None, "Last year of the data."),
        ("production_system", "list", "R", "production_system", "Open ground or greenhouse type."),
        ("organic", "yes/no", "R", "yes_no", "Certified organic production."),
        ("crop_cycle_duration", "months", "O", None, "Months from the harvest of the previous crop to the harvest of this crop. N/A = 12 (T4)."),
        ("yield_main_product", "kg FM/(ha and crop cycle)", "E", None, "Fresh-matter yield. N/A = FAOSTAT default, with warning; checked against +/- 10 % (T2)."),
        ("irrigated", "yes/no", "R", "yes_no", "Yes: the three irrigation fields are required (T5)."),
        ("irrigation_water", "per crop cycle", "R*", None, "Required if irrigated = yes; 0 or N/A if no."),
        ("irrigation_water_unit", "list", "R*", "water_unit", "m3/ha or mm (1 mm = 10 m3/ha)."),
        ("irrigation_share_surface", "% of irrigation water", "R*", None, "Shares of the three techniques sum to 100 %."),
        ("irrigation_share_sprinkler", "% of irrigation water", "R*", None, ""),
        ("irrigation_share_drip", "% of irrigation water", "R*", None, ""),
        ("drained_share", "% of area", "O", None, "N/A = 0 (L5)."),
        ("tillage", "list", "O", "tillage", "N/A or unknown = conventional tillage (L59)."),
        ("anti_erosion_practice", "list", "O", "anti_erosion_practice", "N/A or unknown = P of Panagos 2015b in the EU, 1 elsewhere (L62)."),
        ("slope", "%", "O", None, "Mean field slope. N/A = 3 % (flooded rice 0 %)."),
        ("plantation_lifetime", "years", "O", None, "Perennial crops only. N/A = ecoinvent 3.12 lifetime (L50)."),
        ("planting_density", "kg seed, seedlings or trees per ha", "O", None, "Unit follows the crop type. N/A = default (L46, L47)."),
        ("annual_precipitation", "mm/yr", "O", None, "N/A = TerraClimate 1991-2020 over the crop area (L61)."),
        ("rainfall_erosivity", "MJ mm/(ha h yr)", "O", None, "N/A = GloREDa over the crop area (L60)."),
        ("soil_clay", "% of fine earth, 0-20 cm", "O", None, "N/A = HWSD v2.0 (L63)."),
        ("soil_organic_carbon", "%, mean of 0-50 cm", "O", None, "N/A = HWSD v2.0 (L63)."),
        ("soil_ph", "pH in water, topsoil", "O", None, "N/A = HWSD v2.0 share of soils with pH <= 7 (L63)."),
    ] + [(k, "N/A or 0", "G", "na_zero", f"{label}: N/A = use the rows of the group (or the defaults if there are none); 0 = group not used.")
         for k, label in GROUPS],
    "Coproducts": [
        ("dataset_id", "text", "R", None, "As in Datasets."),
        ("coproduct", "text (list DRAFT)", "R", None, "Co-product, e.g. straw. The list of Master Data products is still to be built."),
        ("amount", "kg FM/(ha and crop cycle)", "R", None, ""),
        ("fate", "list", "R", "fate", "removed = product of the dataset; left on field; burned = not supported yet (error) (T11)."),
        ("comment", "text", "O", None, ""),
    ],
    "Fertilisers": [
        ("dataset_id", "text", "R", None, "As in Datasets. One row per product."),
        ("item", "list", "R", "fertiliser_item", "Product, nutrient total, lime or micronutrient, manure, compost or sewage sludge."),
        ("amount", "per ha and crop cycle", "R", None, "N/A only where the item has its own default."),
        ("unit", "list", "R", "fertiliser_unit", "kg product, kg N, kg P2O5, kg K2O; manure in m3 (liquid) or t FM (solid)."),
        ("liquid_manure_dilution", "share undiluted", "O", None, "Liquid manure only. N/A = 0.5 (legacy)."),
        ("comment", "text", "O", None, ""),
    ],
    "Pesticides": [
        ("dataset_id", "text", "R", None, "As in Datasets. One row per active ingredient."),
        ("active_ingredient", "list", "R", "active_ingredient", "Unlisted ingredient: 'other herbicide / fungicide / insecticide' and the name in comment."),
        ("amount", "per ha and crop cycle", "R", None, ""),
        ("unit", "list", "R", "pesticide_unit", "g of active ingredient; horticultural oil in kg."),
        ("comment", "text", "O", None, ""),
    ],
    "Operations": [
        ("dataset_id", "text", "R", None, "As in Datasets. One row per field operation."),
        ("operation", "list", "R", "operation", "ecoinvent field operation. 'total diesel' = diesel of the operations without their own diesel (T6)."),
        ("passes", "number per crop cycle", "O", None, "N/A = diesel / intensity of the operation. Passes and diesel both N/A = error."),
        ("diesel", "per ha and crop cycle", "O", None, "N/A = intensity of the operation x passes."),
        ("diesel_unit", "list", "O", "diesel_unit", "l/ha or kg/ha."),
        ("comment", "text", "O", None, ""),
    ],
    "Energy_water": [
        ("dataset_id", "text", "R", None, "As in Datasets. Irrigation amount and techniques are in Datasets."),
        ("item", "list", "R", "energy_item", "Energy carrier, irrigation water source share or other water."),
        ("amount", "per ha and crop cycle", "R", None, ""),
        ("unit", "list", "R", "energy_unit", ""),
        ("comment", "text", "O", None, ""),
    ],
    "Materials": [
        ("dataset_id", "text", "R", None, "As in Datasets."),
        ("item", "list", "R", "material_item", "Plastics in kg; greenhouse and tunnel in m2 of soil covered (L51); trellis yes/no/unknown."),
        ("amount", "per ha and crop cycle", "R", None, ""),
        ("unit", "list", "R", "material_unit", ""),
        ("comment", "text", "O", None, ""),
    ],
    "Wastes": [
        ("dataset_id", "text", "R", None, "As in Datasets."),
        ("item", "list", "R", "waste_item", "Plastic waste and its shares (N/A = 50/50), biowaste and its fate shares, wastewater, COD."),
        ("amount", "per ha and crop cycle", "R", None, ""),
        ("unit", "list", "R", "waste_unit", ""),
        ("comment", "text", "O", None, ""),
    ],
    "Sources": [
        ("dataset_id", "text", "R", None, "As in Datasets. One row per dataset."),
        ("data_source", "list", "R", "data_source", "field (measured or surveyed on farms), statistical or literature."),
        ("data_source_reference", "text", "R", None, "The source as it should be cited, e.g. 'ISTAT (2015-2020)'."),
        ("farms_sampled", "number", "O", None, "For survey data."),
        ("extrapolations", "text", "O", None, "What was extrapolated, and from what."),
        ("region_detail", "text", "O", None, "Narrower area the data refer to."),
        ("share_of_national_production", "%", "O", None, "Share of the national production represented."),
        ("pv_years", "text", "O", None, "Years of the production volume."),
        ("product_description", "text", "O", None, "Common and scientific name, production system, destination of the product."),
        ("comment", "text", "O", None, "Anything else the reviewer should know."),
    ],
}
TITLES = {
    "Datasets": "One row per dataset: crop, country, period, system, yield and site values.",
    "Coproducts": "One row per co-product of a dataset.",
    "Fertilisers": "One row per fertiliser, manure, compost, sewage sludge, lime or micronutrient of a dataset.",
    "Pesticides": "One row per active ingredient of a dataset.",
    "Operations": "One row per field operation of a dataset, with passes and diesel.",
    "Energy_water": "One row per energy carrier or water source of a dataset (irrigation amount is in Datasets).",
    "Materials": "One row per material of a dataset.",
    "Wastes": "One row per waste item of a dataset.",
    "Sources": "One row per dataset: data sources and description (read by the metadata model).",
}

EXAMPLES = {
    "Datasets": {"dataset_id": EXAMPLE_ID, "crop": "wheat", "country": "Italy", "region": "N/A", "period_start": 2019,
                 "period_end": 2020, "production_system": "open ground", "organic": "no", "crop_cycle_duration": 9.5,
                 "yield_main_product": 6500, "irrigated": "no", "irrigation_water": 0, "irrigation_water_unit": "m3/ha",
                 "irrigation_share_surface": "N/A", "irrigation_share_sprinkler": "N/A", "irrigation_share_drip": "N/A",
                 "drained_share": 30, "tillage": "fall plough", "anti_erosion_practice": "no practice",
                 "planting_density": 180, "grp_compost_sludge": "0", "grp_lime_micronutrients": "0", "grp_other_energy": "0",
                 "grp_materials": "0", "grp_wastes": "0"},
    "Fertilisers": [
        {"item": "urea", "amount": 75, "unit": "kg N"},
        {"item": "ammonium nitrate", "amount": 75, "unit": "kg N"},
        {"item": "triple superphosphate (TSP)", "amount": 60, "unit": "kg P2O5"},
        {"item": "potassium chloride (KCl)", "amount": 80, "unit": "kg K2O"},
        {"item": "liquid manure, cattle", "amount": 20, "unit": "m3", "liquid_manure_dilution": "N/A"}],
    "Pesticides": [{"active_ingredient": "Glyphosate", "amount": 1500, "unit": "g a.i."},
                   {"active_ingredient": "Mancozeb", "amount": 500, "unit": "g a.i."}],
    "Operations": [{"operation": "tillage, ploughing", "passes": 1, "diesel": "N/A", "diesel_unit": "l/ha"},
                   {"operation": "combine harvesting", "passes": 1, "diesel": "N/A", "diesel_unit": "l/ha"}],
    "Sources": {"data_source": "literature", "data_source_reference": "Regression case wheat_IT of AgriToolV.1 (illustration only)",
                "comment": "Example row: the reader ignores rows whose dataset_id starts with EXAMPLE."},
}

# ---------------------------------------------------------------- build
wb = Workbook()
wb.remove(wb.active)
guid = wb.create_sheet("Guidance")
ws_lists = wb.create_sheet("Lists")
ranges = {}
col = 1
for name, (values, source) in lists.items():
    L = get_column_letter(col)
    ws_lists.cell(1, col, name).font = Font(name=FONT, bold=True)
    ws_lists.cell(2, col, source).font = Font(name=FONT, italic=True, size=8, color="7F7F7F")
    for k, v in enumerate(values):
        ws_lists.cell(3 + k, col, v).font = Font(name=FONT, size=10)
    ref = f"Lists!${L}$3:${L}${2 + len(values)}"
    wb.defined_names[f"list_{name}"] = DefinedName(f"list_{name}", attr_text=ref)
    ranges[name] = f"list_{name}"
    ws_lists.column_dimensions[L].width = max(14, min(45, max(len(str(v)) for v in values) + 2))
    col += 1
ws_lists.freeze_panes = "A3"

for sheet, fields in SHEETS.items():
    ws = wb.create_sheet(sheet)
    ws.cell(1, 1, sheet).font = Font(name=FONT, bold=True, size=14)
    ws.cell(2, 1, TITLES[sheet] + "  Fill in from row %d; grey rows are the example." % (FIRST_DATA_ROW + 0)).font = Font(name=FONT, size=10)
    for c, (key, unit, status, lst, helptext) in enumerate(fields, start=1):
        st = status.rstrip("*")
        for r, (val, bold) in zip((3, 4, 5, 6), ((key, True), (unit, False),
                                                 ({"R": "required", "E": "expected", "O": "optional (default)", "G": "input group", "T": ""}[st] + ("*" if status.endswith("*") else ""), False),
                                                 (helptext, False))):
            cell = ws.cell(r, c, val)
            cell.font = Font(name=FONT, bold=bold, size=10 if r != 6 else 8)
            cell.fill = FILL[st]
            cell.border = BORDER
            cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws.column_dimensions[get_column_letter(c)].width = max(14, min(34, len(key) + 4))
        last = FIRST_DATA_ROW + N_ROWS[sheet]
        rng = f"{get_column_letter(c)}{FIRST_DATA_ROW}:{get_column_letter(c)}{last}"
        if lst:
            dv = DataValidation(type="list", formula1=f"={ranges[lst]}", allow_blank=True, showErrorMessage=True,
                                errorTitle="Value outside the list", error="Choose a value from the drop-down list.")
            ws.add_data_validation(dv)
            dv.add(rng)
        for r in range(FIRST_DATA_ROW, last + 1):
            cell = ws.cell(r, c)
            cell.fill = INPUT_FILL
            cell.border = BORDER
            cell.font = Font(name=FONT, size=10)
    ws.row_dimensions[6].height = 75
    ws.freeze_panes = ws.cell(FIRST_DATA_ROW, 2)
    # example rows
    keys = [f[0] for f in fields]
    ex = EXAMPLES.get(sheet)
    rows = [] if ex is None else (ex if isinstance(ex, list) else [ex])
    for k, row in enumerate(rows):
        r = FIRST_DATA_ROW + k
        row = dict(row); row.setdefault("dataset_id", EXAMPLE_ID)
        for c, (key, unit, status, lst, _) in enumerate(fields, start=1):
            if key in row:
                v = row[key]
            elif sheet == "Datasets" and status in ("O", "E", "G") or key == "comment":
                v = "N/A" if key != "comment" else None
            else:
                v = None
            cell = ws.cell(r, c, v)
            cell.font = EXAMPLE_FONT
    # pre-fill N/A in the optional columns of Datasets (P3)
    if sheet == "Datasets":
        for r in range(FIRST_DATA_ROW + 1, FIRST_DATA_ROW + N_ROWS[sheet] + 1):
            for c, (key, unit, status, lst, _) in enumerate(fields, start=1):
                if status in ("O", "E", "G"):
                    ws.cell(r, c, "N/A")
ws_lists.sheet_state = "visible"  # hidden in the final template; visible in the draft for review

meta = wb.create_sheet("_meta")
for k, (a, b) in enumerate([("template_version", "3.0-draft"), ("build_date", datetime.date.today().isoformat()),
                            ("master_data_version", "3.12"), ("specification", "docs/template_v3_spec.md, branch template/v3-design")], start=1):
    meta.cell(k, 1, a).font = Font(name=FONT, bold=True)
    meta.cell(k, 2, b).font = Font(name=FONT)
meta.column_dimensions["A"].width = 22; meta.column_dimensions["B"].width = 50
meta.sheet_state = "hidden"

# ---------------------------------------------------------------- guidance
G = [
    ("Crop LCI data collection - template v3 (DRAFT)", "title"),
    ("This workbook collects the data of one or more crop datasets. Each dataset is one crop, in one country, for one period, under one production system. It becomes one ecoinvent unit process.", None),
    ("How to fill it in", "h"),
    ("1. Datasets: one row per dataset. Choose a dataset_id (e.g. WHEAT-IT-1) and use it in all other sheets.", None),
    ("2. The other sheets have one row per input (fertiliser, active ingredient, field operation, ...) with the dataset_id of the dataset it belongs to.", None),
    ("3. Grey italic rows are an example (dataset_id starting with EXAMPLE). The reader ignores them; you can delete them.", None),
    ("4. Give national or regional average practice. Do not enter farm names, addresses or coordinates.", None),
    ("N/A and 0", "h"),
    ("N/A = not available: the tool uses its documented default and reports it. 0 = the input is really not used. An empty cell is read as N/A.", None),
    ("Input groups (last columns of Datasets): N/A = use the rows given in the group's sheet, or the defaults if there are none; 0 = the group is not used on this dataset (no default, no rows).", None),
    ("Colours of the headers", "h"),
    ("required: must be given (N/A is an error). required*: required only in some cases (see the help row).", "R"),
    ("expected: give it if you know it; N/A takes the default with a warning.", "E"),
    ("optional (default): N/A takes the documented default.", "O"),
    ("input group: N/A or 0, see above.", "G"),
    ("Light yellow cells are the cells to fill in. Drop-down lists accept only their values.", None),
    ("Units", "h"),
    ("The unit of each column is in row 4. Where several units are allowed, choose it in the unit column of the row. Amounts are per hectare and per crop cycle.", None),
    ("Sheets", "h"),
] + [(f"{s}: {TITLES[s]}", None) for s in SHEETS] + [
    ("Lists: drop-down lists generated from the tables of data/ (hidden in the final template).", None),
    ("Draft notes (for the review, removed in the final template)", "h"),
    ("Built from docs/template_v3_spec.md (decisions T1-T13) and the tables of data/. Lists marked DRAFT in row 2 of the Lists sheet do not come from data/ yet: field operations (agri-lca-pipeline table), units, energy, materials, wastes, fertiliser labels.", None),
    ("Not yet in this draft: the co-product list from the Master Data (free text for now), the unit conversion table, the per-crop unit of planting_density, the 'diesel used in <operation>' products of Master Data v4.", None),
    ("The IPCC climate zone field is left out (FC, 2026-11-02, removal in progress in the specification).", None),
]
guid.column_dimensions["A"].width = 120
for k, (text, style) in enumerate(G, start=1):
    c = guid.cell(k, 1, text)
    c.alignment = Alignment(wrap_text=True, vertical="top")
    if style == "title":
        c.font = Font(name=FONT, bold=True, size=16)
    elif style == "h":
        c.font = Font(name=FONT, bold=True, size=12)
    elif style in FILL:
        c.font = Font(name=FONT, size=10); c.fill = FILL[style]
    else:
        c.font = Font(name=FONT, size=10)

order = ["Guidance"] + list(SHEETS) + ["Lists", "_meta"]
wb._sheets = [wb[n] for n in order]
wb.active = 0
wb.save(OUT)
print("saved", OUT, {k: len(v[0]) for k, v in lists.items()})

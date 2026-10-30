# Data-collection template v3: specification (draft)

Status: **draft for FC review**. Nothing in this document is decided until FC confirms it; the
decisions will then be recorded in `docs/DECISIONS.md`. The Excel file and its reader are built
only after the specification is agreed.

## 1. Purpose

The template is the only document a data provider fills in. Template v3 replaces the legacy
template `templates/LCI-Database_Data-collection_Crop_v2.xlsx` (Quantis, version 2.0.0). It must:

1. describe **several datasets in one workbook** (several crops, countries, periods or systems);
2. ask the provider **only what the provider knows** (practices, inputs, yields) and leave to the
   tool everything that has a documented default in `data/` (site, soil and climate parameters,
   national practice averages);
3. use **controlled vocabularies** for crops, countries, products and active ingredients, each
   mapped to the ecoinvent Master Data, so that the inputs and outputs of the dataset are
   harmonised with the Master Data;
4. be read by a **Python reader** with explicit validation, units and provenance, and feed the model
   layer (`src/legacy_model/`) and, later, the writer of the ecoinvent v4 JSON format.

## 2. Problems of the legacy template that v3 must solve

| # | Legacy behaviour | Consequence | v3 rule |
|---|---|---|---|
| T1 | One crop, one country per workbook, values in one column | One file per dataset; no comparison across datasets | One row per dataset (P1) |
| T2 | Pre-filled `0` for mineral N, P, K, manure and total pesticides, `-` elsewhere | The defaults of these inputs never apply unless the provider deletes the 0; blank water triggers the default irrigation | `N/A` and 0 differ; every input cell starts as `N/A` (P3) |
| T3 | Units only in the label text; the Java reader never reads them (`"TODO"`) | Unit errors are silent | Unit per column or per row, checked by the reader (P4) |
| T4 | Site parameters asked to the provider (climate zones, precipitation, wet days, elevation) | Burden on the provider; inconsistent values | Optional overrides of documented defaults (P2) |
| T5 | Fertilisers as nutrient totals and percentage splits | Providers know products and amounts, not nutrient shares | Products and amounts, nutrient totals as alternative (section 5.3) |
| T6 | Diesel in kg per group of operations, split in % | Providers rarely know the diesel per operation | To be decided (Q6) |
| T7 | Free-text pesticide names become `other` without emission | Toxicity under-counted | Active ingredients from a list; unknown names flagged |
| T8 | Defaults invisible in the output | No traceability | Provenance recorded for every value (P5) |
| T9 | Template version never checked | Old files read with new rules | Version checked by the reader (P6) |

## 3. Principles

- **P1 One row, one dataset.** A dataset is one crop, in one geography, for one period, under one
  production system. It becomes one unit process in ecoinvent v4 (technology + geography + time
  period). Every row has a `dataset_id` chosen by the provider; the input sheets refer to it.
- **P2 Provider data first, documented defaults second.** Every field is either *required* (no
  default exists or the value defines the dataset) or *optional* (the tool has a default in `data/`,
  with its decision number). An optional value given by the provider always overrides the default.
- **P3 N/A is not zero (Q3, decided by FC on 2026-10-27).** Every input cell of the template starts
  with the text `N/A` (not available): the tool uses the default and flags it. The provider
  overwrites it with the value, or with `0` when the input is really not used on the dataset; 0 is
  always a real zero and never triggers a default. A cell left empty (N/A deleted) and the Excel
  error value `#N/A` are read as N/A, with a warning for the empty cell. A required field (R) may
  not be N/A.
- **P4 Units are explicit.** Each numeric column has one unit, written in the header; where several
  units are allowed (fertilisers, energy, irrigation water) the row has a `unit` column with a
  drop-down list. The reader converts to the units of the model with the factors of a unit table
  in `data/` (e.g. 1 mm of water = 10 m3/ha) and rejects unknown units.
- **P5 Provenance per value.** The reader records for every model input whether it comes from the
  template (sheet, cell) or from a default (data file and decision number). The provenance feeds the
  standard comments of the dataset.
- **P6 Versioned template.** A hidden sheet `_meta` holds the template version. The reader accepts
  only the versions it knows.
- **P7 Controlled vocabularies.** Drop-down lists come from the tables of `data/` (crop list,
  countries, products, active ingredients, operations), never typed by hand in the workbook. A
  value outside the list is an error, except in the free-text `other` rows, which are flagged.
- **P8 National or regional averages, no farm identity.** The template describes average practice
  of a country or region. It asks no farm name, address or coordinates of a single farm
  (`CLAUDE.md`: no identifiable farm data in the repository).
- **P9 English only**, labels and guidance.

## 4. Workbook structure

| Sheet | Shape | Content |
|---|---|---|
| `Guidance` | text | How to fill in the template; N/A vs 0; units; one example dataset |
| `Datasets` | one row per dataset | Identity, system, yield, site overrides (section 5.1) |
| `Coproducts` | one row per co-product | Co-products of each dataset (section 5.2) |
| `Fertilisers` | one row per product | Mineral fertilisers, manure, compost, sewage sludge, lime and micronutrients (section 5.3) |
| `Pesticides` | one row per active ingredient | Active ingredients and amounts (section 5.4) |
| `Operations` | one row per operation | Field operations (section 5.5) |
| `Energy_water` | one row per carrier | Electricity, fuels, heat, irrigation and other water (section 5.6) |
| `Materials` | one row per item | Plastics, greenhouse and tunnel area, trellis (section 5.7) |
| `Wastes` | one row per item | Plastic waste, biowaste, wastewater (section 5.8) |
| `Sources` | one row per dataset | Data sources, collection method, reference period, comments (section 5.9) |
| `Lists` (hidden) | lists | Drop-down lists generated from `data/` by a build script |
| `_meta` (hidden) | key/value | Template version, build date, Master Data version of the lists |

The long sheets (`Fertilisers` to `Wastes`) have the same first columns: `dataset_id`, `item`
(drop-down), `amount`, `unit` (drop-down), `comment`.

`Datasets` has one **input-group column** per long-sheet group, pre-filled with `N/A` like every
other input cell (Q3): mineral fertilisers, manure, compost and sewage sludge, lime and
micronutrients, pesticides, field operations, other energy, materials, wastes. Irrigation is not an
input group: it is set by the `irrigated` field of `Datasets` (section 5.12).

| Group column | Rows of the dataset in the long sheet | Result |
|---|---|---|
| `N/A` | none | Defaults of the group (or 0 where the group has no default), flagged |
| `N/A` | one or more | The rows are used; inputs of the group not listed in the rows are 0 |
| `0` | none | Group not used: no default, no input |
| `0` | one or more | Error: contradiction |

Within a row, `amount` = `N/A` is allowed only where the item has its own default (e.g. a manure
type given without amount); otherwise it is an error.

## 5. Fields

Legend: **R** required (N/A is an error), **E** expected (the provider must give it if known; N/A
takes the default with a prominent warning), **O** optional with a default (decision in
brackets), **D** dropped (derived or not used), **N** new field. "Legacy tag" is the column-A tag
of template v2.

### 5.1 Sheet `Datasets`

| Field | Unit | Status | Legacy tag | Default / note |
|---|---|---|---|---|
| `dataset_id` | text | R, N | - | Unique in the workbook |
| `crop` | list | R | `crop` | `crop_types.csv` (67 crops) |
| `country` | list | R | `country` | Any country or area of UN M49 (section 5.10, Q1 decided) |
| `region` | text | O, N | - | Sub-national region, documentation only for now |
| `period_start`, `period_end` | year | R, N | - | Time period of the dataset (ecoinvent v4 unit process) |
| `production_system` | list | R | `cultivation_type` | open ground; greenhouse soil heated / unheated; greenhouse hydroponic heated / unheated |
| `organic` | yes/no | R | `organic_certified` | |
| `crop_cycles_per_year` | number | O, N | dates | Replaces the four dates (Q4); default 1 |
| `yield_main_product` | kg FM/(ha and crop cycle) | E | `yield_main_product_per_crop_cycle` | N/A -> default FAOSTAT 2021-2024 per crop cycle (L23, L24), with warning. A given value is checked for plausibility (section 5.11). Crops without a default yield (guar, mulberry, pomegranate) require the value |
| `irrigated` | yes/no | R, N | - | No "unknown" (Q5, section 5.12). Sets the land use flows (irrigated or non-irrigated) |
| `irrigation_water`, `irrigation_water_unit` | m3/ha or mm, per crop cycle | R if `irrigated` = yes | `total_wateruse` | No default (section 5.12); must be 0 or N/A when `irrigated` = no |
| `irrigation_share_surface`, `irrigation_share_sprinkler`, `irrigation_share_drip` | % of the irrigation water | R if `irrigated` = yes, N | `ratio_irr_*` (not in v2) | Sum 100 %; one technique = 100 %. No default (section 5.12) |
| `drained_share` | % of area | O | `drainage` | Default 0 (L5) |
| `tillage` | list | O | `tillage_method` | Default "unknown" (factor 1); C factor, section 5.13 |
| `anti_erosion_practice` | list | O | `anti_erosion_practice` | Default "unknown" (factor 1); P factor, section 5.13 |
| `slope` | % | O, N | - | N/A -> 3 %, flooded rice 0 % (rule of L6); section 5.13 |
| `plantation_lifetime` | years | O | `orchard_lifetime` | Perennials only; default ecoinvent 3.12 (L50) |
| `planting_density` | seeds kg, seedlings or trees per ha | O | `seeds`, `nb_seedlings`, `nb_planted_trees` | Defaults L46, L47; the unit follows the crop type |
| `annual_precipitation` | mm/yr | O | `average_annual_precipitation` | Default TerraClimate (section 5.13); WFLDB 2017 (L22) until it is built |
| `rainfall_erosivity` | MJ mm/(ha h yr) | O, N | - | Default from GloREDa; section 5.13 |
| `ipcc_climate_zone` | list | O, N | - | Default from the IPCC climate zone map; only if the IPCC 2019 climate-specific N2O factors are adopted; section 5.13 |
| `soil_clay`, `soil_silt`, `soil_sand` | % of fine earth | O, N | - | Default from HWSD v2.0; section 5.13 |
| `soil_organic_carbon` | % | O, N | - | Default from HWSD v2.0; section 5.13 |
| `soil_ph` | - | O, N | - | Default from HWSD v2.0; section 5.13 |
| `climate_zone`, `climate_zone_specific` | list | D | `climate_zone_1`, `climate_zone_specific` | Dropped: used only for the rainfall erosivity R, now taken from GloREDa (Q7, section 5.13) |
| `wet_days`, `elevation` | days, m | D | `nb_wet_days_per_year`, `mean_elevation_m` | Dropped for the same reason (Q7) |
| `record_entry_by`, `collection_method` | text | moved | same | To sheet `Sources` |

### 5.2 Sheet `Coproducts`

`dataset_id`, `coproduct` (list of Master Data products, e.g. straw), `amount` (kg FM/(ha and crop
cycle)), `fate` (sold, left on field, burned, composted; N). Replaces `yield_BP1..3_per_crop_cycle`,
whose name was the free text of the label. The fate is needed for crop residues (N input, heavy-metal
export) and for the functional flows of the v4 dataset (Q8).

### 5.3 Sheet `Fertilisers`

One row per product and dataset. `item` is one of:

- a **mineral fertiliser product** of `fertiliser_product_basis.csv` (urea, AN, CAN, AS, UAN, MAP,
  DAP, ANP, KNO3, TSP, SSP, KCl, K2SO4, raw phosphate, basic slag, patent potassium, liquid
  ammonia), with `unit` = kg product, kg N, kg P2O5 or kg K2O;
- a **total mineral nutrient** when the products are unknown (`mineral N total`, `mineral P2O5
  total`, `mineral K2O total`): the tool splits it with the country mix (L45);
- a **lime or micronutrient** (limestone, carbonation lime, seaweed lime, dolomite, Mg fertiliser,
  zinc sulfate, zinc oxide, other Zn, borax, gypsum, kaolin, manganese sulfate, portafer, sulfite);
- a **manure** type (liquid: cattle, pig, laying hens, other, in m3; solid: cattle, pig, sheep and
  goats, laying hens, horses, other, in t), with the dilution of liquid manure as optional column
  (default 0.5, legacy);
- a **compost or sewage sludge** type (the types of `organic_fertiliser_composition.csv`), in t FM.

Defaults when the dataset has no fertiliser row: mineral N, P2O5, K2O (L28-L37, L53), mix (L45),
manure (L29, L40, L42). Compound fertilisers are counted with the rule of R8 (one exchange, mass =
minimum over the nutrients, rest on the generic product). NPK products are not in the list until
the Master Data contents of `NPK (15-15-15) fertiliser` are clarified (L45 open point).

### 5.4 Sheet `Pesticides`

`dataset_id`, `active_ingredient` (list from `elementary_flow_alignment.csv`, pesticide rows,
grouped by class), `amount` (g a.i./(ha and crop cycle)), `comment`. Unlisted ingredients: rows
`other herbicide / fungicide / insecticide` with the name in `comment`, flagged by the reader.
Horticultural oil in kg. Default when the dataset has no row: total active ingredient of the atlas
(L48), used only for the packaging; no emission without active ingredients (Q9).

### 5.5 Sheet `Operations`

Decided by FC on 2026-10-27 (Q6, option B): one row per field operation, with its diesel and its
number of passes. The diesel model follows the agri-lca-pipeline (repository
`giakoumatos/agri-lca-pipeline`, `calculators/agri_diesel/`, the "Fuel Project" structure), where
the diesel and its emissions are in the crop dataset and not in the field operation dataset.

Columns: `dataset_id`, `operation` (list of the ecoinvent field operations), `passes` (number per
crop cycle), `diesel`, `diesel_unit` (l/ha or kg/ha per crop cycle, both accepted for now),
`comment`. The legacy groups of operations with a diesel total and a percentage split are dropped.

| `passes` | `diesel` | Result |
|---|---|---|
| given | given | Both used as given |
| given | N/A | Diesel = diesel intensity of the operation (kg/ha per pass) for the geography x passes |
| N/A | given | Passes = diesel (kg/ha) / diesel intensity of the operation for the geography, rounded to 0.5 as in the pipeline (more than 8 passes: warning, value not rounded) |
| N/A | N/A | Error: the dataset is not calculated |

Written in the dataset, per kg of main product (as the pipeline does):

- the field operation input = passes / yield (ha per kg);
- the diesel input `diesel used in <operation>` = diesel (kg/ha) / yield (kg per kg).

Data to bring into `data/` (CSV, registered in `sources.csv`, confirmed by FC):

- the diesel intensity per field operation and geography (kg diesel per ha): the table
  `FO_DIESEL_INTENSITIES` of the pipeline, built there from `exchanges (3.12, undef).xlsx` and the
  field-operation list `FO UND.xlsx` of the Fuel Project (104 rows, 151 operation-geography
  pairs). Either copied with its source or rebuilt in AgriToolV.1 by a script from the same two
  files (`FO UND.xlsx` to be supplied by FC);
- the geography of the intensity for each country (`config/models/fo_geography_map.csv` of the
  pipeline, then GLO and RoW as fallback, as in the pipeline). How it combines with the M49
  fallback of section 5.10 is to be agreed;
- the list of operations of the template = the operations of the intensity table.

Open points:

- litres -> kg: FC proposes 0.835 kg/l (average) or 0.832 kg/l (EN 590 specification) (FC,
  2026-10-27). Master Data 3.12 gives `diesel` no density (only the net heating value,
  42.8 MJ/kg). The value enters the unit table only with a document supplied by FC that states
  it; candidates: the JEC Well-to-Tank report v5, Annexes, Appendix 2 section 4.1 "Standard
  properties of fuels" (JRC 2020, open access), or the standard EN 590 itself, which specifies a
  range (820-845 kg/m3 at 15 degrees C), not a single value;
- the 67 products `diesel used in <operation>` of the pipeline are not in Master Data 3.12 (their
  UUIDs come from the pipeline's lookup): the Master Data version that holds them is to be
  confirmed for the alignment tables;
- an operation not in the list: free text with its diesel, written as
  `diesel, burned in agricultural machinery` (MJ, with the 42.8 MJ/kg of the Master Data);
- a provider who knows only the total diesel of the dataset gives it once (item `total diesel`,
  FC 2026-10-27, case 2 of the pipeline): it is split over the listed operations without their own
  diesel in proportion to intensity x passes, z x a / (a + b + ...), where a, b are the kg/ha of
  each operation for the geography times its passes; operations with their own diesel keep it.
  The passes of each operation are then required (otherwise the split has no basis).

### 5.6 Sheet `Energy_water`

Electricity (grid, on-site photovoltaic, on-site wind) in kWh; diesel outside tractors, petrol,
fuel oil light and heavy, natural gas, lignite and hard coal briquettes in kg or MJ or Nm3; wood
pellets, chips, logs in kg; heat (district, solar collector) in MJ. For irrigated datasets, optional
source shares of the irrigation water (groundwater, surface water, other; default WFLDB 2017, L22);
the amount and the techniques of irrigation are in `Datasets` (section 5.12). Other water
(cleaning, processing on farm) in m3 by source.

### 5.7 Sheet `Materials`

Fleece, silage foil, covering sheet, bird net in kg; greenhouse glass, greenhouse plastic and
plastic tunnel in m2 of soil covered (L51); trellis yes/no/unknown (default rule of L47).

### 5.8 Sheet `Wastes`

Plastic waste in kg with landfill / incineration shares (default 50/50, legacy); biowaste in kg with
fate shares; wastewater to treatment and to nature in m3; COD in mg/l.

### 5.9 Sheet `Sources`

One row per dataset. The columns are the `facts` of the meta model of the agri-lca-pipeline
(`meta_model/meta_facts.py`, sheet `facts` of its `dataset_input_template.xlsx`), so that the meta
model can read them directly and build the metadata of the dataset (FC, 2026-10-27):

| Column | Content |
|---|---|
| `dataset_id` | As in `Datasets` |
| `data_source` | field (measured or surveyed on farms), statistical (national statistics) or literature |
| `data_source_reference` | The source as it should be cited, e.g. "ISTAT (2015-2020)" |
| `farms_sampled` | Number of farms, for survey data |
| `extrapolations` | What was extrapolated, and from what |
| `region_detail` | The narrower area the data refer to, e.g. "the hills of Tuscany" |
| `share_of_national_production` | % of the national production the data represent |
| `pv_years` | Years of the production volume |
| `product_description` | Common and scientific name of the crop, production system and destination of the product (for the general comment) |
| `comment` | Anything else the reviewer should know |

The fields are text and are not used in calculations. The meta model organises them, together with
the inputs of the other sheets (operations, fertilisers, pesticides, defaults used and their
provenance), into the metadata fields required by ecoSpold2 (sampling procedure, geography, time
period and technology comments, extrapolations); the update to the ecoinvent v4 JSON format comes
later. The name and e-mail of the person who collected the data are not asked in the workbook
(P8): the provider sends them separately.

### 5.10 Geography and fallback of the defaults (Q1, decided by FC on 2026-10-27)

- The `country` list is the UN M49 list of countries and areas (UNSD overview table supplied by
  FC, `data/external_data/UNSD — Methodology.csv`, 248 countries and areas with their region,
  sub-region and intermediate region). The provider picks the name; the tool stores the M49 code,
  which also gives the geography of the ecoinvent v4 dataset. The list in the template is built
  from a table of `data/` extracted from this file and confirmed by FC before use.
- A default that has no value for the country falls back along the M49 hierarchy:
  **country -> intermediate region (where it exists) -> sub-region -> region -> World**. M49 has
  intermediate regions only in Africa and the Americas (Caribbean, Central America, South America,
  Eastern, Middle, Southern and Western Africa), where the sub-regions are very large
  (Sub-Saharan Africa, Latin America and the Caribbean); elsewhere the chain goes from the country
  to the sub-region (e.g. Greece -> Southern Europe -> Europe -> World).
- The reader records the level used (country, intermediate region, sub-region, region, World) in
  the provenance of each value, so that the dataset comment states it.
- How the value of an aggregate is computed (simple mean, weighted mean and weight, minimum number
  of countries) and for which tables a fallback is acceptable is decided table by table with the
  defaults, not in the template. Until a table has M49 aggregates, its existing fallback applies
  (GLO row of the crop x country matrices, IFA region of L37, IPCC region of L42), and a country
  outside the 39 tool countries with no fallback in a table stops the calculation with an error
  that names the table.

### 5.11 Plausibility of the yield (Q2, decided by FC on 2026-10-27)

A yield given by the provider is never replaced. It is compared with two references, and each
comparison gives a warning (never an error) when the yield lies outside the reference by more
than the tolerance:

1. the FAOSTAT default yield of the crop and country (`default_yield.csv`, L23, L24), with the
   fallback of section 5.10 when the country has no value;
2. the yield of the same crop in the ecoinvent database of the **same country only** (FC,
   2026-10-27, option B): kg of main product per ha and crop cycle of the ecoinvent 3.12 datasets
   of the crop, derived from the release file supplied by FC as in L47 and L50 (annual crops:
   10000 / land transformation per kg; perennial crops: 10000 / land occupation per kg).

Tolerance: +/- 10 % for both references (FC), stored as a parameter in `model_parameters.csv`, not
in the code. The warning states the given yield, the reference value, its source and the
deviation in %.

Rules of the ecoinvent reference:

- one dataset of the crop in the country: its yield +/- 10 %;
- several datasets in the country or its sub-national regions (e.g. US-IA, US-IL; BR-SP): the
  range from the lowest to the highest yield, +/- 10 %;
- no dataset in the country: no ecoinvent comparison, only the FAOSTAT check. Rejected: the GLO or
  RoW dataset (option A) and the datasets of the nearest M49 area (option C), which give warnings
  against references that do not describe the country (e.g. wheat IT, 4000 kg/ha: +16 % against
  ecoinvent GLO 3450, +31 % against ES 3049, while FAOSTAT IT is 3824);
- not used as reference: datasets produced with the legacy tool (comment of the land use
  exchanges, as in L50), datasets without land transformation (annual crops; e.g. several
  Australian wheat and maize datasets) and values that FC excludes as implausible in the review
  of the table.

To be built and confirmed by FC before use:

- the crop -> ecoinvent activity mapping for all 67 crops (today only for the planted crops in
  `ecoinvent312_planting_crop_mapping.csv` and `orchard_lifetime_crop_mapping.csv`), signed by FC;
- the derived table (per dataset: activity, geography, yield per ha and crop cycle, flags), shown
  to FC with the comparison to FAOSTAT.

A first check on six crops (wheat, grain maize, rice non-basmati, potato, soybean, apple; scratch
analysis, not stored) found: deviations of 20-30 % from FAOSTAT also in datasets not made with the
legacy tool (wheat US -30 %, apple CN -31 %); the legacy-tool datasets of wheat, maize and rice IN
at +59 %, +121 % and +82 %; soybean IN at 27 500 kg/ha against 1092 kg/ha in FAOSTAT (not flagged
as made with the legacy tool; to be reported to the ecoinvent data team).

Note: if the year-to-year variation of the FAOSTAT yields (2021-2024 series of `default_yield.csv`)
is often larger than 10 %, the warning will be frequent; this is accepted, since it does not block
the calculation. The share of the series outside +/- 10 % of their mean can be checked when the
reference is built.

### 5.12 Irrigation (Q5, decided by FC on 2026-10-27)

- `irrigated` = yes: the provider gives the irrigation water of the crop cycle, in m3/ha or mm
  (1 mm = 10 m3/ha; the conversion factor sits in the unit table of the reader in `data/`, not in
  the code). N/A is an error: there is no default irrigation water any more.
- `irrigated` = yes: the provider also gives the share of the water applied with each technique,
  surface, sprinkler and drip (sum 100 %; a single technique is 100 %). N/A is an error: the
  AQUASTAT technique shares of the country (L44) are no longer a default of the template input.
  The techniques are used for:
  - the irrigation efficiency of the plausibility range below (0.45 surface, 0.75 sprinkler,
    0.90 drip, `model_parameters.csv`, L44);
  - the irrigation input of the dataset: Master Data 3.12 has one product `irrigation` (m3),
    produced by the activities `irrigation, surface`, `irrigation, sprinkler` and
    `irrigation, drip` and supplied in a country by `market for irrigation`. With the techniques
    known, the input can be split into one amount per technique, each linked to its activity (an
    activity link in ecoSpold v3, a process link in ecoinvent v4) instead of the country market.
    To be confirmed with the v4 writer design.
- The legacy split of each technique into electricity, diesel and no energy (template v2 tags
  `ratio_irr_*_electricity`, `_diesel`, `_no_energy`, never in the v2 sheet) is not asked: the
  energy of pumping is part of the ecoinvent irrigation activities. To be checked against these
  activities, together with whether they already carry the water source (in which case the source
  shares of section 5.6 are not needed either).
- `irrigated` = no: no irrigation, the land use flows are the non-irrigated ones.
- There is no "unknown". A dataset that averages irrigated and non-irrigated land is entered as two
  datasets (two rows of `Datasets`), one irrigated and one not; rejected: a share of irrigated
  area with the water averaged over the whole area, which would require splitting the land
  occupation between irrigated and non-irrigated flows.
- Plausibility (warning, never an error): the given water is compared with the range of Pfister &
  Bayer (2014) (`pfister2014_blue_water_country.csv`, columns `bw_min_m3_t` and `bw_max_m3_t`,
  L44), converted to the same basis as the default of L44: range (m3/ha) = [min, max] x yield
  (kg/ha and crop cycle) / 1000 / irrigation efficiency, with the efficiency of the technique
  shares of the dataset. The warning says that the reference is a national average
  that includes non-irrigated production, so a fully irrigated dataset can lie above it.
- The Pfister expected value (`bw_expected_m3_t`) is no longer a default of the template input;
  whether the model keeps it as a default for other uses is decided with the defaults.

### 5.13 Soil, climate and topography (Q7, decided by FC on 2026-10-30)

Sources proposed in Antón (2026), *Ideas to enhance a crop production LC inventory tool*, Table 1
and section ACTIVITY DESCRIPTION, and supplied by FC in `Literature/` and `data/external_data/`.

- **Rainfall erosivity R.** In the legacy erosion model R is estimated with the LANCA equations
  of the Köppen climate zone, from annual precipitation, wet days and elevation
  (`erosionmodel.py`). In AgriToolV.1 climate zone 1, climate zone 2, wet days and elevation are
  used only for this (the NH3 model no longer reads the climate since L38). R is taken instead
  from the Global Rainfall Erosivity Database, GloREDa (ESDAC; `Public_GLOREDA_07082023.zip`),
  so these four fields are removed from the template. Optional override: `rainfall_erosivity`.
- **Slope.** Optional field `slope` (%). N/A keeps the rule of L6 (3 %, flooded rice 0 %), which
  sets the LS factor and the 3 % threshold of the phosphate run-off. This revises L6 (no slope
  field) for providers who know the slope.
- **Soil.** Clay, silt, sand, soil organic carbon and pH from the Harmonized World Soil Database
  v2.0 (FAO & IIASA 2023; `HWSD2_RASTER.zip`, documentation `HarmonizedWorldSoilDatabase.pdf`),
  replacing the country table of WFLDB 2017 (L22, L26). Optional overrides: `soil_clay`,
  `soil_silt`, `soil_sand`, `soil_organic_carbon`, `soil_ph`.
- **Soil erodibility K** from the texture with the equation of Bos et al. (2016), LANCA v2.0
  (`LANCA_CFLCIA.pdf`, `LANCA.xlsx`), replacing the WFLDB soil-type factors of L27; not a
  template field.
- **C factor** (cover management), all countries (FC, 2026-10-30): C = C_crop x C_management, the
  form of Panagos et al. (2015a), Eq. 1 (`Panos_soilerosioncover-managmentfactorEU.pdf`).
  - C_crop is a property of the crop, not of the EU, so it is applied in every country: Panagos
    et al. (2015a) Table 1 (16 arable crops and fallow, values from a literature review) for the
    crops it covers; for the other crops (vegetables, fruit, perennials, tropical crops) the crop
    classes of Borrelli et al. (2017), *Nature Communications* 8: 2013
    (`Borrelli_assessmentonsoilerosion.pdf`), which assign C values to FAOSTAT crops grouped in
    14 classes: Supplementary Table 2 (`Borelli_SMs_info.pdf`, p. 35) and Supplementary Data 1
    (`Borelli_SMs_data.xlsx`; 176 crops, while the article states 170), transcribed to
    `data/borrelli2017_crop_group_c_factors.csv` and `data/borrelli2017_faostat_crop_groups.csv`
    (branch `data/erosion-factors`). The tool crop -> crop group mapping is a judgement table to be
    signed by FC.
  - C_management from the `tillage` field with the tillage factors of Panagos et al. (2015a)
    Eq. 4a (conventional 1, conservation or ridge tillage 0.35, no till 0.25); the template list of
    tillage methods is aligned with these classes. The factors of Panagos et al. (2015a) for cover
    crops and plant residues apply if the template asks for them (optional fields, to be decided
    with Q8).
- **P factor** (support practices) (FC, 2026-10-30):
  - practice given in `anti_erosion_practice`: P from Wischmeier & Smith (1978), USDA Agriculture
    Handbook 537 (`AH_537 Predicting Rainfall Soil Losses.pdf`), Table 13 (contouring), Table 14
    (contour strip cropping) and Table 15 (contour-farmed terraced fields), by slope class (slope
    of the dataset or its default), in every country;
  - practice N/A or "none": P = 1 outside the EU (no practice; standard assumption of global
    studies); in the EU the P factor of Panagos et al. (2015b) (`Panagos Pfactor.pdf`; stone walls,
    grass margins and contour farming from LUCAS), aggregated to the country, as default;
  - the legacy practice factors of `erosionmodel.py` (0.75, 0.5, 0.37, 0.25, no documented source)
    are replaced by the tables of AH 537.
  - Agriculture Handbook 703 (Renard et al. 1997, RUSLE;
    `Renard_1997_Predictingsoilerosionbywater_aguidetoconservationplaningwithRUSLE.pdf`,
    chapter 6) is the revised method, but its contouring P is computed from ridge height,
    cover-management condition and storm erosivity (Eq. 6-1 and 6-2, Table 6-3) and its terrace P
    (Table 6-15) needs the terrace interval and the outlet type, which the template does not ask.
    FC chose AH 537 (option a, 2026-10-30); AH 703 is the methodological reference.
    (`RUSLE2 Handbook_0.pdf` is the user handbook of the RUSLE2 program, not AH 703.)
  - Tables 13-15 of AH 537 are transcribed to `data/ah537_p_factors.csv`; the slope classes are
    printed with gaps (1-2, 3-5 %, ...): the rule for intermediate slopes is set in the
    implementation.
- **IPCC climate zone** (`Climate_Zone.zip`): needed only if the climate-specific N2O factors of
  IPCC 2019 (wet / dry climate) are adopted in the model. The classes of the map (IPCC 2006,
  JRC) are to be checked against figure 3A.5.1 of the 2019 Refinement. Optional override:
  `ipcc_climate_zone`.
- **Annual precipitation** (FC, 2026-10-30): default from TerraClimate (Abatzoglou et al. 2018,
  *Scientific Data* 5: 170191; `TerraClimate_highresglodatasetofclimaticwater.pdf`), monthly
  gridded precipitation at about 4 km, summed to annual values, aggregated over the crop area like
  the other maps. TerraClimate
  also gives the reference evapotranspiration, so the same source provides the ratio of
  precipitation to potential evapotranspiration that IPCC 2019 uses to separate wet and dry
  climates. Data: the 30-year monthly climatology 1991-2020 of TerraClimate v1.1 (THREDDS
  catalog `TERRACLIMATE_ALL/summaries`), supplied by FC on 2026-10-30 in `data/external_data/`
  as `TerraClimate_19912020_ppt.nc` (147,673,585 bytes) and `TerraClimate_19912020_pet.nc`
  (119,571,852 bytes). Checked from the file headers: netCDF-4 (HDF5) files, complete (the end of
  file address in the header equals the file size); dimensions `lon lat time`; WGS 84
  latitude-longitude grid of 8640 x 4320 cells at 1/24 degree (cell centres -179.979 to
  179.979 and 89.979 to -89.979); 12 monthly steps ("months since January"); variables `ppt`
  ("Accumulated Precipitation") and `pet` ("Reference Evapotranspiration") in mm, stored with
  `scale_factor` and `add_offset`; global note "computed from TerraClimate v1.1 using years
  1991-2020". The data values themselves were not read (no netCDF reader available in that
  check); the build script must report the annual range per country for FC to confirm. The
  period 1991-2020 replaces the "recent period" to be decided above.
  Cross-check: World Bank
  `AG.LND.PRCP.MM` (FAO AQUASTAT long-term average precipitation per country,
  `API_AG.LND.PRCP.MM_DS2_en_csv_v2_1875.zip`). Replaces the WFLDB 2017 default (L22) once built.

All these columns start as N/A (P3): N/A takes the default and records its source in the
provenance; a value of the provider (e.g. local soil analyses) replaces it for that dataset.

The defaults themselves are built with the default tables, not in the template: the maps are
aggregated to the country (and later the region) over the cropland, ideally weighted by the area
of the crop (SPAM 2020, `spam2020V0r1_global_physical_area.zip`); the aggregation rule, the
fallback (section 5.10) and the tables are decided and confirmed by FC there. The GloREDa archive
(about 2.2 GB) has to be processed on FC's computer.

Country boundaries for the aggregation (FC, 2026-10-30):

- **Primary: FAO GAUL 2024**, countries built from level 1 (Global Administrative Unit Layers, FAO Hand-in-Hand
  Geospatial Platform, 2024 edition). Reason: boundaries processed against the UN-recognised
  borders (UN map 2018), the same UN/FAO frame as M49, FAOSTAT (default yields) and SPAM 2020
  (crop area), so a country has the same outline in all the default sources. Disputed areas are
  separate units and are not assigned to a country. Licence (GAUL Terms of Use supplied by FC,
  2026-10-30): CC BY 4.0, which allows use, adaptation and re-dissemination of the data and of
  derived works, commercial use included, under three conditions:
  - every default derived from GAUL cites "FAO. 2024. Global Administrative Unit Layers (GAUL).
    [Accessed on DD Month YYYY]. https://data.apps.fao.org/?lang=en. Licence: CC-BY-4.0" (to go
    in `data/sources.csv` and in the provenance of the defaults);
  - no statement that FAO approved or endorsed the use (terms, para. 8);
  - third-party data inside GAUL may carry other terms, listed in the dataset metadata
    (para. 6); the build script checks the metadata of the downloaded file.
  FAO distributes only the subnational levels (`GAUL_2024_L1`, `GAUL_2024_L2`), no country
  layer: the build script dissolves level 1 by `gaul0_code` (attributes `gaul0_code`,
  `gaul0_name`, `iso3_code`, `map_code`, `disp_en`), and maps `iso3_code` to M49 through the
  UNSD table; units without a country (disputed areas) are listed for FC. Level 1, to be
  downloaded by FC into `data/external_data/` (not yet supplied).
- **Fallback: the ecoinvent geography geometries** (Natural Earth based, ecoinvent approach), used
  if the GAUL 2024 coverage or third-party terms are not acceptable. Source: internal page "v4 geographies:
  geometries" (DBD space, version 26 of 2026-10-30). v3 geometries: geography.ecoinvent.org,
  geopackage "All geographies" (`all.gpkg`). v4 geopackages: built from the v3 file with the v3 to
  v4 geography mapping, one file for all geographies and one per geography type (country, region,
  sub-region, global); every Master Data geography has a geometry and vice versa. Differences
  from v3 relevant here: Crimea merged into RU, Northern Cyprus and the UK bases into CY, Siachen
  Glacier into IN, Guantanamo Bay into CU, Somaliland into SO; new geometries for GLO and
  UN-SSAFRICA; RU removed from Eastern Europe and IR from Western Asia; Aland Islands and
  Svalbard / Jan Mayen are separate units. Advantage: the region and sub-region geometries match
  the ecoinvent geographies of the M49 fallback (section 5.10) directly. Use the v4 country
  geopackage, supplied by FC into `data/external_data/` (not yet supplied).
- Whichever layer is used, the build script records its name and version in the provenance of
  each default, and lists the countries whose value changes by more than a threshold to be agreed
  with FC between the two layers if both are available.

## 6. Reader and validation (outline)

A Python module reads the workbook into one input record per dataset, with provenance, and maps it
to the inputs of `src/legacy_model/`. Validation, reported per sheet and cell:

- errors (the dataset is not calculated): unknown template version, missing required field,
  `dataset_id` not unique or unknown in a long sheet, value outside a list, unknown unit,
  negative amount, shares not summing to 100 % (tolerance to be set), N/A in a required field,
  input group set to 0 with rows in the long sheet, text other than `N/A` in a numeric cell,
  `irrigated` = yes without irrigation water or without technique shares summing to 100 %,
  `irrigated` = no with irrigation water above 0, field operation with neither passes nor diesel;
- warnings (the dataset is calculated): default used (yield included), empty cell read as N/A,
  yield outside +/- 10 % of the FAOSTAT default or of the ecoinvent yield of the crop in the same
  country (section 5.11), irrigation water outside the Pfister range (section 5.12), more than 8
  passes derived for an operation (section 5.5), free-text `other` rows, inputs given for a field
  the model does not use.

The reader is built after the specification is agreed, with tests on example workbooks that hold
no real farm data.

## 7. Candidate fields that depend on model decisions

These fields are needed only if the corresponding model is adopted (decisions of the model work):

- flooded rice: water regime during and before the cultivation period, organic amendments
  (methane of flooded rice);
- crop residue management (removed, left, burned, incorporated) and residue amount;
- previous land use or year of conversion (land use change, soil carbon);
- soil pH or soil texture overrides (NH3, nitrate, erosion).

## 8. Open questions for FC

| # | Question | Proposal |
|---|---|---|
| Q1 | Geography: only the 39 tool countries, or any M49 country with regional or world defaults? Sub-national regions now or later? | **Decided (FC, 2026-10-27):** any M49 country or area; defaults fall back to intermediate region, sub-region, region and World (section 5.10); `region` as text for documentation. Open: confirm the intermediate-region level |
| Q2 | Should the yield stay required, or may the FAOSTAT default be used when missing? | **Decided (FC, 2026-10-27):** the yield is expected from the provider (E); FAOSTAT default (L23, L24) only when it is N/A, with warning; a given yield gets a non-blocking warning outside +/- 10 % of the FAOSTAT default or of the ecoinvent yield of the same crop in the same country (section 5.11). Open: the crop -> ecoinvent activity mapping and the reference table (section 5.11) |
| Q3 | How does the provider state "not used" for a whole input group (no manure, no pesticides)? | **Decided (FC, 2026-10-27):** every input cell starts as `N/A` (default); `0` is a real zero (P3). Input-group columns in `Datasets` (section 4) |
| Q4 | Replace the four dates of v2 by `crop_cycles_per_year`? | Yes; optional harvest month for documentation |
| Q5 | Irrigation: is the default water (Pfister, L44) applied only when `irrigated` = yes and the amount is N/A, and 0 when `irrigated` = no? What when `unknown`? | **Decided (FC, 2026-10-27):** yes -> water required, in m3/ha or mm, and the shares of surface, sprinkler and drip irrigation; no -> 0; no "unknown"; mixed systems as two datasets; Pfister min-max only as plausibility range (section 5.12) |
| Q6 | Operations: diesel per group (A) or passes per operation (B)? | **Decided (FC, 2026-10-27):** B, one row per operation with diesel (l/ha or kg/ha) and passes; missing diesel from the intensity table of the agri-lca-pipeline, missing passes from diesel / intensity; both missing is an error (section 5.5) |
| Q7 | Climate zone, wet days, elevation: which source for country defaults, or keep them as provider fields? | **Decided (FC, 2026-10-30):** removed; R from GloREDa; optional slope (revises L6); soil from HWSD v2.0, K with LANCA (Bos et al. 2016), C and P from Panagos et al. (2015a, b), IPCC climate zone map; all as optional overrides of defaults (section 5.13) |
| Q8 | Co-product fate: needed now? | Yes, it decides residue N and the functional flows of the v4 dataset |
| Q9 | Pesticides without active ingredients: keep the atlas total for packaging only, or also an emission of an unspecified pesticide? | Packaging only, warning to the provider |
| Q10 | Keep a reader for template v2 files? | No; a one-off conversion script only if old filled templates must be reused |

## 9. Reminders for later (FC, 2026-10-27)

- The Fuel Project (diesel per field operation, the `diesel used in <operation>` products, the new
  field operation datasets) and the OLCA-Pest pesticide emissions are in the agri-lca-pipeline,
  not in AgriToolV.1, and are not to be merged now. Their products and flows will be in the
  Master Data of ecoinvent v4, which is not ready yet; the alignment tables of AgriToolV.1 stay on
  Master Data 3.12 until then.
- The meta model of the agri-lca-pipeline is to be connected to template v3 (sheet `Sources` and
  the inputs) and to organise the metadata to the current ecoSpold2 standard; its update to the v4
  JSON format comes later.

## 10. Next steps

1. FC reviews this specification and answers Q1-Q10.
2. Record the decisions in `docs/DECISIONS.md`.
3. Build script for the `Lists` sheet from `data/`, and the empty template v3 in `templates/`.
4. Reader with validation and provenance, with tests on example workbooks.
5. Adapter from the reader output to the inputs of `src/legacy_model/` (one run per dataset).

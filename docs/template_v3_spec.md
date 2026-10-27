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
  units are allowed (fertilisers, energy) the row has a `unit` column with a drop-down list. The
  reader converts to the units of the model and rejects unknown units.
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
micronutrients, pesticides, irrigation water, field operations, other energy, materials, wastes.

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
| `irrigated` | yes/no/unknown | R, N | - | Decides whether the default irrigation applies (Q5) |
| `drained_share` | % of area | O | `drainage` | Default 0 (L5) |
| `tillage` | list | O | `tillage_method` | Default "unknown" (factor 1) |
| `anti_erosion_practice` | list | O | `anti_erosion_practice` | Default "unknown" (factor 1) |
| `plantation_lifetime` | years | O | `orchard_lifetime` | Perennials only; default ecoinvent 3.12 (L50) |
| `planting_density` | seeds kg, seedlings or trees per ha | O | `seeds`, `nb_seedlings`, `nb_planted_trees` | Defaults L46, L47; the unit follows the crop type |
| `annual_precipitation` | mm/yr | O | `average_annual_precipitation` | Default WFLDB 2017 (L22) |
| `climate_zone`, `climate_zone_specific` | list | D | `climate_zone_1`, `climate_zone_specific` | To be derived from the country; the current default ("temperate") has no source (Q7) |
| `wet_days`, `elevation` | days, m | D | `nb_wet_days_per_year`, `mean_elevation_m` | Same as above: the defaults 180 days and 700 m have no source (Q7) |
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

Option A (legacy): diesel in kg per group of operations and its split. Option B: one row per
operation (list of ecoinvent field operations), number of passes per crop cycle; diesel only
optional for the total. To be decided (Q6).

### 5.6 Sheet `Energy_water`

Electricity (grid, on-site photovoltaic, on-site wind) in kWh; diesel outside tractors, petrol,
fuel oil light and heavy, natural gas, lignite and hard coal briquettes in kg or MJ or Nm3; wood
pellets, chips, logs in kg; heat (district, solar collector) in MJ. Irrigation water in m3/(ha and
crop cycle) with optional technique shares (surface, sprinkler, drip; default AQUASTAT, L44) and
source shares (groundwater, surface water, other; default WFLDB 2017, L22). Other water (cleaning,
processing on farm) in m3 by source.

### 5.7 Sheet `Materials`

Fleece, silage foil, covering sheet, bird net in kg; greenhouse glass, greenhouse plastic and
plastic tunnel in m2 of soil covered (L51); trellis yes/no/unknown (default rule of L47).

### 5.8 Sheet `Wastes`

Plastic waste in kg with landfill / incineration shares (default 50/50, legacy); biowaste in kg with
fate shares; wastewater to treatment and to nature in m3; COD in mg/l.

### 5.9 Sheet `Sources`

One row per dataset: data provider (organisation), data sources, collection method, reference years
of the data, representativeness (share of national production or area, if known), extrapolations,
general comment. These fields feed the documentation of the v4 dataset; they are text and are not
used in calculations.

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

## 6. Reader and validation (outline)

A Python module reads the workbook into one input record per dataset, with provenance, and maps it
to the inputs of `src/legacy_model/`. Validation, reported per sheet and cell:

- errors (the dataset is not calculated): unknown template version, missing required field,
  `dataset_id` not unique or unknown in a long sheet, value outside a list, unknown unit,
  negative amount, shares not summing to 100 % (tolerance to be set), N/A in a required field,
  input group set to 0 with rows in the long sheet, text other than `N/A` in a numeric cell;
- warnings (the dataset is calculated): default used (yield included), empty cell read as N/A,
  yield outside +/- 10 % of the FAOSTAT default or of the ecoinvent yield of the crop in the same
  country (section 5.11), free-text `other` rows, inputs given for a field the model does not use.

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
| Q5 | Irrigation: is the default water (Pfister, L44) applied only when `irrigated` = yes and the amount is N/A, and 0 when `irrigated` = no? What when `unknown`? | yes -> default; no -> 0; unknown -> default weighted by the irrigated share, if a source for it is available, else error |
| Q6 | Operations: diesel per group (A) or passes per operation (B)? | B, with optional total diesel as a check |
| Q7 | Climate zone, wet days, elevation: which source for country defaults, or keep them as provider fields? | Look for a source among the documents of FC; until then keep them optional with the current default, tagged legacy, undocumented, provisional |
| Q8 | Co-product fate: needed now? | Yes, it decides residue N and the functional flows of the v4 dataset |
| Q9 | Pesticides without active ingredients: keep the atlas total for packaging only, or also an emission of an unspecified pesticide? | Packaging only, warning to the provider |
| Q10 | Keep a reader for template v2 files? | No; a one-off conversion script only if old filled templates must be reused |

## 9. Next steps

1. FC reviews this specification and answers Q1-Q10.
2. Record the decisions in `docs/DECISIONS.md`.
3. Build script for the `Lists` sheet from `data/`, and the empty template v3 in `templates/`.
4. Reader with validation and provenance, with tests on example workbooks.
5. Adapter from the reader output to the inputs of `src/legacy_model/` (one run per dataset).

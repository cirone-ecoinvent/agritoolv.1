# Legacy crop LCI tool (sri-crop-tool): how the model works

**Status of this document:** snapshot of 2026-10-26, moved here from the working notes of the legacy analysis. It describes the legacy code (`master` of sri-crop-tool) and the status of the fixes on that date. The detailed analysis is `docs/legacy_analysis.md`; the current status of each point is in `docs/DECISIONS.md` and `docs/legacy_fixes_report.md`.

**Code reference:** `ecoinvent/sri-crop-tool`, branch `master`, commit `a0a434a` (release 1.3.4-EI, built by Quantis 2016–2019).
**Method reference:** Quantis, *Models integrated in ecoinvent LCI calculation tool for crop production* (final report 30 Jan 2018, file dated 2019-10-15). It is called "the description" below.
**Working copy:** the local folder `C:\python\sri-crop-tool` is checked out on branch `legacy-fixes` (fixes F1–F9, October 2026), not on `master`. This document describes `master`. The last column of the issue tables in sections 7 and 8 says whether a `legacy-fixes` commit already addresses the point. That status is based on the commit messages.
**How this was produced:** by reading the code. No model code was run. The only thing imported was the default-table modules (plain dictionaries), to check how many crops and countries they cover.

---

## 1. What one run produces

One run describes one crop, in one country, under one farming system, as declared in an Excel template for **1 ha and 1 crop cycle**.

The tool then:
1. fills missing inputs with crop × country defaults;
2. runs the field-emission models;
3. writes **one ecoSpold2 unit process for 1 kg of main product**. Every per-hectare amount is divided by the fresh-matter yield of the main product.

Coverage: 67 crops (`crops.properties`) and 39 countries (`countries.properties`).

## 2. Architecture

| Layer | Technology | Role |
|---|---|---|
| Front-end | Dart / AngularDart | 4-step wizard: download the template, fill it in, upload it, download the `.spold` |
| Back-end | Java 8, Guice, RESTEasy, Shiro, MyBatis + MySQL | Login and licences; Excel parsing and validation; ecoSpold writing; master-data lookup |
| Calculation engine | Python 3, `http.server` on `localhost:11001/computeLci` | Defaults and emission models. Flat JSON in, flat JSON out |

**Request flow**

1. `POST /api/computeLci`. `ExcelInputReader` parses the sheet `Template`:
   - Row 0 is a hidden header row with column tags.
   - Column A holds a machine tag for each row (e.g. `total_fertnmin`).
   - A block is a `total_x` row, followed by rows with drop-down labels, closed by `end`.
   - Values are typed as Double, String or Date. **Units are never read**: they are implied by the template.
   - Validation:
     - ratio blocks are normalised to sum 1;
     - part blocks are completed with an `other` row;
     - `pest_remains` and `remains_machinery_diesel` are computed in Java.
   - Errors return HTTP 400. Warnings are stored in the database.
2. `POST /api/generateScsv` (despite the name, this produces the ecoSpold file):
   - `ValueGroup.flattenValues()` turns the parsed data into a flat map, with keys such as `total_fertnmin`, `ratio_fertnmin_urea`, `part_herbicides_glyphosate`.
   - `PyBridgeService` sends the map to Python, where `ModelsSequence` runs.
   - Python returns a flat map of about 300 keys.
   - `EcospoldFileWriter` builds the dataset from it.
3. Cell comments become exchange comments. Cell sources, the data-quality scores and the collection method are **dropped**.

A SimaPro CSV writer (`ScsvFileWriter`, WFLDB 3.3 names) is still in the code but cannot be reached from the UI.

## 3. Python engine: how a value is resolved

`ModelsSequence.__init__` builds:

```
allInputs = DefaultValuesWrapper(
    ChainMap(NonStrictInputMapping(user_inputs, EXCEL_INPUT_MAPPING_RULES),
             intermediate_values, output),
    DEFAULTS_VALUES_GENERATORS)
```

Each name is looked up in this order:
1. **User value**, through a mapping rule (`excelInputMappingRules.py`). A rule can:
   - rename a key (`total_fertnmin` → `nitrogen_from_mineral_fert`);
   - collect the `ratio_*` rows of a block into an enum dictionary. If at least one ratio of the block is given, the missing ones are set to 0;
   - convert a string into an enum.
2. **Intermediate values** computed earlier in the run.
3. **Values already written to the output.**
4. Otherwise the **default generator** for that name (`defaultGeneration.py`). Generators are lazy and recursive, and their results are not cached.

**Consequences**
- Defaults are invisible. Nothing is logged and nothing is flagged in the output.
- `KeyError` is used for control flow.
- Each model copies its inputs by name in `__init__`, so the order of execution matters.

**Execution order** (`ModelsSequence.executeSequence`):

1. Direct outputs (metadata, yields, greenhouse, energy and material conversions).
2. Splits of plastic and biowaste disposal.
3. `FertModel`: NH3 and heavy metals from mineral fertilisers.
4. `ManureModel`: N, P2O5 (liquid and solid), heavy metals, NH3.
5. `OtherOrganicFertModel`: N, P2O5 of liquid sludge, heavy metals, NH3.
6. `SeedModel`: heavy metals. Then `mapSeeds`.
7. `ErosionModel`, for open ground only. Other cultivation types get eroded soil = 0.
8. `IrrigationModel` (WFLDB split), then irrigation quantities, then the ecoinvent water split.
9. Fertiliser product amounts.
10. The remaining models: `Co2Model`, `NModel`, `PModel`, `HmModel`, `PackModel`, `LUCModel` with land use.
11. Machinery, COD, pesticides.

## 4. Defaults

| Input | Default rule (code) | Source in code comments |
|---|---|---|
| `crop_cycle_per_year` | From the harvest dates of the previous and the current crop: 1 / (Δyears + Δmonths/12 + ⌊Δdays/14⌋/24). Set to 1 if the dates are missing or the difference is ≤ 0 | — |
| Yield per cycle | Yield per year (crop × country matrix, GLO fallback) ÷ cycles per year | WFLDB GD_crop |
| Dry matter, C content | Water content and C content per crop | GD_crop, various |
| Precipitation | Country table [mm/yr]. 0 for greenhouses. Per cycle: P × 10 / cycles [m3/ha] | GD_crop |
| Climate | Zone 1 = temperate. Zone 2 is derived from zone 1: cool → `snow_winter_continental`, temperate → `warm_summer_dry_warm`, other → `equatorial_summer_dry`. 180 wet days per year, 700 m elevation | — |
| **Irrigation water** | ETirr [m3/t, crop × country] ÷ irrigation efficiency × yield / 1000. Efficiency: surface 0.45, sprinkler 0.75, drip 0.9, weighted by the country technique mix | Pfister (GD_crop `ETirr_m3t`) |
| Mineral N | Crop × country matrix | GD_crop |
| P2O5, K2O, Ca, Zn, Mg | 0 | "maybe in fertistat" |
| Fertiliser type shares | N, P and K: country tables. Ca, Zn, compost, sludge: uniform split | GD_crop |
| Manure | Crop × country matrices for liquid [m3] and solid [kg]. Animal shares from country tables. Liquid-manure undiluted share 0.5 | GD_crop |
| Total pesticides | Crop × country matrix [g a.i.] | GD_crop |
| Seeds, seedlings, trees | Crop × country matrices, which are partial: 25, 15 and 26 crops. **Missing → 0, silently** | GD_crop |
| Orchard lifetime | 20 years (sugarcane: 3). **Also used as the lifetime of greenhouses** | — |
| Soil | Clay, sand, organic C and share of soils with pH ≤ 7: country tables. Texture from clay and sand. K factor by texture (Panagos 2014). C factor per crop | GD_crop |
| Topography | Slope 3 % (rice 0 %). Slope length 50 m. Tillage and anti-erosion practice "unknown" (factor 1) | — |
| N model constants | Bulk density 1300 kg/m3; soil volume 5000 m3/ha; C/N 11; Norg/Ntot 0.85; rooting depth per crop | SQCB |
| N uptake | Crop × country matrix. Pineapple: 2 % of the dry yield | SQCB / GD_crop |
| N in crop residues | IPCC-type formula for 13 crops; fixed values for 12 crops; **0 for all other crops** | IPCC 2006, literature |
| P parameters | Soil P 0.00095 kg/kg; enrichment factor 1.86; delivery ratio 0.2; land-use category per crop | Prasuhn 2006 |
| Machinery | Diesel totals 0. Split by operation: 100 % "other" | — |

**Template asymmetry.** The template ships with `0` already filled in for:
- N, P and K mineral fertiliser;
- liquid and solid manure;
- total pesticides.

Unless the user deletes these zeros, the fertiliser, manure and pesticide defaults are never used. Irrigation water is pre-filled with "-", so the **default irrigation is applied** when the user leaves the cell alone.

## 5. Field models as coded

Units: kg per ha and crop cycle, unless stated otherwise. "cycles" = crop cycles per year.

### 5.1 Ammonia (NH3)

- **Mineral fertiliser** (`FertModel`):
  - NH3 = 17/14 × Σm Nm × [p·EFa,m + (1−p)·EFb,m]
  - The emission factors are from EMEP/EEA 2016, Tab. 3-2, by climate zone 1 and fertiliser type.
  - p = country share of soils with pH ≤ 7.
  - Hydroponics: temperate climate and p = 1 are forced.
  - `an_phosphate` and `potassium_nitrate` use the "other complex NK/NPK" factor.
- **Manure** (`ManureModel`):
  - liquid: m3 × 0.5 × (TAN × EF) [kg N/m3];
  - solid: kg / 1000 × (TAN × EF) [kg N/t];
  - both are then multiplied by 17/14.
  - The TAN × EF products are hard-coded per animal type.
- **Compost and sewage sludge** (`OtherOrganicFertModel`):
  - kg / 1000 × TAN × EF (Agribalyse Tab. 67 × Tab. 154).
  - **The result is not converted to NH3.** It is kg NH3-N, but it is summed with kg NH3 from the other sources (fixed in F5).
- **Total**: `ammonia_total` = mineral + manure + other organic.

### 5.2 Nitrogen oxides (NOx)

- NOx [kg NO2] = N_applied × 0.04 × 14/30 × 46/14 = **0.0613 kg NO2/kg N** (0.0187 kg NOx-N/kg N).
- N_applied is the gross N, NH3-N included.
- Problems:
  - EEA 2016 gives 0.04 kg NO2/kg N (0.0122 kg NOx-N/kg N), so the code is **53 % too high**.
  - The description says the factor applies to N after the NH3 losses, but the code applies it to gross N.
  - Both points are fixed in F1.

### 5.3 Nitrous oxide (N2O)

- N2O = 44/28 × [0.01 × (N_applied + N_residues + NH3-N + NOx-N) + 0.0075 × NO3-N]
- This is the IPCC 2006 Tier 1 structure, with EF1 = EF4 = 0.01 and EF5 = 0.0075.
- Missing compared with the description (both added in F2):
  - **N_som**, the N mineralised from soil organic matter after land-use change;
  - **EF1FR = 0.003 for flooded rice**.
- The rice flag in F2 is an assumption, not a template input.

### 5.4 Nitrate (NO3, SQCB-NO3 model)

- NO3-N = max(0, 21.37 + P / (c·L) × (0.0037·S + 0.0000601·Norg − 0.00362·U))
- Terms:
  - P = precipitation per cycle + irrigation [mm];
  - c = clay [%];
  - L = rooting depth [m];
  - Norg = Corg × 1300 × 5000 / 11 × 0.85;
  - U = N uptake by the crop.
- Supply term **S = N_applied − 0.01 × (N_applied + N_res + NH3-N + NOx-N) − 0.99 × NH3-N**. The description defines S differently:
  - only the soluble part of the organic N should count; the code counts all of it;
  - NOx is not subtracted;
  - an unexplained factor 0.99 is applied to NH3-N;
  - (fixed in F3).
- Time base: the intercept and the Norg term are annual, while the water term is per cycle (decision D1).
- Legumes: the description's "40 % of uptake" rule is not applied in the code. It is not documented whether the uptake table already includes it.
- A clay content of 0 would cause a division by zero.
- Output split:
  - NO3 = NO3-N × 62/14;
  - the drained share goes to surface water, the rest to groundwater.

### 5.5 Phosphorus (SALCA-P, Prasuhn 2006)

- **Leaching to groundwater**:
  - P = Pgwl(land use) / cycles × (1 + 0.2/80 × P2O5 from slurry and liquid sludge), converted to PO4 (× 95/31);
  - groundwater: PO4 × (1 − d);
  - surface water through drainage: PO4 × d × 6 (d = drained share).
- **Run-off**:
  - 0 if slope < 3 %;
  - otherwise Prol(land use) / cycles × (1 + 0.2/80·P2O5_min + 0.7/80·P2O5_slurry + 0.4/80·P2O5_solid manure), converted to PO4.
- **Erosion**: P = 0.00095 × 1.86 × 0.2 × eroded soil / cycles.
- Limitations:
  - The loss rates for vegetables, fruit trees, viticulture and alpine pastures have no source.
  - P from compost and from dehydrated or dried sludge enters no correction factor.

### 5.6 Erosion (RUSLE)

- Soil loss = 1000 × R × K × LS × C × tillage factor × practice factor [kg/ha/yr].
- R: LANCA equations per Köppen zone, using precipitation, elevation and precipitation per wet day.
- LS: Wischmeier–Smith, with `sin(slope)` where the slope is a ratio used as an angle in radians.
- Tillage factor: from 1 (fall plough) to 0.25 (no-till).
- Open ground only.
- **Problem:** some R equations become negative at low precipitation (e.g. −3172 + 7.562·P below 420 mm). Nothing clips them, so the eroded soil can be negative.

### 5.7 Heavy metals (SALCA-HM, Freiermuth 2006)

Seven metals: Cd, Cu, Zn, Pb, Ni, Cr, Hg.

- **Agricultural inputs** [mg/ha]:
  - Mineral fertiliser: mg/kg nutrient × kg nutrient.
    - **Bug:** Zn "other" is counted as **lead**, because its index points to Pb.
    - **Bug:** the lime row is per kg CaO but is applied to kg Ca.
    - Both fixed in F4c.
  - Manure: mg/kg DM × DM × quantity.
    - **Bug:** the quantity is in tonnes, so the result is in g. It is summed as mg, i.e. 1000 × too low (fixed in F4d).
  - Compost and sludge: mg/kg DM × DM × kg. Correct.
  - Seeds: mg/kg DM × DM × quantity.
    - **For trees and seedlings the quantity is a number of plants, treated as kg.** This is not in F1–F9.
  - Fungicides: Cu, and Zn from the dithiocarbamates (Zn stoichiometry), in g a.i. × 0.95 × 1000.
- **Allocation factor**: A = agro / (agro + deposition / cycles).
- **Leaching**: m_leach / cycles × A. The drained share goes to surface water.
- **Erosion**: c_soil(land use) × eroded soil / cycles × **0.86** × 0.2 × A. The description uses an accumulation factor of **1.86** (fixed in F4).
- **Soil**:
  - The code computes A·agro − leaching − erosion. This drops the deposition term of (inputs + deposition − outputs) × A (fixed in F4).
  - `soil_minus_uptake` = soil − dry yield × a fixed coefficient:
    - the coefficient is the generic mean of Tab. 5 for **every crop**;
    - it is not allocated (fixed in F4b).
- Hydroponics: all heavy-metal emissions are set to 0.

### 5.8 Fossil CO2 from urea and lime

- Urea: 44/28 = 1.571 kg CO2/kg urea-N. UAN counts as 50 % urea.
- Lime (limestone, carbonation lime and seaweed lime alike): 44/40.08 = 1.098 kg CO2/kg Ca.
- Dolomite: 2 × 44/24.3 = 3.62 kg CO2/kg Mg × dolomite share.
- All the carbon is assumed to be released (IPCC worst case).
- Changed by L67 (IPCC 2006 Eq. 11.12-11.13): UAN counts as 100 % urea unless a share is given; the dolomite of
  calcium ammonium nitrate gives 0.405 kg CO2/kg N; dolomite is an input in kg of product (0.477 kg CO2/kg), and
  the dolomite share of the Mg fertiliser is gone.

### 5.9 Biogenic CO2 uptake and energy

- CO2 uptake = C content × 44/12 × dry yield of the **main product only**. By-products get no carbon.
- Gross energy:
  - GCV per crop × dry yield, where the GCV table exists;
  - otherwise a proxy: 11.5 MJ per kg of CO2 taken up.

### 5.10 Water

- The water use becomes one intermediate input, `irrigation` [m3].
- The elementary water flows to air, river and groundwater use country ratio tables `EI_IRR_*`. They cover 14 countries, with a GLO fallback.
- `IrrigationModel` (efficiency-based split, 20 % river / 80 % groundwater) feeds only the SimaPro output.
- The shares of irrigation technique and water source matter only for the default water amount.
- **Bug:** the user's "groundwater" utility water is written as the resource `Water, river`.

### 5.11 Land

- **Occupation** = 10000 / cycles [m2a].
  - Irrigated if water use > 0. Because of the default irrigation, this is the case for almost every crop.
  - Greenhouse for annual crops not grown on open ground.
  - Organic crops map to the same flows as conventional ones.
- **Transformation**:
  - annual crops: 10000 m2;
  - perennial crops: 10000 / orchard lifetime.
- **Rice:** the crop type is "Paddy rice", which matches neither branch, so **rice has no land flows** (fixed in F7).
- **LUC** (land-use change):
  - Amount = max(0, country share of area expansion) / cycles. This is the "shared responsibility" approach.
  - The crop-specific table contains **only almond** (11 countries). For the other 66 crops LUC is shared-responsibility only, although the description calls crop-specific the default.
  - The `LUC_crop_specific` parameter therefore changes nothing for those crops.
  - The exchange is written as `land use change, annual|perennial crop`, using a formula divided by the yield.
  - The template declares the unit as kg; Master Data has ha (flagged in F9).
  - Not modelled: N2O from soil organic carbon losses (N_som), and changes in soil carbon from land management.

### 5.12 Packaging, pesticides, machinery, other inputs

- **Packaging**:
  - fertilisers: (N + P2O5 + K2O + Mg + Ca + Zn) × 2 kg;
  - pesticides: kg a.i. × 3;
  - plus horticultural oil.
  - The nutrient mass is used as a proxy for the product mass.
- **Pesticides**:
  - 100 % of each active ingredient is emitted to agricultural soil.
  - The product input uses generic ecoinvent pesticide groups.
  - "Other" and unspecified pesticides get a product input but **no emission**.
  - Copper is counted twice. It is emitted directly as `Copper` to soil, and it also enters the heavy-metal soil balance, which ends up in the same flow.
- **Machinery**: kg of diesel per operation ÷ the diesel use per unit of the matching ecoinvent operation dataset gives the number of operation units (ha, m3, unit or tkm). "Other" becomes MJ of diesel burned (45.0 MJ/kg). The diesel factors are hard-coded from ecoinvent v3.
- **Unit conversions**:
  - energy carriers: kg → MJ, with hard-coded heating values;
  - fleece: kg → m2 (0.017 kg/m2);
  - liquid manure: m3 → kg (× 1006);
  - greenhouses: m2 / lifetime (tunnels also / 25).
- **Waste water**: DOC = TOC = COD / 2.7 and BOD5 = 0.5 × COD, all emitted to groundwater.

## 6. ecoSpold writer (Java)

**Dataset metadata**
- Activity name: taken from `ecospold_activity_name_mapping.properties`, with ", organic" added for organic crops.
- Geography: two-letter code.
- **Time period: taken from the server clock** (current year − 3 to the current year), not from the template.

**Reference product and by-products**
- The reference product is 1 kg, with no properties: no dry mass, no carbon, no price.
- By-products are written in output group 2, but with no properties, so there is no allocation basis.

**Exchanges**
- About 200 intermediate exchanges are hard-coded and matched **by name** to the Master Data XML files in the deployment folder.
- Elementary flows are matched on hard-coded subcompartment UUIDs plus the flow name.
- A missing name or a unit mismatch is reported only on stdout, and the exchange is dropped.

**Uncertainty**
- Always lognormal, with one fixed pedigree per category.
- The template's data-quality scores are ignored.

**Activity links**
- Only for photovoltaic and wind electricity. All other inputs go to the market.

**Hard-coded proxies**
- Seeds of other crops, e.g. sesame → linseed seed. The sesame key does not match, so sesame always gets 0 seed.
- Solid pig manure → liquid pig manure.
- Solar heat → fossil heat.
- Copper fungicide → copper oxide at 1:1.
- Bromofenoxim and fenoxaprop: the keys do not match, so their product inputs are dropped.

## 7. Code compared with the 2019 description

| Topic | Description | Code (`master`) | `legacy-fixes` |
|---|---|---|---|
| NOx | 0.0187 kg NOx-N/kg N, applied to N net of NH3 | Same factor, applied to gross N (the EEA value itself is 0.0122) | F1 |
| N2O | Includes N_som and EF1FR 0.003 for flooded rice | Neither | F2 |
| NO3 supply S | Mineral N + soluble organic N − (NH3 + NOx + N2O) | All organic N; 0.99 × NH3-N; no NOx | F3, D1 |
| HM accumulation factor | 1.86 | 0.86 | F4 |
| HM soil balance | (inputs + deposition − outputs) × A | A × inputs − allocated outputs; harvest not allocated | F4 |
| HM plant export | Crop-specific values (Tab. 5) | Generic mean for every crop | F4b |
| Crop-specific LUC as default | Yes | Data for almond only | — |
| CH4 (biogenic), e.g. rice | Listed among the emissions | Not modelled | — |
| Land-management changes in soil carbon | Described (2.9.2.2) | Not modelled | — |
| C uptake default (47.5 % C) | Yes | Table per crop | — |
| Irrigation emissions | ecoinvent irrigation report | Country ratio tables (14 countries + GLO) | — |

## 8. Critical issues and limitations

### A. Wrong numbers (the method is clear, the code does something else)

| # | Issue | Status |
|---|---|---|
| A1 | NH3 from compost and sludge in kg N, summed with kg NH3 | F5 |
| A2 | NOx +53 % and not net of NH3 | F1 |
| A3 | NO3 supply term S | F3 |
| A4 | Annual vs per-cycle mix in SQCB | D1 |
| A5 | HM: manure input 1000 × too low; accumulation factor 0.86; deposition term missing; export not allocated | F4, F4d |
| A6 | Fertiliser Zn "other" counted as Pb; lime per kg CaO applied to kg Ca | F4c |
| A7 | Seed HM uses numbers of trees or seedlings as kg | Open |
| A8 | Copper fungicide counted twice in soil (direct emission + HM balance) | Open |
| A9 | Negative R factor, so negative erosion, at low precipitation | Open |
| A10 | Groundwater utility water written as `Water, river` | Open (check the F9 alignment table) |
| A11 | Sesame seed key mismatch; bromofenoxim and fenoxaprop product inputs dropped | Java side pending (F6/F9) |
| A12 | LUC unit kg vs ha | Flagged in F9 |

### B. Missing processes

| # | Issue | Status |
|---|---|---|
| B1 | No CH4 from flooded rice | L66 (IPCC 2019 Tier 1, `ch4_rice_air`) |
| B2 | No N_som / N2O from soil carbon losses; no land-management soil-carbon changes | N_som hook in F2 (input defaults to 0) |
| B3 | Rice had no land occupation or transformation | F7 |
| B4 | Unspecified pesticides: product input but no emission | Open |
| B5 | P from compost and from dehydrated or dried sludge ignored | Open |
| B6 | By-products: no carbon uptake and no allocation properties | Open |
| B7 | No pesticide fate (100 % to soil); no emissions to air or water | Open (method choice) |

### C. Defaults and data

| # | Issue | Status |
|---|---|---|
| C1 | Template pre-filled 0s disable the fertiliser, manure and pesticide defaults, while blank water triggers the default irrigation | Open |
| C2 | Default irrigation makes almost every crop "irrigated" | Open |
| C3 | Seed default tables are partial; a missing entry silently gives 0 seed | Open |
| C4 | LUC is in practice shared-responsibility only; country table frozen (FAOSTAT up to 2012); 39 countries | Open |
| C5 | Unsourced P loss rates for vegetables, fruit trees and viticulture; legacy constants spread over Python dictionaries | Partly moved to CSV in F8 and F4 |
| C6 | Country coverage limited to 39 hard-coded countries; `CS` = Serbia (obsolete code) | Open |
| C7 | Greenhouse lifetime = orchard lifetime (20 years) | Open |

### D. Architecture and ecoinvent integration

| # | Issue | Status |
|---|---|---|
| D1 | Product and flow names hard-coded in Java and matched by name; failures only on stdout | F9 review tables |
| D2 | ecoinvent version set by whatever Master Data XML is deployed on the server | config.py + agritool.cfg (F6, F9) |
| D3 | Logic split between Java and Python (pesticide remainders in Java; unit conversions in Python; crop list duplicated) | Open |
| D4 | Defaults invisible to the user and in the dataset | Open |
| D5 | Time period taken from the server clock; no ISIC/CPC classification, no technology text, no reference-product properties | Open |
| D6 | Fixed pedigree per category; data-quality scores and sources from the template ignored | Open |
| D7 | Closed-source Quantis libraries; single-threaded Python server; no timeouts; unauthenticated account-creation endpoint | Open (obsolete if rewritten) |

## 9. Points to carry into AgriTool V.1

- **One engine.** Read the template, compute and write the dataset in one language, with no Java/Python contract to keep in sync.
- **Explicit defaults.** Every default must be traceable: value, source, and a flag in the output and in the dataset comment.
- **Master Data by UUID.** Product and flow identities come from the Master Data of the target release. Failures stop the run with a report; nothing is dropped silently.
- **One time base.** Declare annual vs per-cycle quantities once, and convert in one place.
- **Units carried with values.** Reading units from the template would have prevented A1, A5 and A7.
- **Regression cases with reference values.** Keep the three cases on `legacy-fixes` as a baseline for comparing the old and new versions.
- **Method gaps to close.** Rice CH4, N_som, pesticide emissions for "other", by-product allocation, and a policy for crop-specific vs shared-responsibility LUC.

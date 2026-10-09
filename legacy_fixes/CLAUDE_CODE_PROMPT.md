# Task: fix verified code–documentation discrepancies in sri-crop-tool

Context: `docs/legacy_analysis.md` lists discrepancies between the legacy code and
Quantis (2019) *Models integrated in ecoinvent LCI calculation tool for crop production*.
`legacy_fixes/` contains the specification of the corrected models:
`reference_models.py` (corrected equations), `data/*.csv` (parameters and tables with
sources, see `data/SOURCES.md`) and `test_reference_models.py` (22 tests).

## Paths

- Legacy repository to fix: `C:\python\sri-crop-tool`
- Specification package (read-only, do not edit): `C:\python\AgriToolV.1\legacy_fixes`
- Legacy analysis: `C:\python\AgriToolV.1\docs\legacy_analysis.md`
- ecoinvent Master Data v3.12: `C:\python\external_data\MasterData_3_12.xlsx`
  (outside any git repository; read it from a config setting, never copy it into a repo)
- Copy the CSV files the legacy code needs from `legacy_fixes\data` into
  `sri-crop-tool\data` and read them from there.

Work in a new branch `legacy-fixes` of `sri-crop-tool`; keep the tag `v1-legacy` untouched.
Reply to me in Italian in chat; code, docstrings, comments and commit messages in English.
Start in plan mode.

## Steps

1. For each fix, locate the code (file, function, lines) and show me the current
   implementation next to the reference one before editing.
2. Before changing anything, add a regression test on 2-3 reference cases that records the
   CURRENT output, so every numerical change is visible.
3. One fix per commit, with `reference_models.py` as specification. Constants go to the
   CSV files in `data/`, never hardcoded.
4. After each commit, report old vs new values on the reference cases.

## Fixes (apply directly)

- F1 NOx: 0.012174 kg NOx-N/kg N (EEA 2016 Tab. 3.1: 0.04 kg NO2/kg N) on
  (N applied − NH3-N), then × 46/14. Document it as a deviation from Quantis (0.018667).
- F2 N2O: add N_som = SOC loss / C:N (15 LUC from forest/grassland, 11 cropland) from the
  SOC change of the LUC / land-management block, in the field N2O only (SALCAfieldN Eq. 5).
  If the LUC block already reports N2O from SOC mineralisation, remove it there and show me
  the change; EF1FR = 0.003 for flooded rice
  on the direct term only; volatilised N only in the indirect term.
- F3 NO3: S = N_min + soluble N_org − (NH3-N + NOx-N + direct N2O-N); remove the 0.99
  factor. Check that clay enters as % (Annex 1 gives a ratio).
- F4 Heavy metals:
  - accumulation factor 1.86;
  - plant contents from Tab. 5 (CSV), NA = 0;
  - compound/"other" fertilisers via the Tab. 6 generic means, keyed by metal name
    (fix Zn counted as Pb);
  - all inputs in mg (manure: kg FM × DM × mg/kg DM);
  - deposition and leaching scaled by the occupation period;
  - A_i applied exactly once to each output (see `heavy_metals`). Check whether the legacy
    code applies it twice to leaching and erosion and report it.
- F5 NH3 from compost and sewage sludge: × 17/14.
- F6 Seeds/seedlings via ecoinvent Master Data v3.12:
  1. Read the IntermediateExchanges sheet of the local Master Data xlsx with
     `load_intermediate_exchanges` (path from config; file kept out of git).
  2. `data/seed_exchange_mapping.csv` already holds proposals for 72 crops, all verified
     against MD v3.12. Compare it with the crop names used by the template and the legacy
     code; add any missing crop as `proposed` using `suggest_seed_exchanges`.
  3. Replace the legacy lookup with `resolve_seed_exchange`, passing the unit of the
     template amount. The run must stop on unmapped or unreviewed crops and on unit
     mismatches (seedlings are in 'unit'). UUIDs always come from the master data.
  4. List the 15 crops that were losing seeds and the rows I must confirm.
- F7 Rice: land occupation computed like other crops, with the flooded-crop flows from
  `data/ecoinvent_flows_md312.csv` (Occupation, annual crop, flooded crop, 7956039f-...).
- F8 Phosphorus (now sourced, Prasuhn 2006 / SALCAfieldP 2023):
  - drainage factor kd = 6 applies only to the drained share, going to surface water;
  - run-off is zero for slopes ≤ 3 % when the slope is known;
  - move both values to `model_parameters.csv` and replace the hardcoded ones;
  - show me how the legacy code currently splits ground water and drainage.
- F9 Elementary flows: compare every flow written to the ecoSpold output (name,
  compartment, UUID) with `data/ecoinvent_flows_md312.csv` and report the differences. Do not
  choose between Chromium III/VI or Copper/Copper ion: show me what the legacy code uses.

## Ask me before implementing

- D1 NO3 per crop cycle: proposed rule in `nitrate_leaching` (intercept and N_org term
  scaled by the occupation period, S and U as cycle totals). Show me first how cycles and
  irrigation are defined in the Excel template.
- D5 Drained fraction: one input (`drained_fraction`, default 0) is now used for NO3,
  phosphate and heavy-metal leaching. Show me whether and how the template provides it.

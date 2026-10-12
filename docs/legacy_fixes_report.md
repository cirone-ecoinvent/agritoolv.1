# Legacy fixes F1-F9: report

> Moved on 2026-10-09 (decision M1, docs/DECISIONS.md): the code, data, tests and scripts
> described here now live in AgriToolV.1 (`src/legacy_model`, `data`, `tests/legacy_model`,
> `scripts`). Commit hashes below refer to the former local branch `legacy-fixes` of
> sri-crop-tool. Paths `src/main/python/...` correspond to `src/legacy_model/...`.

Branch `legacy-fixes` of `C:\python\sri-crop-tool` (13 commits on top of tag `v1-legacy` =
master `a0a434a`). Specification: `C:\python\AgriToolV.1\legacy_fixes` (unchanged, hash verified).
Python only; the Java edits are listed in `java_changes_pending.md`. All tests run with
`C:\python\AgriToolV.1\.venv` (22 specification tests, 65 branch tests, all green).

How to run:

```
cd C:\python\sri-crop-tool
C:\python\AgriToolV.1\.venv\Scripts\python -m pytest src/test/python --import-mode=importlib -q
C:\python\AgriToolV.1\.venv\Scripts\python scripts/compare_regression.py --markdown
```

## 1. Commits

| Commit | Fix | Files | Numerical effect on the 3 cases |
|---|---|---|---|
| `9dbf8cc` | setup | `data/` (spec CSVs + `sources.csv`), `dataloader.py`, `config.py` | none |
| `0e9d655` | regression baseline | `src/test/python/regression_*`, `scripts/compare_regression.py` | none |
| `8559058` | F5 NH3 compost/sludge x 17/14 | `otherorganicfertilisermodel.py`, `data/organic_fertiliser_nh3.csv` | apple_FR NH3 +3.4 % |
| `041717b` | F1 NOx 0.04 kg NO2/kg net N | `nmodel.py` | NOx x 0.54-0.62 |
| `8947bb3` | F3 NO3 supply S, clay check | `nmodel.py`, `manuremodel.py`, `otherorganicfertilisermodel.py`, `modelsSequence.py`, `data/manure_nh3.csv` | NO3 -3 to -7 % |
| `74b271f` | D1 NO3 per cycle | `nmodel.py` | NO3 -4 % (wheat, t = 0.79), +5 % (rice, t = 0.42) |
| `c81b138` | F2 N2O terms, N_som, EF1FR | `nmodel.py`, `defaultGeneration.py` | rice N2O x 0.48 |
| `c03a981` | F8 phosphorus | `pmodel.py`, `defaultGeneration.py`, `data/p_landuse_classes.csv`, `model_parameters.csv` | none |
| `5705e70` | F4a+b HM balance, 1.86, Tab. 5 export | `hmmodel.py`, `defaultGeneration.py`, `data/hm_crop_product_mapping.csv`, `hm_pesticide_fungicides.csv` | all HM keys |
| `6e1c83f` | F4c mineral fertilisers Tab. 6 | `fertilisermodel.py`, `data/hm_fertiliser_row_mapping.csv` | Hg only |
| `3a52072` | F4d manure in mg | `manuremodel.py`, `outputMapping.py`, `data/hm_manure_class_mapping.csv` | all HM keys |
| `12a254d` | F7 rice occupation | `lucmodel.py`, `outputMapping.py`, `nmodel.py`, `data/crop_types.csv` | rice gains 3 land flows |
| `df6b665` | F6 seeds (Python side) | `seedexchanges.py`, `outputMapping.py`, `data/crop_key_aliases.csv` | status key only |

## 2. Checks requested in the prompt

- **F2, LUC block**: the legacy LUC module (`lucmodel.py`) reports only area-expansion ratios;
  it has no SOC change and no N2O, so nothing had to be removed. `N_som` is 0 unless the new
  input `soc_change_kg_c` is supplied (the template has no such field).
- **F3, clay**: the country tables give clay as a fraction (e.g. IT 0.301); the regression
  multiplies by 100 as documented; a value >= 1 now raises `ValueError`.
- **F4, allocation factor "applied twice?"**: the legacy code applied `A` once to leaching and
  erosion (`m_leach x A`, `c_soil x Ser x 0.86 x 0.2 x A`) but its soil balance was
  `M_agro x A - leaching - erosion`: compared with the Freiermuth form
  `(inputs + deposition - raw outputs) x A = M_agro - allocated outputs` it dropped the
  deposition term `dep x t x A`, and the harvest export was subtracted without `A`. Now `A` is
  applied exactly once to each output (test `test_balance_equals_freiermuth_form`).
- **F8, legacy split**: `PO4 x (1 - drained)` to ground water, `PO4 x drained x 6` to surface
  water, i.e. kd already acted on the drained share only; run-off was zero only for rice
  (default slope 0 vs threshold `< 0.03`). No numerical change.
- **F6, crops that were losing seeds** (Java variable names not matching the Python keys):
  asparagus_green, asparagus_white, cabbage_red, cabbage_white, coffee_arabica, coffee_robusta,
  lemon, citruslime, orange_fresh, orange_processing, strawberry_fresh, strawberry_processing,
  tomato_fresh, tomato_processing, sesame_seed (15 of 67). With F6 the exchange name comes
  from the mapping, so the Java static names are no longer needed.

## Update 2026-10-09: Master Data 3.12 available

`C:\python\external_data\MasterData (3.12, undef).xlsx` is configured in the git-ignored
`sri-crop-tool\agritool.cfg`. Results (commits `056c0f4`, `6a6bcc9`):

- Seed mapping: all 29 exchange names exist in the Master Data with the mapped unit.
- Elementary flows: 402 checked, 364 exact, 23 renamed to the Master Data spelling, 15 open
  (Chromium III/VI, 8 pesticide proposals, Cyfluthrin, Pyrethrine, Pyrethrum, Metiram).
- Intermediate exchanges: 587 checked, 543 exact, 44 open (mineral fertilisers, lime,
  ammonia, transport, triazine-compound, cotton seed); LUC exchange unit is ha, not kg.
- Review tables and the review procedure: `data/*_alignment.csv`, `scripts/review_status.py`.
  Sections 3 and 4 below describe the state before the Master Data was available.

## 3. F6: rows of `seed_exchange_mapping.csv` to confirm

No row has status `confirmed` yet, so with the Master Data configured every run would stop
until the rows are reviewed. Grouped by what is needed:

| Group | Rows | Action |
|---|---|---|
| `proposed`, direct exchange | wheat, barley, rye, oat, rice (CPC note), maize_grain, sugar_beet, potato ("for setting"), rapeseed, sunflower, soybean, cotton, linseed, lentil, peanut, faba_beans, protein_peas, carrot, onion, tomato_fresh_grade, tomato_processing_grade, strawberry_fresh_grade, strawberry_processing_grade, mint | set `confirmed` (and `reviewed_by`) |
| `to_decide`, proxy or amortisation | sweet_corn (maize seed proxy), flax (linseed), green/white asparagus, mango (perennial seedlings), grass, sesame_seed | decide exchange or `no_exchange` |
| `to_decide`, tree crops | almond, apple, apricot, peach, pear, lemon, citrus_lime, mandarin, orange_*_grade, pomegranate (candidate "fruit tree seedling, for planting"); cashew, olive, cocoa, coconut, palm_tree, coffee_*, tea (candidate "tree seedling, for planting"); banana, grape, blueberry, cranberry, raspberry, mulberry, pineapple (no specific exchange) | decide; note that the legacy writer also added "planting tree" and "establishing orchard" per tree, which the mapping does not cover |
| `no_exchange` | chick_pea, sugar_cane, cassava, bell_pepper, chilli, eggplant, cabbage_red/white, coriander, ginger, turmeric, guar, hemp, castor_bean, pearl_millet | already usable (no seed input) |

Legacy crops not in the mapping: none (16 spelling aliases in `crop_key_aliases.csv`;
barley, rye, faba_beans, protein_peas, grass exist only in the mapping).

Still to run when `C:\python\external_data\MasterData_3_12.xlsx` is available (set
`AGRITOOL_MASTER_DATA_PATH` or `agritool.cfg`): `seedexchanges.validate_seed_mapping` against
the real sheet (column names `id`, `name`, `unitName` assumed in `dataloader.load_intermediate_exchanges`;
adjust if the sheet differs), and the UUID comparison of section 4.

## 4. F9: elementary flows written by the ecoSpold writer vs Master Data v3.12

Source: `EcospoldTemplateSubstanceUsages.java` (+ pesticide substances from
`ecospold_pesticides_substance_mapping.properties`) vs `data/ecoinvent_flows_md312.csv`. The
writer resolves UUIDs at runtime from `ElementaryExchanges.xml` (version unknown); UUIDs can
only be compared once the Master Data file is available.

| Tool flow | Legacy name (writer) | Compartment (writer) | MD v3.12 name(s) | Status |
|---|---|---|---|---|
| NH3 | Ammonia | air / non-urban | Ammonia `0f440cc0-...` | name identical |
| N2O | Dinitrogen monoxide | air / non-urban | Dinitrogen monoxide `afd6d670-...` | identical |
| NOx | Nitrogen oxides | air / non-urban | Nitrogen oxides `77357947-...` | identical |
| CO2 urea/lime | Carbon dioxide, fossil | air / non-urban | Carbon dioxide, fossil `aa7cac3a-...` | identical |
| NO3 | Nitrate | water / ground-; surface | Nitrate `b9291c72-...`, `7ce56135-...` | identical |
| PO4 | Phosphate | water / ground-; surface | Phosphate `329fc7d8-...`, `1727b41d-...` | identical |
| P erosion | Phosphorus | water / surface | Phosphorus `b2631209-...` | identical |
| Cd | Cadmium, ion (water); Cadmium (soil) | water ground-/surface; soil agricultural | Cadmium II | **rename** |
| Cr | Chromium, ion (water); Chromium (soil) | idem | Chromium III **or** Chromium VI (both exist in all three compartments) | **user decision** |
| Cu | Copper, ion (water); Copper (soil) | idem | ground water: only "Copper ion"; surface water and soil: "Copper ion" and "Copper" both exist | **user decision** |
| Pb | Lead | idem | Lead II | **rename** |
| Hg | Mercury | idem | Mercury II | **rename** |
| Ni | Nickel, ion (water); Nickel (soil) | idem | Nickel II | **rename** |
| Zn | Zinc, ion (water); Zinc (soil) | idem | Zinc II | **rename** |
| rice land use | (none) | natural resource / land | Occupation / Transformation, annual crop, flooded crop | added on the Python side (F7), Java pending |
| not in the CSV | Carbon dioxide, in air; Energy, gross calorific value, in biomass; Water, river; Occupation / Transformation (irrigated, non-irrigated, greenhouse, permanent); Water (air, surface, ground); COD, DOC, TOC, BOD5 (ground water); Mineral oil (soil); pesticide active ingredients (soil) | | | not verifiable with the current CSV |

Legacy names for the metals are the ecoinvent 3.4-era names; the writer would silently drop
these flows against a 3.12 master data file (lookup by name returns null).

## 5. Assumptions and open items

- Stoichiometric conversions use the exact atomic masses of `atomicmass.py` (17.0306/14.0067 =
  1.2159) while the reference uses 17/14 (1.2143): +0.13 % on NH3, similar on NO2, NO3, N2O.
- F3 soluble organic N: manure TAN taken from the legacy "TAN x EF" products split into
  `manure_nh3.csv` (unsourced legacy values); the "other" manure categories cannot be split and
  fall back to total N; compost and sludge TAN from the Agribalyse values in the legacy code.
- F2 `N_som` needs a SOC change that the legacy tool does not compute (`soc_change_kg_c` = 0).
- F4c drops the legacy Agribalyse Hg contents of mineral fertilisers (Tab. 6 has no Hg).
- F4 manure: liquid manure converted with the legacy density 1006 kg/m3 and the 50 %
  "undiluted share" default; Tab. 7 class shares are legacy assumptions.
- F4 harvest export: main product only, Tab. 5 product mapping for 8 crops, generic mean for the
  other 59 (plausibility flags of `SOURCES.md` apply, e.g. rape seed Cd 1.6).
- F8 extra land-use classes (vegetables, viticulture, fruit trees, alpine pastures) keep the
  legacy values, flagged unsourced in `p_landuse_classes.csv`.
- Java writer not rebuilt; see `java_changes_pending.md`.

## 6. Cumulative old vs new on the reference cases (legacy baseline `0e9d655` -> `df6b665`)

Heavy-metal keys are listed in full in the per-commit tables printed during the work; here the
complete diff of the three snapshots.

### apple_FR (33 changed keys)

| key | legacy | fixed | ratio |
|---|---|---|---|
| `N2o_air` | 2.429 | 2.389 | 0.984 |
| `Nox_as_n2o_air` | 7.329 | 4.521 | 0.617 |
| `ammonia_total` | 7.583 | 7.838 | 1.034 |
| `heavymetal_to_ground_water_cd` | 3.349e-05 | 3.412e-05 | 1.019 |
| `heavymetal_to_ground_water_cr` | 0.01726 | 0.01742 | 1.010 |
| `heavymetal_to_ground_water_cu` | 0.003237 | 0.003237 | 1.000 |
| `heavymetal_to_ground_water_hg` | 9.448e-07 | 1.072e-06 | 1.135 |
| `heavymetal_to_ground_water_pb` | 0.0004235 | 0.0004277 | 1.010 |
| `heavymetal_to_ground_water_zn` | 0.02189 | 0.0237 | 1.083 |
| `heavymetal_to_soil_cd` | 0.001471 | 0.002142 | 1.456 |
| `heavymetal_to_soil_cr` | 0.01128 | 0.01736 | 1.540 |
| `heavymetal_to_soil_cu` | 2.911 | 2.935 | 1.008 |
| `heavymetal_to_soil_hg` | 0.0001664 | 0.0005431 | 3.264 |
| `heavymetal_to_soil_minus_uptake_cd` | 0.0009344 | 0.001741 | 1.863 |
| `heavymetal_to_soil_minus_uptake_cr` | 0.008396 | 0.01471 | 1.752 |
| `heavymetal_to_soil_minus_uptake_cu` | 2.876 | 2.9 | 1.008 |
| `heavymetal_to_soil_minus_uptake_hg` | -4.796e-05 | 0.0003494 | -7.285 |
| `heavymetal_to_soil_minus_uptake_ni` | 0.01353 | 0.02241 | 1.656 |
| `heavymetal_to_soil_minus_uptake_pb` | 0.04936 | 0.06714 | 1.360 |
| `heavymetal_to_soil_minus_uptake_zn` | -0.008368 | 0.192 | -22.938 |
| `heavymetal_to_soil_ni` | 0.01905 | 0.02702 | 1.418 |
| `heavymetal_to_soil_pb` | 0.05222 | 0.0694 | 1.329 |
| `heavymetal_to_soil_zn` | 0.1609 | 0.3269 | 2.032 |
| `heavymetal_to_surface_water_cd` | 1.103e-05 | 1.991e-05 | 1.804 |
| `heavymetal_to_surface_water_cr` | 0.002699 | 0.003643 | 1.350 |
| `heavymetal_to_surface_water_cu` | 0.001613 | 0.003071 | 1.904 |
| `heavymetal_to_surface_water_hg` | 2.095e-06 | 5.005e-06 | 2.389 |
| `heavymetal_to_surface_water_ni` | 0.0006472 | 0.00144 | 2.225 |
| `heavymetal_to_surface_water_pb` | 0.0006721 | 0.001413 | 2.102 |
| `heavymetal_to_surface_water_zn` | 0.004086 | 0.006506 | 1.592 |
| `nitrate_to_groundwater` | 141.4 | 131.5 | 0.930 |
| `nitrate_to_surfacewater` | 15.71 | 14.61 | 0.930 |
| `seed_exchange_status` | None | 'master data not configured: legacy seed lookup' |  |

### rice_IN (35 changed keys)

| key | legacy | fixed | ratio |
|---|---|---|---|
| `N2o_air` | 4.019 | 1.917 | 0.477 |
| `Nox_as_n2o_air` | 8.874 | 4.782 | 0.539 |
| `heavymetal_to_ground_water_cd` | 1.826e-05 | 1.839e-05 | 1.007 |
| `heavymetal_to_ground_water_cr` | 0.008309 | 0.00837 | 1.007 |
| `heavymetal_to_ground_water_cu` | 0.001302 | 0.001455 | 1.118 |
| `heavymetal_to_ground_water_hg` | 4.185e-07 | 5.025e-07 | 1.201 |
| `heavymetal_to_ground_water_pb` | 5.647e-05 | 8.671e-05 | 1.535 |
| `heavymetal_to_ground_water_zn` | 0.007408 | 0.01168 | 1.577 |
| `heavymetal_to_soil_cd` | 0.001756 | 0.002084 | 1.187 |
| `heavymetal_to_soil_cr` | 0.009616 | 0.00871 | 0.906 |
| `heavymetal_to_soil_cu` | 0.0007388 | 0.02209 | 29.898 |
| `heavymetal_to_soil_hg` | 4.241e-05 | 0.0002357 | 5.558 |
| `heavymetal_to_soil_minus_uptake_cd` | 0.001314 | 0.002007 | 1.527 |
| `heavymetal_to_soil_minus_uptake_cr` | 0.007248 | 0.006693 | 0.923 |
| `heavymetal_to_soil_minus_uptake_cu` | -0.02806 | -0.000123 | 0.004 |
| `heavymetal_to_soil_minus_uptake_hg` | -0.0001338 | 0.0002357 | -1.762 |
| `heavymetal_to_soil_minus_uptake_ni` | -0.004719 | -0.001104 | 0.234 |
| `heavymetal_to_soil_minus_uptake_pb` | -0.002818 | -0.0004694 | 0.167 |
| `heavymetal_to_soil_minus_uptake_zn` | -0.1285 | 0.02 | -0.156 |
| `heavymetal_to_soil_ni` | -0.0001805 | 0.002389 | -13.239 |
| `heavymetal_to_soil_pb` | -0.0004684 | 0.0009772 | -2.086 |
| `heavymetal_to_soil_zn` | 0.01068 | 0.1821 | 17.047 |
| `heavymetal_to_surface_water_cd` | 4.421e-05 | 9.629e-05 | 2.178 |
| `heavymetal_to_surface_water_cr` | 0.004763 | 0.01038 | 2.178 |
| `heavymetal_to_surface_water_cu` | 0.003666 | 0.00886 | 2.417 |
| `heavymetal_to_surface_water_hg` | 1.185e-05 | 3.077e-05 | 2.597 |
| `heavymetal_to_surface_water_ni` | 0.003221 | 0.008664 | 2.689 |
| `heavymetal_to_surface_water_pb` | 0.0009255 | 0.003073 | 3.321 |
| `heavymetal_to_surface_water_zn` | 0.005615 | 0.01915 | 3.411 |
| `luc_crop_type` | 'Paddy rice' | 'annual' |  |
| `nitrate_to_groundwater` | 219.7 | 225.5 | 1.026 |
| `occupation_annual_flooded` | None | 4167 |  |
| `seed_exchange_status` | None | 'master data not configured: legacy seed lookup' |  |
| `transformation_from_annual_flooded` | None | 1e+04 |  |
| `transformation_to_annual_flooded` | None | 1e+04 |  |

### wheat_IT (32 changed keys)

| key | legacy | fixed | ratio |
|---|---|---|---|
| `N2o_air` | 5.067 | 4.995 | 0.986 |
| `Nox_as_n2o_air` | 12.02 | 6.795 | 0.565 |
| `heavymetal_to_ground_water_cd` | 2.563e-05 | 2.567e-05 | 1.002 |
| `heavymetal_to_ground_water_cr` | 0.01087 | 0.01092 | 1.005 |
| `heavymetal_to_ground_water_cu` | 0.001682 | 0.00189 | 1.124 |
| `heavymetal_to_ground_water_hg` | 4.881e-07 | 6.568e-07 | 1.346 |
| `heavymetal_to_ground_water_pb` | 3.808e-05 | 8.039e-05 | 2.111 |
| `heavymetal_to_ground_water_zn` | 0.01181 | 0.01422 | 1.204 |
| `heavymetal_to_soil_cd` | 0.006256 | 0.006876 | 1.099 |
| `heavymetal_to_soil_cr` | 0.01459 | 0.01623 | 1.113 |
| `heavymetal_to_soil_cu` | 0.003938 | 0.02597 | 6.596 |
| `heavymetal_to_soil_hg` | 4.904e-05 | 0.0003887 | 7.927 |
| `heavymetal_to_soil_minus_uptake_cd` | 0.005695 | 0.006364 | 1.117 |
| `heavymetal_to_soil_minus_uptake_cr` | 0.01158 | 0.01521 | 1.314 |
| `heavymetal_to_soil_minus_uptake_cu` | -0.03268 | 0.008701 | -0.266 |
| `heavymetal_to_soil_minus_uptake_hg` | -0.000175 | 0.0003384 | -1.933 |
| `heavymetal_to_soil_minus_uptake_ni` | -0.0009949 | 0.007222 | -7.259 |
| `heavymetal_to_soil_minus_uptake_pb` | -0.003122 | 0.002973 | -0.952 |
| `heavymetal_to_soil_minus_uptake_zn` | -0.1139 | 0.128 | -1.124 |
| `heavymetal_to_soil_ni` | 0.004777 | 0.008052 | 1.686 |
| `heavymetal_to_soil_pb` | -0.0001342 | 0.00324 | -24.150 |
| `heavymetal_to_soil_zn` | 0.063 | 0.2187 | 3.471 |
| `heavymetal_to_surface_water_cd` | 4.071e-05 | 7.54e-05 | 1.852 |
| `heavymetal_to_surface_water_cr` | 0.007645 | 0.01117 | 1.461 |
| `heavymetal_to_surface_water_cu` | 0.00299 | 0.006325 | 2.115 |
| `heavymetal_to_surface_water_hg` | 6.833e-06 | 1.956e-05 | 2.862 |
| `heavymetal_to_surface_water_ni` | 0.002145 | 0.005001 | 2.332 |
| `heavymetal_to_surface_water_pb` | 0.0003154 | 0.0014 | 4.438 |
| `heavymetal_to_surface_water_zn` | 0.009348 | 0.01726 | 1.847 |
| `nitrate_to_groundwater` | 135.9 | 123.6 | 0.910 |
| `nitrate_to_surfacewater` | 58.24 | 52.99 | 0.910 |
| `seed_exchange_status` | None | 'master data not configured: legacy seed lookup' |  |

## 7. Heavy metals on SALCAheavymetal 2023 (decision L10, 2026-10-10)

Old vs new outputs of the three reference cases after each of the commits that switched the
heavy-metal model from Quantis 2019 / Freiermuth 2006 to SALCAheavymetal V1.0 (Nemecek et al.
2023, Appendix 7, Table 1). Values in kg per ha and crop cycle; ratio = new / old. Step 8
(ed6b10a, removal of the old tables) changed no output.

### Step 1: Deposition, leaching and soil contents (commit 9a1699e)

**apple_FR** (25 changed keys)

| key | old | new | ratio new/old |
|---|---|---|---|
| `heavymetal_to_ground_water_cd` | 3.41222e-05 | 3.54823e-05 | 1.0399 |
| `heavymetal_to_ground_water_cu` | 0.00323736 | 0.003214 | 0.9928 |
| `heavymetal_to_ground_water_pb` | 0.000427727 | 0.000468914 | 1.0963 |
| `heavymetal_to_ground_water_zn` | 0.0237005 | 0.0257488 | 1.0864 |
| `heavymetal_to_soil_cd` | 0.00214177 | 0.00213945 | 0.9989 |
| `heavymetal_to_soil_cr` | 0.0173607 | 0.0173733 | 1.0007 |
| `heavymetal_to_soil_cu` | 2.93518 | 2.92926 | 0.9980 |
| `heavymetal_to_soil_hg` | 0.000543123 | 0.000541663 | 0.9973 |
| `heavymetal_to_soil_minus_uptake_cd` | 0.00174102 | 0.00172273 | 0.9895 |
| `heavymetal_to_soil_minus_uptake_cr` | 0.0147061 | 0.0147187 | 1.0009 |
| `heavymetal_to_soil_minus_uptake_cu` | 2.90033 | 2.89466 | 0.9980 |
| `heavymetal_to_soil_minus_uptake_hg` | 0.000349363 | 0.000347903 | 0.9958 |
| `heavymetal_to_soil_minus_uptake_ni` | 0.0224092 | 0.0225096 | 1.0045 |
| `heavymetal_to_soil_minus_uptake_pb` | 0.0671403 | 0.0667514 | 0.9942 |
| `heavymetal_to_soil_minus_uptake_zn` | 0.191956 | 0.177363 | 0.9240 |
| `heavymetal_to_soil_ni` | 0.0270187 | 0.0269573 | 0.9977 |
| `heavymetal_to_soil_pb` | 0.0694009 | 0.0692296 | 0.9975 |
| `heavymetal_to_soil_zn` | 0.326913 | 0.323984 | 0.9910 |
| `heavymetal_to_surface_water_cd` | 1.9907e-05 | 2.08642e-05 | 1.0481 |
| `heavymetal_to_surface_water_cr` | 0.00364314 | 0.00363049 | 0.9965 |
| `heavymetal_to_surface_water_cu` | 0.00307125 | 0.00900988 | 2.9336 |
| `heavymetal_to_surface_water_hg` | 5.00493e-06 | 6.46432e-06 | 1.2916 |
| `heavymetal_to_surface_water_ni` | 0.00143986 | 0.00150134 | 1.0427 |
| `heavymetal_to_surface_water_pb` | 0.00141292 | 0.00154296 | 1.0920 |
| `heavymetal_to_surface_water_zn` | 0.00650601 | 0.00738638 | 1.1353 |

**rice_IN** (25 changed keys)

| key | old | new | ratio new/old |
|---|---|---|---|
| `heavymetal_to_ground_water_cd` | 1.83933e-05 | 1.87413e-05 | 1.0189 |
| `heavymetal_to_ground_water_cu` | 0.0014551 | 0.00114853 | 0.7893 |
| `heavymetal_to_ground_water_pb` | 8.67059e-05 | 0.00011975 | 1.3811 |
| `heavymetal_to_ground_water_zn` | 0.0116831 | 0.0124182 | 1.0629 |
| `heavymetal_to_soil_cd` | 0.00208389 | 0.00206946 | 0.9931 |
| `heavymetal_to_soil_cr` | 0.00871013 | 0.00681561 | 0.7825 |
| `heavymetal_to_soil_cu` | 0.0220897 | 0.0230104 | 1.0417 |
| `heavymetal_to_soil_hg` | 0.000235708 | 0.000228542 | 0.9696 |
| `heavymetal_to_soil_minus_uptake_cd` | 0.00200717 | 0.00199129 | 0.9921 |
| `heavymetal_to_soil_minus_uptake_cr` | 0.00669282 | 0.0047983 | 0.7169 |
| `heavymetal_to_soil_minus_uptake_cu` | -0.000122996 | 0.00547768 | -44.5355 |
| `heavymetal_to_soil_minus_uptake_hg` | 0.000235708 | 0.000228542 | 0.9696 |
| `heavymetal_to_soil_minus_uptake_ni` | -0.00110416 | -0.00271972 | 2.4632 |
| `heavymetal_to_soil_minus_uptake_pb` | -0.000469432 | -0.00296511 | 6.3164 |
| `heavymetal_to_soil_minus_uptake_zn` | 0.019999 | 0.00441336 | 0.2207 |
| `heavymetal_to_soil_ni` | 0.00238944 | 0.00064407 | 0.2695 |
| `heavymetal_to_soil_pb` | 0.000977239 | -0.000967107 | -0.9896 |
| `heavymetal_to_soil_zn` | 0.182071 | 0.176683 | 0.9704 |
| `heavymetal_to_surface_water_cd` | 9.62873e-05 | 0.000110373 | 1.1463 |
| `heavymetal_to_surface_water_cr` | 0.0103768 | 0.0122713 | 1.1826 |
| `heavymetal_to_surface_water_cu` | 0.00886043 | 0.00824625 | 0.9307 |
| `heavymetal_to_surface_water_hg` | 3.07715e-05 | 3.79375e-05 | 1.2329 |
| `heavymetal_to_surface_water_ni` | 0.00866359 | 0.010409 | 1.2015 |
| `heavymetal_to_surface_water_pb` | 0.00307328 | 0.00498458 | 1.6219 |
| `heavymetal_to_surface_water_zn` | 0.0191511 | 0.0238036 | 1.2429 |

**wheat_IT** (25 changed keys)

| key | old | new | ratio new/old |
|---|---|---|---|
| `heavymetal_to_ground_water_cd` | 2.56695e-05 | 2.59725e-05 | 1.0118 |
| `heavymetal_to_ground_water_cu` | 0.00188997 | 0.00128618 | 0.6805 |
| `heavymetal_to_ground_water_pb` | 8.0388e-05 | 0.000118274 | 1.4713 |
| `heavymetal_to_ground_water_zn` | 0.0142197 | 0.0155849 | 1.0960 |
| `heavymetal_to_soil_cd` | 0.00687588 | 0.00686654 | 0.9986 |
| `heavymetal_to_soil_cr` | 0.0162334 | 0.0150484 | 0.9270 |
| `heavymetal_to_soil_cu` | 0.0259736 | 0.0279259 | 1.0752 |
| `heavymetal_to_soil_hg` | 0.000388745 | 0.000384255 | 0.9885 |
| `heavymetal_to_soil_minus_uptake_cd` | 0.00636403 | 0.00634865 | 0.9976 |
| `heavymetal_to_soil_minus_uptake_cr` | 0.0152059 | 0.0140208 | 0.9221 |
| `heavymetal_to_soil_minus_uptake_cu` | 0.00870101 | 0.0161714 | 1.8586 |
| `heavymetal_to_soil_minus_uptake_hg` | 0.00033837 | 0.000333881 | 0.9867 |
| `heavymetal_to_soil_minus_uptake_ni` | 0.00722213 | 0.00635918 | 0.8805 |
| `heavymetal_to_soil_minus_uptake_pb` | 0.00297299 | 0.00179916 | 0.6052 |
| `heavymetal_to_soil_minus_uptake_zn` | 0.128046 | 0.114248 | 0.8922 |
| `heavymetal_to_soil_ni` | 0.00805166 | 0.00714455 | 0.8873 |
| `heavymetal_to_soil_pb` | 0.00324014 | 0.00219222 | 0.6766 |
| `heavymetal_to_soil_zn` | 0.218693 | 0.213597 | 0.9767 |
| `heavymetal_to_surface_water_cd` | 7.53972e-05 | 8.44319e-05 | 1.1198 |
| `heavymetal_to_surface_water_cr` | 0.0111728 | 0.0123578 | 1.1061 |
| `heavymetal_to_surface_water_cu` | 0.00632503 | 0.00497657 | 0.7868 |
| `heavymetal_to_surface_water_hg` | 1.95586e-05 | 2.40477e-05 | 1.2295 |
| `heavymetal_to_surface_water_ni` | 0.00500082 | 0.00590794 | 1.1814 |
| `heavymetal_to_surface_water_pb` | 0.0013999 | 0.00240994 | 1.7215 |
| `heavymetal_to_surface_water_zn` | 0.0172644 | 0.0209952 | 1.2161 |

### Step 2: Harvest export with Table 1 plant contents, co-products and pesticide term (2a3840a)

**apple_FR** (7 changed keys)

| key | old | new | ratio new/old |
|---|---|---|---|
| `heavymetal_to_soil_minus_uptake_cd` | 0.00172273 | 0.00168106 | 0.9758 |
| `heavymetal_to_soil_minus_uptake_cr` | 0.0147187 | 0.0145739 | 0.9902 |
| `heavymetal_to_soil_minus_uptake_cu` | 2.89466 | 2.75279 | 0.9510 |
| `heavymetal_to_soil_minus_uptake_hg` | 0.000347903 | 0.000251024 | 0.7215 |
| `heavymetal_to_soil_minus_uptake_ni` | 0.0225096 | 0.0230655 | 1.0247 |
| `heavymetal_to_soil_minus_uptake_pb` | 0.0667514 | 0.0665678 | 0.9972 |
| `heavymetal_to_soil_minus_uptake_zn` | 0.177363 | 0.190651 | 1.0749 |

**rice_IN** (0 changed keys)


**wheat_IT** (6 changed keys)

| key | old | new | ratio new/old |
|---|---|---|---|
| `heavymetal_to_soil_minus_uptake_cd` | 0.00634865 | 0.00661796 | 1.0424 |
| `heavymetal_to_soil_minus_uptake_cu` | 0.0161714 | 0.0145329 | 0.8987 |
| `heavymetal_to_soil_minus_uptake_hg` | 0.000333881 | 0.000323806 | 0.9698 |
| `heavymetal_to_soil_minus_uptake_ni` | 0.00635918 | 0.00651625 | 1.0247 |
| `heavymetal_to_soil_minus_uptake_pb` | 0.00179916 | 0.00193673 | 1.0765 |
| `heavymetal_to_soil_minus_uptake_zn` | 0.114248 | 0.12974 | 1.1356 |

### Step 3: Metal contents of pesticides (ca839bc)

**apple_FR** (0 changed keys)


**rice_IN** (0 changed keys)


**wheat_IT** (4 changed keys)

| key | old | new | ratio new/old |
|---|---|---|---|
| `heavymetal_to_ground_water_zn` | 0.0155849 | 0.0150888 | 0.9682 |
| `heavymetal_to_soil_minus_uptake_zn` | 0.12974 | 0.0902292 | 0.6955 |
| `heavymetal_to_soil_zn` | 0.213597 | 0.169231 | 0.7923 |
| `heavymetal_to_surface_water_zn` | 0.0209952 | 0.0203268 | 0.9682 |

### Step 4: Mineral-fertiliser heavy metals, Hg, Ca per kg Ca, Mg (f1d5dd7)

**apple_FR** (27 changed keys)

| key | old | new | ratio new/old |
|---|---|---|---|
| `heavymetal_to_ground_water_cd` | 3.54823e-05 | 3.54797e-05 | 0.9999 |
| `heavymetal_to_ground_water_cr` | 0.017425 | 0.0174247 | 1.0000 |
| `heavymetal_to_ground_water_cu` | 0.003214 | 0.003214 | 1.0000 |
| `heavymetal_to_ground_water_hg` | 1.07237e-06 | 1.08132e-06 | 1.0083 |
| `heavymetal_to_ground_water_pb` | 0.000468914 | 0.000468915 | 1.0000 |
| `heavymetal_to_ground_water_zn` | 0.0257488 | 0.0257491 | 1.0000 |
| `heavymetal_to_soil_cd` | 0.00213945 | 0.00213872 | 0.9997 |
| `heavymetal_to_soil_cr` | 0.0173733 | 0.0173664 | 0.9996 |
| `heavymetal_to_soil_cu` | 2.92926 | 2.92927 | 1.0000 |
| `heavymetal_to_soil_hg` | 0.000541663 | 0.00060209 | 1.1116 |
| `heavymetal_to_soil_minus_uptake_cd` | 0.00168106 | 0.00168036 | 0.9996 |
| `heavymetal_to_soil_minus_uptake_cr` | 0.0145739 | 0.014567 | 0.9995 |
| `heavymetal_to_soil_minus_uptake_cu` | 2.75279 | 2.75279 | 1.0000 |
| `heavymetal_to_soil_minus_uptake_hg` | 0.000251024 | 0.000309024 | 1.2311 |
| `heavymetal_to_soil_minus_uptake_ni` | 0.0230655 | 0.0230603 | 0.9998 |
| `heavymetal_to_soil_minus_uptake_pb` | 0.0665678 | 0.0665693 | 1.0000 |
| `heavymetal_to_soil_minus_uptake_zn` | 0.190651 | 0.190675 | 1.0001 |
| `heavymetal_to_soil_ni` | 0.0269573 | 0.0269519 | 0.9998 |
| `heavymetal_to_soil_pb` | 0.0692296 | 0.0692311 | 1.0000 |
| `heavymetal_to_soil_zn` | 0.323984 | 0.324009 | 1.0001 |
| `heavymetal_to_surface_water_cd` | 2.08642e-05 | 2.08627e-05 | 0.9999 |
| `heavymetal_to_surface_water_cr` | 0.00363049 | 0.00363044 | 1.0000 |
| `heavymetal_to_surface_water_cu` | 0.00900988 | 0.00900988 | 1.0000 |
| `heavymetal_to_surface_water_hg` | 6.46432e-06 | 6.51829e-06 | 1.0083 |
| `heavymetal_to_surface_water_ni` | 0.00150134 | 0.00150128 | 1.0000 |
| `heavymetal_to_surface_water_pb` | 0.00154296 | 0.00154296 | 1.0000 |
| `heavymetal_to_surface_water_zn` | 0.00738638 | 0.00738645 | 1.0000 |

**rice_IN** (27 changed keys)

| key | old | new | ratio new/old |
|---|---|---|---|
| `heavymetal_to_ground_water_cd` | 1.87413e-05 | 1.87405e-05 | 1.0000 |
| `heavymetal_to_ground_water_cr` | 0.00836973 | 0.00836944 | 1.0000 |
| `heavymetal_to_ground_water_cu` | 0.00114853 | 0.00114841 | 0.9999 |
| `heavymetal_to_ground_water_hg` | 5.02458e-07 | 5.10182e-07 | 1.0154 |
| `heavymetal_to_ground_water_pb` | 0.00011975 | 0.000119738 | 0.9999 |
| `heavymetal_to_ground_water_zn` | 0.0124182 | 0.0124182 | 1.0000 |
| `heavymetal_to_soil_cd` | 0.00206946 | 0.00206855 | 0.9996 |
| `heavymetal_to_soil_cr` | 0.00681561 | 0.00679794 | 0.9974 |
| `heavymetal_to_soil_cu` | 0.0230104 | 0.0229978 | 0.9994 |
| `heavymetal_to_soil_hg` | 0.000228542 | 0.000298551 | 1.3063 |
| `heavymetal_to_soil_minus_uptake_cd` | 0.00199129 | 0.00199037 | 0.9995 |
| `heavymetal_to_soil_minus_uptake_cr` | 0.0047983 | 0.0047807 | 0.9963 |
| `heavymetal_to_soil_minus_uptake_cu` | 0.00547768 | 0.00546673 | 0.9980 |
| `heavymetal_to_soil_minus_uptake_hg` | 0.000228542 | 0.000298551 | 1.3063 |
| `heavymetal_to_soil_minus_uptake_ni` | -0.00271972 | -0.00273348 | 1.0051 |
| `heavymetal_to_soil_minus_uptake_pb` | -0.00296511 | -0.00296519 | 1.0000 |
| `heavymetal_to_soil_minus_uptake_zn` | 0.00441336 | 0.0044072 | 0.9986 |
| `heavymetal_to_soil_ni` | 0.00064407 | 0.000629173 | 0.9769 |
| `heavymetal_to_soil_pb` | -0.000967107 | -0.000967392 | 1.0003 |
| `heavymetal_to_soil_zn` | 0.176683 | 0.176677 | 1.0000 |
| `heavymetal_to_surface_water_cd` | 0.000110373 | 0.000110369 | 1.0000 |
| `heavymetal_to_surface_water_cr` | 0.0122713 | 0.0122708 | 1.0000 |
| `heavymetal_to_surface_water_cu` | 0.00824625 | 0.00824544 | 0.9999 |
| `heavymetal_to_surface_water_hg` | 3.79375e-05 | 3.85206e-05 | 1.0154 |
| `heavymetal_to_surface_water_ni` | 0.010409 | 0.0104055 | 0.9997 |
| `heavymetal_to_surface_water_pb` | 0.00498458 | 0.00498407 | 0.9999 |
| `heavymetal_to_surface_water_zn` | 0.0238036 | 0.0238035 | 1.0000 |

**wheat_IT** (23 changed keys)

| key | old | new | ratio new/old |
|---|---|---|---|
| `heavymetal_to_ground_water_cd` | 2.59725e-05 | 2.5972e-05 | 1.0000 |
| `heavymetal_to_ground_water_cr` | 0.0109248 | 0.0109242 | 1.0000 |
| `heavymetal_to_ground_water_cu` | 0.00128618 | 0.00128616 | 1.0000 |
| `heavymetal_to_ground_water_hg` | 6.56841e-07 | 6.66692e-07 | 1.0150 |
| `heavymetal_to_ground_water_zn` | 0.0150888 | 0.0150891 | 1.0000 |
| `heavymetal_to_soil_cd` | 0.00686654 | 0.00686422 | 0.9997 |
| `heavymetal_to_soil_cr` | 0.0150484 | 0.0150224 | 0.9983 |
| `heavymetal_to_soil_cu` | 0.0279259 | 0.0279249 | 1.0000 |
| `heavymetal_to_soil_hg` | 0.000384255 | 0.000466134 | 1.2131 |
| `heavymetal_to_soil_minus_uptake_cd` | 0.00661796 | 0.00661564 | 0.9996 |
| `heavymetal_to_soil_minus_uptake_cr` | 0.0140208 | 0.0139949 | 0.9981 |
| `heavymetal_to_soil_minus_uptake_cu` | 0.0145329 | 0.014532 | 0.9999 |
| `heavymetal_to_soil_minus_uptake_hg` | 0.000323806 | 0.000404778 | 1.2501 |
| `heavymetal_to_soil_minus_uptake_ni` | 0.00651625 | 0.00652074 | 1.0007 |
| `heavymetal_to_soil_minus_uptake_zn` | 0.0902292 | 0.0902469 | 1.0002 |
| `heavymetal_to_soil_ni` | 0.00714455 | 0.00714911 | 1.0006 |
| `heavymetal_to_soil_zn` | 0.169231 | 0.16925 | 1.0001 |
| `heavymetal_to_surface_water_cd` | 8.44319e-05 | 8.44301e-05 | 1.0000 |
| `heavymetal_to_surface_water_cr` | 0.0123578 | 0.0123572 | 1.0000 |
| `heavymetal_to_surface_water_cu` | 0.00497657 | 0.00497651 | 1.0000 |
| `heavymetal_to_surface_water_hg` | 2.40477e-05 | 2.44084e-05 | 1.0150 |
| `heavymetal_to_surface_water_ni` | 0.00590794 | 0.00590863 | 1.0001 |
| `heavymetal_to_surface_water_zn` | 0.0203268 | 0.0203272 | 1.0000 |

### Step 5: Farmyard manure (bbf65a2)

**apple_FR** (12 changed keys)

| key | old | new | ratio new/old |
|---|---|---|---|
| `heavymetal_to_ground_water_cd` | 3.54797e-05 | 3.55139e-05 | 1.0010 |
| `heavymetal_to_ground_water_cu` | 0.003214 | 0.003214 | 1.0000 |
| `heavymetal_to_ground_water_zn` | 0.0257491 | 0.0258043 | 1.0021 |
| `heavymetal_to_soil_cd` | 0.00213872 | 0.00214869 | 1.0047 |
| `heavymetal_to_soil_cu` | 2.92927 | 2.93036 | 1.0004 |
| `heavymetal_to_soil_minus_uptake_cd` | 0.00168036 | 0.00168989 | 1.0057 |
| `heavymetal_to_soil_minus_uptake_cu` | 2.75279 | 2.75389 | 1.0004 |
| `heavymetal_to_soil_minus_uptake_zn` | 0.190675 | 0.19616 | 1.0288 |
| `heavymetal_to_soil_zn` | 0.324009 | 0.329781 | 1.0178 |
| `heavymetal_to_surface_water_cd` | 2.08627e-05 | 2.08828e-05 | 1.0010 |
| `heavymetal_to_surface_water_cu` | 0.00900988 | 0.00900991 | 1.0000 |
| `heavymetal_to_surface_water_zn` | 0.00738645 | 0.0074023 | 1.0021 |

**rice_IN** (27 changed keys)

| key | old | new | ratio new/old |
|---|---|---|---|
| `heavymetal_to_ground_water_cd` | 1.87405e-05 | 1.87521e-05 | 1.0006 |
| `heavymetal_to_ground_water_cr` | 0.00836944 | 0.00837823 | 1.0011 |
| `heavymetal_to_ground_water_cu` | 0.00114841 | 0.00121815 | 1.0607 |
| `heavymetal_to_ground_water_hg` | 5.10182e-07 | 5.13978e-07 | 1.0074 |
| `heavymetal_to_ground_water_pb` | 0.000119738 | 0.000123434 | 1.0309 |
| `heavymetal_to_ground_water_zn` | 0.0124182 | 0.012818 | 1.0322 |
| `heavymetal_to_soil_cd` | 0.00206855 | 0.00208205 | 1.0065 |
| `heavymetal_to_soil_cr` | 0.00679794 | 0.00733554 | 1.0791 |
| `heavymetal_to_soil_cu` | 0.0229978 | 0.0328959 | 1.4304 |
| `heavymetal_to_soil_hg` | 0.000298551 | 0.000347399 | 1.1636 |
| `heavymetal_to_soil_minus_uptake_cd` | 0.00199037 | 0.00200383 | 1.0068 |
| `heavymetal_to_soil_minus_uptake_cr` | 0.0047807 | 0.00531618 | 1.1120 |
| `heavymetal_to_soil_minus_uptake_cu` | 0.00546673 | 0.0143003 | 2.6159 |
| `heavymetal_to_soil_minus_uptake_hg` | 0.000298551 | 0.000347399 | 1.1636 |
| `heavymetal_to_soil_minus_uptake_ni` | -0.00273348 | -0.00143712 | 0.5257 |
| `heavymetal_to_soil_minus_uptake_pb` | -0.00296519 | -0.0029322 | 0.9889 |
| `heavymetal_to_soil_minus_uptake_zn` | 0.0044072 | 0.0988321 | 22.4251 |
| `heavymetal_to_soil_ni` | 0.000629173 | 0.00201746 | 3.2065 |
| `heavymetal_to_soil_pb` | -0.000967392 | -0.000872733 | 0.9021 |
| `heavymetal_to_soil_zn` | 0.176677 | 0.276649 | 1.5658 |
| `heavymetal_to_surface_water_cd` | 0.000110369 | 0.000110437 | 1.0006 |
| `heavymetal_to_surface_water_cr` | 0.0122708 | 0.0122837 | 1.0011 |
| `heavymetal_to_surface_water_cu` | 0.00824544 | 0.00874615 | 1.0607 |
| `heavymetal_to_surface_water_hg` | 3.85206e-05 | 3.88073e-05 | 1.0074 |
| `heavymetal_to_surface_water_ni` | 0.0104055 | 0.0106899 | 1.0273 |
| `heavymetal_to_surface_water_pb` | 0.00498407 | 0.00513792 | 1.0309 |
| `heavymetal_to_surface_water_zn` | 0.0238035 | 0.0245699 | 1.0322 |

**wheat_IT** (8 changed keys)

| key | old | new | ratio new/old |
|---|---|---|---|
| `heavymetal_to_ground_water_cd` | 2.5972e-05 | 2.59718e-05 | 1.0000 |
| `heavymetal_to_ground_water_zn` | 0.0150891 | 0.0150864 | 0.9998 |
| `heavymetal_to_soil_cd` | 0.00686422 | 0.00686331 | 0.9999 |
| `heavymetal_to_soil_minus_uptake_cd` | 0.00661564 | 0.00661474 | 0.9999 |
| `heavymetal_to_soil_minus_uptake_zn` | 0.0902469 | 0.090063 | 0.9980 |
| `heavymetal_to_soil_zn` | 0.16925 | 0.169053 | 0.9988 |
| `heavymetal_to_surface_water_cd` | 8.44301e-05 | 8.44294e-05 | 1.0000 |
| `heavymetal_to_surface_water_zn` | 0.0203272 | 0.0203236 | 0.9998 |

### Step 6: Compost and sewage sludge (b7726d5)

**apple_FR** (27 changed keys)

| key | old | new | ratio new/old |
|---|---|---|---|
| `heavymetal_to_ground_water_cd` | 3.55139e-05 | 3.55679e-05 | 1.0015 |
| `heavymetal_to_ground_water_cr` | 0.0174247 | 0.0174669 | 1.0024 |
| `heavymetal_to_ground_water_cu` | 0.003214 | 0.00321403 | 1.0000 |
| `heavymetal_to_ground_water_hg` | 1.08132e-06 | 1.08207e-06 | 1.0007 |
| `heavymetal_to_ground_water_pb` | 0.000468915 | 0.000471099 | 1.0047 |
| `heavymetal_to_ground_water_zn` | 0.0258043 | 0.025882 | 1.0030 |
| `heavymetal_to_soil_cd` | 0.00214869 | 0.0021646 | 1.0074 |
| `heavymetal_to_soil_cr` | 0.0173664 | 0.0184154 | 1.0604 |
| `heavymetal_to_soil_cu` | 2.93036 | 2.93306 | 1.0009 |
| `heavymetal_to_soil_hg` | 0.00060209 | 0.000607685 | 1.0093 |
| `heavymetal_to_soil_minus_uptake_cd` | 0.00168989 | 0.0017051 | 1.0090 |
| `heavymetal_to_soil_minus_uptake_cr` | 0.014567 | 0.0156093 | 1.0715 |
| `heavymetal_to_soil_minus_uptake_cu` | 2.75389 | 2.75659 | 1.0010 |
| `heavymetal_to_soil_minus_uptake_hg` | 0.000309024 | 0.000314417 | 1.0174 |
| `heavymetal_to_soil_minus_uptake_ni` | 0.0230603 | 0.0237741 | 1.0310 |
| `heavymetal_to_soil_minus_uptake_pb` | 0.0665693 | 0.0691476 | 1.0387 |
| `heavymetal_to_soil_minus_uptake_zn` | 0.19616 | 0.204158 | 1.0408 |
| `heavymetal_to_soil_ni` | 0.0269519 | 0.0276846 | 1.0272 |
| `heavymetal_to_soil_pb` | 0.0692311 | 0.0718218 | 1.0374 |
| `heavymetal_to_soil_zn` | 0.329781 | 0.338181 | 1.0255 |
| `heavymetal_to_surface_water_cd` | 2.08828e-05 | 2.09146e-05 | 1.0015 |
| `heavymetal_to_surface_water_cr` | 0.00363044 | 0.00363922 | 1.0024 |
| `heavymetal_to_surface_water_cu` | 0.00900991 | 0.00900998 | 1.0000 |
| `heavymetal_to_surface_water_hg` | 6.51829e-06 | 6.52279e-06 | 1.0007 |
| `heavymetal_to_surface_water_ni` | 0.00150128 | 0.00150858 | 1.0049 |
| `heavymetal_to_surface_water_pb` | 0.00154296 | 0.00155015 | 1.0047 |
| `heavymetal_to_surface_water_zn` | 0.0074023 | 0.00742459 | 1.0030 |

**rice_IN** (0 changed keys)


**wheat_IT** (0 changed keys)


### Step 7: Seed (c1c8857)

**apple_FR** (27 changed keys)

| key | old | new | ratio new/old |
|---|---|---|---|
| `heavymetal_to_ground_water_cd` | 3.55679e-05 | 3.53163e-05 | 0.9929 |
| `heavymetal_to_ground_water_cr` | 0.0174669 | 0.0174517 | 0.9991 |
| `heavymetal_to_ground_water_cu` | 0.00321403 | 0.00321399 | 1.0000 |
| `heavymetal_to_ground_water_hg` | 1.08207e-06 | 1.07803e-06 | 0.9963 |
| `heavymetal_to_ground_water_pb` | 0.000471099 | 0.000470776 | 0.9993 |
| `heavymetal_to_ground_water_zn` | 0.025882 | 0.0256607 | 0.9914 |
| `heavymetal_to_soil_cd` | 0.0021646 | 0.002092 | 0.9665 |
| `heavymetal_to_soil_cr` | 0.0184154 | 0.0180322 | 0.9792 |
| `heavymetal_to_soil_cu` | 2.93306 | 2.92824 | 0.9984 |
| `heavymetal_to_soil_hg` | 0.000607685 | 0.000578514 | 0.9520 |
| `heavymetal_to_soil_minus_uptake_cd` | 0.0017051 | 0.00163575 | 0.9593 |
| `heavymetal_to_soil_minus_uptake_cr` | 0.0156093 | 0.0152285 | 0.9756 |
| `heavymetal_to_soil_minus_uptake_cu` | 2.75659 | 2.75177 | 0.9983 |
| `heavymetal_to_soil_minus_uptake_hg` | 0.000314417 | 0.000286339 | 0.9107 |
| `heavymetal_to_soil_minus_uptake_ni` | 0.0237741 | 0.0230418 | 0.9692 |
| `heavymetal_to_soil_minus_uptake_pb` | 0.0691476 | 0.0687566 | 0.9943 |
| `heavymetal_to_soil_minus_uptake_zn` | 0.204158 | 0.182229 | 0.8926 |
| `heavymetal_to_soil_ni` | 0.0276846 | 0.0269329 | 0.9728 |
| `heavymetal_to_soil_pb` | 0.0718218 | 0.0714289 | 0.9945 |
| `heavymetal_to_soil_zn` | 0.338181 | 0.315106 | 0.9318 |
| `heavymetal_to_surface_water_cd` | 2.09146e-05 | 2.07667e-05 | 0.9929 |
| `heavymetal_to_surface_water_cr` | 0.00363922 | 0.00363607 | 0.9991 |
| `heavymetal_to_surface_water_cu` | 0.00900998 | 0.00900986 | 1.0000 |
| `heavymetal_to_surface_water_hg` | 6.52279e-06 | 6.49845e-06 | 0.9963 |
| `heavymetal_to_surface_water_ni` | 0.00150858 | 0.00150109 | 0.9950 |
| `heavymetal_to_surface_water_pb` | 0.00155015 | 0.00154909 | 0.9993 |
| `heavymetal_to_surface_water_zn` | 0.00742459 | 0.00736109 | 0.9914 |

**rice_IN** (27 changed keys)

| key | old | new | ratio new/old |
|---|---|---|---|
| `heavymetal_to_ground_water_cd` | 1.87521e-05 | 1.87465e-05 | 0.9997 |
| `heavymetal_to_ground_water_cr` | 0.00837823 | 0.00837838 | 1.0000 |
| `heavymetal_to_ground_water_cu` | 0.00121815 | 0.00121826 | 1.0001 |
| `heavymetal_to_ground_water_hg` | 5.13978e-07 | 5.13943e-07 | 0.9999 |
| `heavymetal_to_ground_water_pb` | 0.000123434 | 0.000124028 | 1.0048 |
| `heavymetal_to_ground_water_zn` | 0.012818 | 0.012818 | 1.0000 |
| `heavymetal_to_soil_cd` | 0.00208205 | 0.00207548 | 0.9968 |
| `heavymetal_to_soil_cr` | 0.00733554 | 0.00734543 | 1.0013 |
| `heavymetal_to_soil_cu` | 0.0328959 | 0.0329151 | 1.0006 |
| `heavymetal_to_soil_hg` | 0.000347399 | 0.000346892 | 0.9985 |
| `heavymetal_to_soil_minus_uptake_cd` | 0.00200383 | 0.00199728 | 0.9967 |
| `heavymetal_to_soil_minus_uptake_cr` | 0.00531618 | 0.00532603 | 1.0019 |
| `heavymetal_to_soil_minus_uptake_cu` | 0.0143003 | 0.0143178 | 1.0012 |
| `heavymetal_to_soil_minus_uptake_hg` | 0.000347399 | 0.000346892 | 0.9985 |
| `heavymetal_to_soil_minus_uptake_ni` | -0.00143712 | -0.00140886 | 0.9803 |
| `heavymetal_to_soil_minus_uptake_pb` | -0.0029322 | -0.00292551 | 0.9977 |
| `heavymetal_to_soil_minus_uptake_zn` | 0.0988321 | 0.0988288 | 1.0000 |
| `heavymetal_to_soil_ni` | 0.00201746 | 0.00204745 | 1.0149 |
| `heavymetal_to_soil_pb` | -0.000872733 | -0.000856124 | 0.9810 |
| `heavymetal_to_soil_zn` | 0.276649 | 0.276645 | 1.0000 |
| `heavymetal_to_surface_water_cd` | 0.000110437 | 0.000110404 | 0.9997 |
| `heavymetal_to_surface_water_cr` | 0.0122837 | 0.012284 | 1.0000 |
| `heavymetal_to_surface_water_cu` | 0.00874615 | 0.00874692 | 1.0001 |
| `heavymetal_to_surface_water_hg` | 3.88073e-05 | 3.88046e-05 | 0.9999 |
| `heavymetal_to_surface_water_ni` | 0.0106899 | 0.0106953 | 1.0005 |
| `heavymetal_to_surface_water_pb` | 0.00513792 | 0.00516267 | 1.0048 |
| `heavymetal_to_surface_water_zn` | 0.0245699 | 0.0245699 | 1.0000 |

**wheat_IT** (27 changed keys)

| key | old | new | ratio new/old |
|---|---|---|---|
| `heavymetal_to_ground_water_cd` | 2.59718e-05 | 2.59681e-05 | 0.9999 |
| `heavymetal_to_ground_water_cr` | 0.0109242 | 0.0109239 | 1.0000 |
| `heavymetal_to_ground_water_cu` | 0.00128616 | 0.00128362 | 0.9980 |
| `heavymetal_to_ground_water_hg` | 6.66692e-07 | 6.66723e-07 | 1.0000 |
| `heavymetal_to_ground_water_pb` | 0.000118274 | 0.0001182 | 0.9994 |
| `heavymetal_to_ground_water_zn` | 0.0150864 | 0.0150305 | 0.9963 |
| `heavymetal_to_soil_cd` | 0.00686331 | 0.00684772 | 0.9977 |
| `heavymetal_to_soil_cr` | 0.0150224 | 0.0150077 | 0.9990 |
| `heavymetal_to_soil_cu` | 0.0279249 | 0.0277475 | 0.9936 |
| `heavymetal_to_soil_hg` | 0.000466134 | 0.000466439 | 1.0007 |
| `heavymetal_to_soil_minus_uptake_cd` | 0.00661474 | 0.00659918 | 0.9976 |
| `heavymetal_to_soil_minus_uptake_cr` | 0.0139949 | 0.0139803 | 0.9990 |
| `heavymetal_to_soil_minus_uptake_cu` | 0.014532 | 0.0143812 | 0.9896 |
| `heavymetal_to_soil_minus_uptake_hg` | 0.000404778 | 0.00040508 | 1.0007 |
| `heavymetal_to_soil_minus_uptake_ni` | 0.00652074 | 0.00650242 | 0.9972 |
| `heavymetal_to_soil_minus_uptake_pb` | 0.00193673 | 0.00193388 | 0.9985 |
| `heavymetal_to_soil_minus_uptake_zn` | 0.090063 | 0.0862313 | 0.9575 |
| `heavymetal_to_soil_ni` | 0.00714911 | 0.00713049 | 0.9974 |
| `heavymetal_to_soil_pb` | 0.00219222 | 0.00218921 | 0.9986 |
| `heavymetal_to_soil_zn` | 0.169053 | 0.16493 | 0.9756 |
| `heavymetal_to_surface_water_cd` | 8.44294e-05 | 8.44176e-05 | 0.9999 |
| `heavymetal_to_surface_water_cr` | 0.0123572 | 0.0123569 | 1.0000 |
| `heavymetal_to_surface_water_cu` | 0.00497651 | 0.00496666 | 0.9980 |
| `heavymetal_to_surface_water_hg` | 2.44084e-05 | 2.44096e-05 | 1.0000 |
| `heavymetal_to_surface_water_ni` | 0.00590863 | 0.00590582 | 0.9995 |
| `heavymetal_to_surface_water_pb` | 0.00240994 | 0.00240843 | 0.9994 |
| `heavymetal_to_surface_water_zn` | 0.0203236 | 0.0202484 | 0.9963 |


## 8. Manure contents and NH3 on GRUDAF 2009 Table 39 and EMEP/EEA 2023 3.B (decision L12, 2026-10-11)

N, P2O5 and TAN (soluble N, Nlös) per m3 of undiluted slurry or per t of solid manure come from
GRUDAF 2009 Table 39 (`grudaf2009_table39.csv`). NH3-N after spreading is TAN x EF application
of EMEP/EEA 2023 3.B Table 3-9 (`emep2023_3b_table3_9.csv`). The combination per legacy input
type is in `manure_type_composition.csv` (status proposed). The legacy constants were already
the Table 39 values, so N and P2O5 do not change; only the EFs change.

| Manure type | Table 39 rows (weight) | EMEP 3-9 row, EF | TAN | NH3-N old | NH3-N new |
|---|---|---|---|---|---|
| liquid cattle (kg/m3) | complete slurry, low-dung slurry (0.5 each) | dairy cattle slurry, 0.55 | 2.75 | 1.5125 | 1.5125 |
| liquid pig (kg/m3) | fattening, breeding slurry (0.5 each) | finishing pigs 0.40, sows 0.29 | 3.75 | 1.29375 | 1.3185 |
| liquid laying hen (kg/m3) | hen droppings, belt | laying hens slurry, 0.69 | 6.3 | 4.347 | 4.347 |
| solid cattle (kg/t) | stackable, deep litter (0.5 each) | dairy cattle solid, 0.68 | 1.05 | 0.8295 | 0.714 |
| solid horses (kg/t) | horse manure (stored) | horses solid, 0.90 | 0.7 | 0.63 | 0.63 |
| solid laying hen + broiler (kg/t) | hen manure pit/floor, broiler manure (0.5 each) | laying hens solid 0.45, broilers 0.38 | 8.5 | 5.7375 | 3.475 |
| solid pig (kg/t) | pig manure | finishing pigs solid, 0.45 | 2.3 | 1.863 | 1.035 |
| solid sheep / goat (kg/t) | sheep / goat manure | sheep solid, 0.90 | 2.3 | 2.07 | 2.07 |
| liquid other (kg/m3) | FAOSTAT world mix (L13) | - | 3.174 | 1.7765461 | 1.5568 |
| solid other (kg/t) | FAOSTAT world mix (L13) | - | 1.902 | 2.00410305 | 1.0619 |

Reference cases (wheat_IT has only liquid cattle manure and does not change):

| Case | Key | Old | New | New/old |
|---|---|---|---|---|
| apple_FR | `ammonia_total` | 7.8377 | 7.13553 | 0.9104 |
| apple_FR | `N2o_air` | 2.38936 | 2.38088 | 0.9965 |
| apple_FR | `Nox_as_n2o_air` | 4.52052 | 4.54362 | 1.0051 |
| apple_FR | `nitrate_to_groundwater` | 131.509 | 131.675 | 1.0013 |
| apple_FR | `nitrate_to_surfacewater` | 14.6121 | 14.6305 | 1.0013 |
| rice_IN | `ammonia_total` | 30.514 | 30.3304 | 0.9940 |
| rice_IN | `N2o_air` | 1.91678 | 1.91538 | 0.9993 |
| rice_IN | `Nox_as_n2o_air` | 4.78204 | 4.78808 | 1.0013 |
| rice_IN | `nitrate_to_groundwater` | 225.51 | 225.865 | 1.0016 |

The reference-case table above is for L12 alone (commit c3d64dc). The 12 rows of
`manure_type_composition.csv` were signed by FC on 2026-10-12.

### "Other" manure as FAOSTAT world mix (decision L13, 2026-10-12)

World manure N applied to soils, mean 2021-2023 (`faostat_manure_n_applied_world.csv`), grouped
by `manure_other_faostat_mapping.csv`; N shares converted to volume (liquid) or mass (solid)
shares with the N content of each type.

| Mix | Type | N share | Volume / mass share |
|---|---|---|---|
| liquid | cattle (incl. buffalo) | 0.5672 | 0.6673 |
| liquid | pig | 0.2934 | 0.2967 |
| liquid | laying hen | 0.1394 | 0.0359 |
| solid | cattle (incl. buffalo) | 0.4320 | 0.6422 |
| solid | horses, asses, mules | 0.0035 | 0.0039 |
| solid | hen, broiler, turkey, duck litter | 0.2668 | 0.0663 |
| solid | pig | 0.2234 | 0.2172 |
| solid | sheep / goat | 0.0742 | 0.0703 |

| Mix | N old | N new | P2O5 old | P2O5 new | TAN new | NH3-N old | NH3-N new |
|---|---|---|---|---|---|---|---|
| liquid other (kg/m3) | 6.33529 | 5.4119 | 3.40798 | 2.6505 | 3.1743 | 1.7765 | 1.5568 |
| solid other (kg/t) | 10.40797 | 7.5819 | 7.40504 | 5.1644 | 1.9022 | 2.0041 | 1.0619 |

The TAN of the "other" types is now known; before, the total N was used as soluble N (F3).

| Case | Key | Old | New | New/old |
|---|---|---|---|---|
| rice_IN | `ammonia_total` | 30.3304 | 28.7146 | 0.9467 |
| rice_IN | `N2o_air` | 1.91538 | 1.80799 | 0.9439 |
| rice_IN | `Nox_as_n2o_air` | 4.78808 | 4.68184 | 0.9778 |
| rice_IN | `nitrate_to_groundwater` | 225.865 | 200.614 | 0.8882 |

apple_FR and wheat_IT have no "other" manure and do not change.

## 9. Pesticide metals reaching the field from OLCA-Pest (decision L14, 2026-10-12)

SALCAheavymetal 2023 Eq. 2 multiplies the metals of the pesticides by 1 - f_air - f_OFS, the
share of the applied pesticide staying on the field in the OLCA-Pest primary distribution
(Nemecek et al. 2022, no buffer zone). It replaces the legacy constant 0.95. The values come from
sheet OLCA CALC of the OLCApest mapping tool (`olca_pest_default_fractions.csv`), the crop
archetypes from sheets crop-class_C and CLASSIFICATION (`pesticide_crop_archetype_mapping.csv`).
All metal-containing pesticides of the model are fungicides.

| Crop archetype (examples) | Field fraction, fungicide | Old |
|---|---|---|
| Grapes/ Vines (grape) | 0.8017 | 0.95 |
| Berries (strawberry, blueberry) | 0.8648 | 0.95 |
| Vegetables fruit / leafy (tomato, cabbage) | 0.8852 | 0.95 |
| Fruit trees temperate / tropical, Citrus, Oil-Bearing trees | 0.8865 | 0.95 |
| Average annual crops (cotton, flax, tea) | 0.8882 | 0.95 |
| Roots and tubers, Bulbs | 0.8885 / 0.8880 | 0.95 |
| Pooideae, Panicoideae, Paddy rice (wheat, maize, rice) | 0.8895 | 0.95 |
| Pulses (soybean, lentil) | 0.9295 | 0.95 |

| Case | Key | Old | New | New/old |
|---|---|---|---|---|
| apple_FR | `heavymetal_to_soil_cu` | 2.92824 | 2.7379 | 0.9350 |
| apple_FR | `heavymetal_to_soil_minus_uptake_cu` | 2.75177 | 2.57096 | 0.9343 |
| apple_FR | `heavymetal_to_ground_water_cu` | 0.00321399 | 0.0032122 | 0.9994 |
| apple_FR | `heavymetal_to_surface_water_cu` | 0.00900986 | 0.00900485 | 0.9994 |
| wheat_IT | `heavymetal_to_soil_zn` | 0.16493 | 0.164198 | 0.9956 |
| wheat_IT | `heavymetal_to_soil_minus_uptake_zn` | 0.0862313 | 0.085589 | 0.9926 |
| wheat_IT | `heavymetal_to_ground_water_zn` | 0.0150305 | 0.0150204 | 0.9993 |
| wheat_IT | `heavymetal_to_surface_water_zn` | 0.0202484 | 0.0202347 | 0.9993 |

rice_IN has no metal-containing pesticides and does not change.


## 10. NH3 from compost and sewage sludge with EMEP/EEA 2023 3.D (decision L15, 2026-10-12)

The legacy NH3 of compost and sewage sludge was TAN x emission fraction from Agribalyse v1.1
Tab. 67 and Tab. 154, values only cited in the legacy code (`organic_fertiliser_nh3.csv`, O7).
EMEP/EEA 2023 3.D Tier 1, Eq. (1), multiplies the total N applied by an EF in kg NH3 per kg N
(Table 3-1, `emep2023_3d_table3_1.csv`): 0.13 for sewage sludge (3Da2b; Annex 1 assumes one third
of the N ammoniacal and one third of that lost) and 0.08 for other organic wastes including
compost (3Da2c). Dried poultry manure is assigned to 3Da2c, because the 3.B method needs the TAN
at spreading, which is not available for the dried product.

The N, TAN and P2O5 contents moved from the code to `organic_fertiliser_composition.csv`. The values
are unchanged except two TAN values:
- compost: Nlös 0.3 kg/t FM from GRUDAF 2009 Table 42 (median), instead of 0.83; the same table
  documents the compost N of 7.0 kg/t FM;
- stone meal: 0, because the product has no N (the legacy code gave it the TAN of feather meal).

The TAN enters only the N supply of the nitrate model (Fix F3). The other N, TAN and P2O5 values
are still legacy, undocumented, provisional.

| Type | NFR | N (kg/t FM) | Old NH3 (kg/t FM) | EF (kg NH3/kg N) | New NH3 (kg/t FM) | TAN old -> new |
|---|---|---|---|---|---|---|
| `composttype_compost` | 3Da2c | 7.0 | 0.72 | 0.08 | 0.56 | 0.83 -> 0.3 |
| `composttype_meat_and_bone_meal` | 3Da2c | 85.5 | 5.61 | 0.08 | 6.84 | 6.50 |
| `composttype_castor_oil_shell_coarse` | 3Da2c | 10.0 | 0.72 | 0.08 | 0.80 | 0.83 |
| `composttype_vinasse` | 3Da2c | 3.5 | 0.95 | 0.08 | 0.28 | 0.96 |
| `composttype_dried_poultry_manure` | 3Da2c | 45.0 | 0.70 | 0.08 | 3.60 | 0.83 |
| `composttype_stone_meal` | 3Da2c | 0.0 | 5.61 | 0.08 | 0.00 | 6.50 -> 0.0 |
| `composttype_feather_meal`, `horn_meal`, `horn_shavings_fine` | 3Da2c | 130.15 | 5.61 | 0.08 | 10.41 | 6.50 |
| `sewagesludge_liquid` | 3Da2b | 2.5 | 1.04 | 0.13 | 0.33 | 2.13 |
| `sewagesludge_dehydrated` | 3Da2b | 9.7 | 1.56 | 0.13 | 1.26 | 3.20 |
| `sewagesludge_dried` | 3Da2b | 8.4 | 0.88 | 0.13 | 1.09 | 1.80 |

Only apple_FR (2 t of green-waste compost) changes. The NH3 of the compost falls from 1.43 to
1.12 kg. Less NH3-N raises the NOx base (N applied minus NH3-N) and the N supply S. The lower
compost TAN (-1.06 kg N) more than compensates for that, so S falls by 0.80 kg N and the nitrate
falls slightly.

| Case | Key | Old | New | New/old |
|---|---|---|---|---|
| apple_FR | `ammonia_total` | 7.13553 | 6.82249 | 0.9561 |
| apple_FR | `Nox_as_n2o_air` | 4.54362 | 4.55391 | 1.0023 |
| apple_FR | `N2o_air` | 2.38088 | 2.3762 | 0.9980 |
| apple_FR | `nitrate_to_groundwater` | 131.675 | 131.441 | 0.9982 |
| apple_FR | `nitrate_to_surfacewater` | 14.6305 | 14.6045 | 0.9982 |

wheat_IT and rice_IN use neither compost nor sewage sludge and do not change.

## 11. Land use change from the WFLDB-adapted Blonk tool, in ha (decision L16, 2026-10-12)

The tool does not compute LUC emissions. It writes an input of the ecoinvent product
"land use change, annual crop / perennial crop / paddy rice" whose amount is the formula
`<REC_CS> * LUC_crop_specific + <REC_SR> * (1-LUC_crop_specific)` per ha and crop cycle (REC / crop
cycles), divided by the yield of the cycle. The dataset parameter LUC_crop_specific = 1 selects the
crop-specific approach.

Source of the ratios. The two tables of the legacy `lucmodel.py` were compared with the
WFLDB-adapted Blonk direct land use change assessment tool 2016-06-09a supplied by FC:

| Table | Workbook | Values | Identical to the legacy code (1e-12) |
|---|---|---|---|
| `luc_blonk_country_expansion.csv` (REC_SR) | sheet "5. Country averages", column AD | 39 countries | 38; MA corrected |
| `luc_blonk_crop_expansion.csv` (REC_CS) | sheet "6. Crop data", column AE | 1583 crop-country pairs | 1583 |

The legacy value for Morocco, 0.032242306728212, has lost one digit of the workbook value
0.03322423067282125. Turmeric uses the FAOSTAT item Ginger and pomegranate the item "Fruit,
tropical fresh nes" as proxies, as in the legacy code (legacy, undocumented, provisional).

Unit. The Blonk tool gives the element to insert in the crop process as
`(0.4016*LUC_crop_specific+0.1999*(1-LUC_crop_specific))` in ha (apples, Brazil; the same REC values
as the legacy code). Its land use change process "is described for 1 ha of LUC" and already contains
the 20-year amortisation: transformation of 500 m2 per ha of LUC and emissions (CSR - CA) x 3.664 x
1/20. The amount is therefore not divided by 20. The legacy Java template declared the exchange in
kg, while the Master Data has ha; the writer will use ha.

Rice. The Blonk tool has three crop types (annual, perennial, paddy rice), and Master Data 3.12 has
the product "land use change, paddy rice". The legacy Java writer built the name "land use change,
Paddy rice crop", which does not exist, so rice had no LUC exchange. Flooded rice now gets
"land use change, paddy rice" (`luc_product_mapping.csv`).

Regression: new key `luc_product` in all cases; in rice_IN the last digit of the ratios changes
(full precision instead of 15 significant digits). No other output changes.

The statistical LUC method of Quantis (2024), used by WFLDB 3.8, is not adopted. It distributes the
LUC over time on the crop side (linear discounting) and puts the full emissions per ha in the LUC
dataset, gives no values per crop and country, and the Master Data 3.12 products still follow the
Blonk structure (five former land uses, land tenure products).

## 12. Seaweed lime CO2, liquid manure density, P land-use classes (decisions L17-L19, 2026-10-12)

CO2 from seaweed lime (L17). Master Data 3.12 gives "limestone, from algae" carbon content, fossil 0
and carbon content, non-fossil 0.107040 (CaCO3 from algae). The legacy `co2model.py` added the Ca of
seaweed lime to limestone and carbonation lime and wrote all of it as "Carbon dioxide, fossil".
Seaweed lime now has its own output `CO2_non_fossil_from_fertilisers`, aligned with "Carbon dioxide,
non-fossil" (air, non-urban air or from high stacks, `d6235194-e4e6-4548-bfa3-ac095131aef4`) in
`elementary_flow_alignment.csv`. The amount keeps the stoichiometry of the other limes,
44.0095 / 40.078 = 1.0981 kg CO2 per kg Ca; the Master Data C/Ca ratio would give 1.1005 (+0.2 %).
The sum of fossil and non-fossil CO2 is the legacy total.

Liquid manure density (L18). FC set `liquid_manure_density_kg_per_m3` to 1020 kg/m3, from the general
comment of the ecoinvent v3.12 dataset "manure, liquid, cattle" (Recycled Content cut-off, 7.5 %
dry matter), instead of the unsourced legacy 1006 kg/m3. The density converts m3 of undiluted liquid
manure to kg of fresh matter for the manure product exchange and for the heavy metals of manure.

P land-use classes (L19). The 7 rows of `p_landuse_classes.csv` were checked against Prasuhn (2006)
SALCA-Phosphor, Tab. 1 (leaching, p. 5) and Tab. 2 (run-off, p. 9):

| Class in the tool | Prasuhn category | Leaching kg P/ha | Run-off kg P/ha |
|---|---|---|---|
| Arable land | Ackerland / offenes Ackerland | 0.07 | 0.175 |
| Grassland intensive | Dauerwiesen | 0.06 | 0.25 |
| Grassland extensive | Dauerwiesen (Tab. 1) / extensive und wenig intensive Wiesen und Weiden (Tab. 2) | 0.06 | 0.15 |
| Fruit trees | Obstbau | 0.06 | 0.25 |
| Summer alpine pastures | Alpwirtschaftliche Nutzfläche | 0.055 | 0.25 |
| Vegetables | Gartenbau | 0.07 | 0.175 |
| Viticulture | Rebbau | 0.07 | 0.175 |

All values equal the table; the four classes taken from the legacy code (fruit trees, summer alpine
pastures, vegetables, viticulture) lose the tag "legacy, undocumented, provisional". Prasuhn states
that the values apply to Switzerland.

Regression (1020 / 1006 = 1.0139):

| Case | Key | Old | New |
|---|---|---|---|
| wheat_IT | liquid_manure_cattle (kg) | 20120 | 20400 |
| rice_IN | liquid_manure_cattle (kg) | 1615.21 | 1637.69 |
| rice_IN | liquid_manure_laying_hen (kg) | 34.767 | 35.2509 |
| rice_IN | liquid_manure_pig (kg) | 39.3942 | 39.9424 |

The heavy-metal outputs of wheat_IT and rice_IN change by -0.2 % to +1.9 % (the decreases are negative
soil balances that become less negative). New key `CO2_non_fossil_from_fertilisers` = 0 in all three
cases (no seaweed lime); `CO2_from_fertilisers` unchanged. apple_FR has no liquid manure.

## 13. Contents of compost-type products and sewage sludge from Agribalyse 3.1 (decision L20, 2026-10-12)

FC supplied the Agribalyse 3.1 methodology report (agricultural stage). Two tables give the
contents of the organic fertilisers that are not farmyard manure:

- Table 59 (p. 130), TAN of organic fertilizers from outside the farm, kg TAN per t or m3: liquid
  sewage sludge 2.13, semi-solid 3.20, dried 1.80 (printed "1.,80"), green waste compost 0.83,
  feather meal 6.50, concentrated sugar beet vinasse and distillery vinasse 0.96. These are the
  values the legacy code cited from Agribalyse v1.1 Tab. 67.
- Table 142 (Appendix G, p. 230-231), composition per t of fresh matter: liquid sewage sludge N 3,
  P2O5 2.5; semi-solid N 10, P2O5 7.5; dried N 40, P2O5 60 (source 6, Arvalis); feather meal N 130
  (source 7, Arvalis); dry poultry droppings N 38.2, N-NH4 4.0, P2O5 37.9 (source 11, ITAVI 2003).

The text was extracted with `pdftotext -table` and each value assigned to its column by character
position. In the vinasse row of Table 142 the total N column is empty in the extracted text, so the
vinasse N stays legacy.

| Type | N old -> new (kg/t FM) | TAN old -> new | NH3 old -> new (kg NH3/t FM) | Source |
|---|---|---|---|---|
| `sewagesludge_liquid` | 2.5 -> 3 | 2.13 | 0.33 -> 0.39 | Agribalyse 3.1; P2O5 3.5 -> 2.5 |
| `sewagesludge_dehydrated` | 9.7 -> 10 | 3.20 | 1.26 -> 1.30 | Agribalyse 3.1 (semi-solid) |
| `sewagesludge_dried` | 8.4 -> 40 | 1.80 | 1.09 -> 5.20 | Agribalyse 3.1 |
| `composttype_feather_meal` | 130.15 -> 130 | 6.50 | 10.41 -> 10.40 | Agribalyse 3.1 |
| `composttype_horn_meal`, `horn_shavings_fine` | 130.15 -> 130 | 6.50 | 10.41 -> 10.40 | proxy feather meal (FC) |
| `composttype_dried_poultry_manure` | 45.0 -> 38.2 | 0.83 -> 4.0 | 3.60 -> 2.19 (L21) | Agribalyse 3.1 (dry poultry droppings) |
| `composttype_meat_and_bone_meal` | 85.5 (legacy) | 6.50 | 6.84 | TAN: proxy feather meal (FC) |
| `composttype_castor_oil_shell_coarse` | 10.0 (legacy) | 0.83 | 0.80 | TAN: proxy green waste compost (FC) |
| `composttype_vinasse` | 3.5 (legacy) | 0.96 | 0.28 | TAN: Agribalyse 3.1 |
| `composttype_stone_meal` | 0 | 0 | 0 | no N (confirmed by FC) |

NH3 = N x EF of EMEP/EEA 2023 3.D Table 3-1 (0.13 sewage sludge, 0.08 other organic wastes), except
dried poultry manure (see below). The
TAN enters the N supply of the nitrate model (Fix F3). Three values remain legacy, undocumented,
provisional: the N of meat and bone meal, castor oil shell and vinasse.

Dried poultry manure (decision L21). L15 placed it in 3Da2c because no TAN at spreading was
available. With the TAN of Agribalyse 3.1 it is now treated as livestock manure, as the manure
model does (L12): NH3-N = TAN x EF application of EMEP/EEA 2023 3.B Table 3-9, laying hens,
"Solid, can be stacked", 0.45 (Agribalyse 3.1 Table 140 maps dry layer droppings to dry poultry
droppings). Per t FM: 4.0 x 0.45 x 17.0306/14.0067 = 2.19 kg NH3, instead of 38.2 x 0.08 = 3.06
with the 3.D EF. NFR 3B4gi; the row gets the new columns emep_livestock and emep_manure_type.

Regression: unchanged (the three cases use only green-waste compost).

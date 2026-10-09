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

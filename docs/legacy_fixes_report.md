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

`C:\python\external_data\MasterData (3.12, undef).xlsx` (since 2026-10-13 in `data/external_data/`, O10) is configured in the git-ignored
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
(b5e3568, removal of the old tables) changed no output.

### Step 1: Deposition, leaching and soil contents (commit ef0d259)

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

### Step 2: Harvest export with Table 1 plant contents, co-products and pesticide term (5f1701f)

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

### Step 3: Metal contents of pesticides (3c98a67)

**apple_FR** (0 changed keys)


**rice_IN** (0 changed keys)


**wheat_IT** (4 changed keys)

| key | old | new | ratio new/old |
|---|---|---|---|
| `heavymetal_to_ground_water_zn` | 0.0155849 | 0.0150888 | 0.9682 |
| `heavymetal_to_soil_minus_uptake_zn` | 0.12974 | 0.0902292 | 0.6955 |
| `heavymetal_to_soil_zn` | 0.213597 | 0.169231 | 0.7923 |
| `heavymetal_to_surface_water_zn` | 0.0209952 | 0.0203268 | 0.9682 |

### Step 4: Mineral-fertiliser heavy metals, Hg, Ca per kg Ca, Mg (0a315b6)

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

### Step 5: Farmyard manure (89defa7)

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

### Step 6: Compost and sewage sludge (b13918a)

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


### Step 7: Seed (0536e59)

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

The reference-case table above is for L12 alone (commit f53c846). The 12 rows of
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

## 14. Country default tables from the WFLDB 2017 background parameters (decision L22, 2026-10-13)

The Quantis workbook "GD_crop", from which `defaultTables.py` and `defaultMatrix*.py` were
generated, was not found in the ecoinvent archives. Its L0/L1 terminology and its sheet names are
those of the World Food LCA Database (WFLDB), whose generic data are published as ecoinvent 3
reports: WFLDB Guidelines v3.0 (2016) for the method, WFLDB 3.1 Documentation and Background
Parameters (04 May 2017) for the country parameters.

| Table | Workbook (Background Parameters 2017) | Values | Identical to the legacy code (15 digits) |
|---|---|---|---|
| `wfldb2017_agr_system_parameters.csv` | sheet 1, rows 17, 12, 7, 13, 14, 18 | 39 x 6 | 37 countries; CN humus changed |
| `wfldb2017_irrigation_water_sources.csv` | sheet 2, rows 4-6 | 39 x 3 | 37 countries |
| `wfldb2017_manure_animal_shares.csv` (removed by L29, section 19) | sheet 3, rows 5-9 and 11-17 | 39 x 10 | 37 countries |

The nine dictionaries of `defaultTables.py` (precipitation, clay, sand, soil carbon, pH <= 7, snow,
irrigation water sources, liquid and solid manure shares) are now built from these files, with
the same names and enum keys. Clay content is the soil-type mix of rows 5-10 times the clay
content per soil type of the Documentation, Tab. 6 (p. 14); this was recalculated for all 37
countries. The soil carbon of China is 0.02, the estimate given in the Documentation, p. 14,
note 3; the workbook cell is 0 and the legacy code used 0.0229, the mean of the other countries.
Morocco and Serbia (CS) are not in WFLDB; their values were added by Quantis in 2017 and stay
legacy, undocumented, provisional.

Regression: unchanged (no case in China; the other values differ only in the last digit).

## 15. Default yield from FAOSTAT 2021-2024 (decision L23, 2026-10-13)

When the template gives no yield, the tool takes `yield_main_product_per_year` from a crop x
country table. The legacy table was the GD_crop sheet Yield_2009_2012_L1: FAOSTAT yields
2009-2012 of an older FAOSTAT vintage (the current FAOSTAT 2009-2012 means match it for only part
of the countries), with GLO as the simple mean of the countries and GLO = 0 for 23 crops
(bell pepper, cabbage, cashew, cassava, cotton, grape, mango, sesame and others).

The new table `default_yield.csv` is built by `scripts/build_default_yield.py` from the FAOSTAT
QCL bulk download of 2026-10-13, with the method of the WFLDB Guidelines v3.0 (section 3.2.1):

| Element | Rule |
|---|---|
| Value | FAOSTAT yield (element 5412, kg/ha), mean of 2021-2024 over the years with a value |
| Countries | the 39 countries of the tool (`faostat_country_mapping.csv`; CN = China; mainland) |
| GLO | FAOSTAT World; flax: World production / area harvested (no World yield in FAOSTAT) |
| Items | `faostat_crop_item_mapping.csv`, signed by FC: 43 exact, 16 shared, 4 group, 1 proxy, 3 none |
| Tea | FAOSTAT green leaf / 4.5 = made tea (Thevathasan & Thevadasan 1987, p. 87) |
| No item | guar, mulberry, pomegranate: GLO 0 as in the legacy table (legacy, undocumented, provisional) |

Checks: wheat FR 6775.05 (legacy 6916.7), rice IN 4267.2 (3444.3), coffee GLO 892.1 (863.5), tea
GLO 1348 (1883); after the conversion, the tea values of the main producers are within 0.9-1.3
of the legacy values. 581 crop-country pairs are new, 37 legacy pairs have no FAOSTAT value in
2021-2024 and use GLO, and 77 values differ from the legacy by more than a factor 2 (mostly small
producers, e.g. peach NZ, pineapple GH). The full comparison is in
`Literature/review_default_yield_faostat_2021_2024.csv`.

Regression: unchanged (all three cases give the yield in the template).

Yield per crop cycle (decision L24). FAOSTAT divides production by the area harvested, and the
area harvested counts every harvest, so the FAOSTAT yield is a yield per harvest. The table is
therefore read as `yield_main_product_per_crop_cycle` (the template field), and the yearly yield
is the yield per cycle times `crop_cycle_per_year`. The legacy code read the table as a yearly
yield and divided it by the crop cycles, which halved the default for crops with two harvests a
year (rice IN with two cycles: 2134 instead of 4267 kg/ha). Regression unchanged.

## 16. Potato pesticides from the WFLDB Documentation 2017 (decision L25, 2026-10-13)

The default total of pesticide active ingredients now comes from `default_pesticides.csv`. For
potato the legacy values (GD_crop Pesticides_L1) were about 27.2 times the values of the WFLDB
3.1 Documentation (Excel annex, sheet "2a) Main inputs_Arable", row 19) in all four documented
countries. They are replaced:

| Country | Legacy (kg a.i./ha) | WFLDB 2017 (kg a.i./ha) | Data level |
|---|---|---|---|
| CN | 75.23 | 2.76 | L1 |
| IN | 27.22 | 1.00 | L3 |
| RU | 23.73 | 0.87 | L1 |
| UA | 51.92 | 1.91 | L1 |
| US | 74.04 | - (uses GLO) | - |
| GLO | 50.43 | 1.635 (mean of the four) | - |

The other crops keep the legacy values, marked legacy, undocumented, provisional. Regression:
unchanged (no potato case). The other crops covered by WFLDB 2017 followed with decision L43 (section 31).

## 17. Soil erodibility from the WFLDB 2017 soil types (decision L27, 2026-10-13)

The default K factor was looked up by soil texture, classified from the clay content and a "sand
content" that was in fact the WFLDB share of sandy soils (a WRB soil type, mostly below 15 %). Almost
every country therefore fell into "medium_fine" (K 0.0438) or "fine" (0.0339). The default is now
the national average of the WFLDB Documentation 2017 (Tab. 6, p. 14): the shares of the six soil
types (Background Parameters sheet 1, rows 5-10) times the K-factor ** recalculated from Panagos et
al. (2014).

| Soil type | HAC | LAC | Sandy | Spodic | Volcanic | Wetland |
|---|---|---|---|---|---|---|
| K ** (t h/(MJ mm)) | 0.0347 | 0.01325 | 0.0122 | 0.02735 | 0.0385 | 0.0032 |

New K: IT 0.0346 (was 0.0438), IN 0.0285 (0.0438), FR 0.0335 (0.0438), BR 0.0169 (0.0339); range
0.43-0.86 x legacy. Morocco and Serbia have no WFLDB soil types and keep the texture lookup.

Regression (22 keys per case): P_surfacewater_erosion wheat_IT 0.275 -> 0.217, rice_IN 0.432 ->
0.281, apple_FR 0.066 -> 0.050 kg P/ha; heavy metals to surface water change by the same factor,
heavy metals to soil rise accordingly (less is eroded).

## 18. N uptake and mineral N computed from the yield (decision L28, 2026-10-13)

The default N uptake and mineral N were crop x country matrices (GD_crop Nuptake_L1 and
NMineral_L1). Analysis showed that they are the WFLDB L1 formula applied to the 2009-2012 yields:
N uptake = yield x (N main product + k x N residues), with the contents of the WFLDB Background
Parameters 2017 (sheet 4) and k = by-product / main product reference yield of GRUDAF 2009 (Tab. 1,
supplied by FC), and mineral N = 0.8 x N uptake (WFLDB Guidelines v3.0, 3.6.2). The formula is now
evaluated with the yield per crop cycle of the dataset, so N uptake no longer stays at the value of
an unrelated yield.

| Crop | GRUDAF 2009 Tab. 1 (dt/ha, main / by-product) | k | kg N per t main product |
|---|---|---|---|
| wheat | 60 / 70 | 1.167 | 23.82 |
| oat | 55 / 70 | 1.273 | 22.36 |
| grain maize | 95 / 105 | 1.105 | 21.07 |
| potato | 450 / 200 | 0.444 | 3.62 |
| sugar beet | 750 / 500 | 0.667 | 3.40 |
| rapeseed | 35 / 65 | 1.857 | 39.10 |
| sunflower | 30 / 60 | 2.000 | 49.50 |
| linseed | 20 / 25 | 1.250 | 62.00 |
| soybean | 30 / 30 | 1.000 | 95.00 |

Palm, sugar cane and sweet corn have no residue N in sheet 4. Asparagus, banana, carrot, onion,
peanut, rice, strawberry and tomato use the k of the legacy matrix (legacy, undocumented,
provisional). Tree crops and the crops outside sheet 4 keep the legacy matrices.

Regression: wheat_IT N uptake 56.0 (legacy GLO, no IT value) -> 154.8 kg N/ha with the template
yield 6500 kg/ha; nitrate to groundwater 123.6 -> 81.6, to surface water 53.0 -> 35.0, N2O 4.995 ->
4.835 kg/ha. rice_IN 64.5 -> 93.7 kg N/ha; nitrate to groundwater 200.6 -> 132.8, N2O 1.808 -> 1.628.
apple_FR unchanged. Mineral N is given in all three templates.

## 19. Default manure computed from the N uptake (decision L29, 2026-10-13)

The default liquid and solid manure were crop x country matrices (GD_crop ManureLiquid_L1 and
ManureSolid_L1). They follow the WFLDB L1 method (Guidelines v3.0, 3.6.2; Documentation 2017, 2.3):
the organic N is 0.2 x the N input (= N uptake), split between liquid and solid manure with the
country's FAOSTAT manure N (2009-2012; cattle, pigs and laying hens half liquid and half solid,
other animals solid), and divided by the country's mean available N (Nav, GRUDAF Nverf) per m3 of
liquid manure diluted 50 % and per t of solid manure. In every country, m3 and kg per kg N uptake
are constant across the L1 crops, and the Nav of the default manure is 0.20 x N uptake (AR 0.1995,
DE 0.1992, FR 0.2007, HU 0.2000 with the mean of the GRUDAF Nverf range). The WFLDB 2017 animal
shares are volume and mass shares (FAOSTAT N / GRUDAF total N per m3 or t).

For the 23 crops whose N uptake is computed from the yield (L28) the default manure is now:

- organic N = (1 - mineral_n_share_of_n_uptake) x N uptake, counted as available N;
- share of N applied as liquid manure and manure shares per country from FAOSTAT GLE, element
  72381 (manure applied to soils, N content), mean 2021-2023 (`faostat_manure_n_applied_country.csv`),
  items grouped by `manure_other_faostat_mapping.csv` (L13) with the WFLDB split;
- liquid m3 = organic N x liquid share / (undiluted part x Nav per m3 of the liquid mix in use),
  solid kg = 1000 x organic N x (1 - liquid share) / Nav per t of the solid mix in use.

The manure shares of all crops (`MANURE_LIQUID_RATIO_PER_COUNTRY`, `MANURE_SOLID_RATIO_PER_COUNTRY`)
now come from the same FAOSTAT data and replace the WFLDB 2017 sheet 3 shares; "other" is 0 (buffalo
with cattle, turkeys and ducks with hen and broiler litter, horses with asses and mules). The other
44 crops keep the legacy totals.

| Country | Liquid N share | m3 per kg N uptake (legacy) | kg solid per kg N uptake (legacy) |
|---|---|---|---|
| DE | 0.46 | 0.0559 (0.0563) | 39.0 (39.9) |
| FR | 0.43 | 0.0523 (0.0530) | 40.6 (42.1) |
| IN | 0.43 | 0.0522 (0.0260) | 48.0 (35.1) |
| IT | 0.48 | 0.0604 (0.0446) | 47.7 (33.6) |
| US | 0.36 | 0.0421 (0.0315) | 30.7 (26.5) |
| TR | 0.34 | 0.0360 (0.0438) | 27.3 (43.1) |
| MA | 0.16 | 0.0179 (0) | 28.4 (148.2) |
| CS | 0.45 | 0.0543 (0) | 37.5 (2220.1) |

Full table for the 39 countries, confirmed by FC: `Literature/review_manure_defaults_faostat_2021_2023.csv`.

Regression: rice_IN (default manure, N uptake 93.7 kg N/ha) liquid manure 1.68 -> 4.89 m3/ha, solid
manure 2.26 -> 4.50 t/ha (solid "other" 1.41 t -> 0); NH3 28.71 -> 34.12, N2O 1.628 -> 1.803, NOx as
N2O 4.68 -> 5.26, nitrate to groundwater 132.8 -> 137.8 kg/ha; heavy metals to soil from x0.63 (Zn)
to x2.1 (Pb), because the manure classes of the mix change. wheat_IT and apple_FR give their manure
and are unchanged.

## 20. Legume N uptake (decision L30, 2026-10-13)

The WFLDB Guidelines v3.0 (section 3.9.7.2, after Schmid et al. 2000) count only 40 % of the N
uptake of legumes: the other 60 % is fixed from the air and is not directly relevant to the balance
of N supplied by fertilisers and the soil. The legacy tool documentation (Quantis 2019, section 2.4)
has the same rule for the nitrate model, and `legume_uptake_share` = 0.4 was already in
`model_parameters.csv`, but the legacy code never used it.

The default N uptake of the legumes (column `legume` of `crop_types.csv`: soybean, peanut,
chick_pea, lentil, guar) is now `legume_uptake_share` x the uptake. With the WFLDB L1 rule N input =
N uptake, the default mineral N (L28) and manure (L29) of soybean and peanut follow, and the same
value is U of the SQCB nitrate model. Chick_pea, lentil and guar keep the legacy matrices: their
uptake is reduced, their default fertilisers are already 0.

| Crop | Country | Yield (kg/ha) | N uptake | Mineral N | Liquid manure (m3) | Solid manure (t) |
|---|---|---|---|---|---|---|
| soybean | AR | 2565 | 243.7 -> 97.5 | 194.9 -> 78.0 | 12.99 -> 5.20 | 7.92 -> 3.17 |
| soybean | BR | 3243 | 308.1 -> 123.2 | 246.5 -> 98.6 | 15.37 -> 6.15 | 9.66 -> 3.87 |
| soybean | US | 3406 | 323.6 -> 129.4 | 258.9 -> 103.6 | 13.62 -> 5.45 | 9.95 -> 3.98 |
| soybean | IN | 1092 | 103.8 -> 41.5 | 83.0 -> 33.2 | 5.42 -> 2.17 | 4.98 -> 1.99 |
| soybean | CN | 1980 | 188.1 -> 75.2 | 150.5 -> 60.2 | 7.75 -> 3.10 | 5.41 -> 2.16 |
| peanut | IN | 2024 | 152.0 -> 60.8 | 121.6 -> 48.6 | 7.94 -> 3.18 | 7.30 -> 2.92 |
| peanut | CN | 3943 | 296.1 -> 118.4 | 236.8 -> 94.7 | 12.20 -> 4.88 | 8.51 -> 3.40 |
| peanut | US | 4368 | 328.0 -> 131.2 | 262.4 -> 105.0 | 13.80 -> 5.52 | 10.08 -> 4.03 |
| chick_pea | all | - | 37.0 -> 14.8 | 0 | 0 | 0 |
| guar | all | - | 45.0 -> 18.0 | 0 | 0 | 0 |
| lentil | all | - | 0 | 0 | 0 | 0 |

N uptake and mineral N in kg N/ha and crop cycle, defaults of the default yield. Full table (5
crops, 39 countries), confirmed by FC: `Literature/review_legume_n_uptake.csv`. For comparison,
the WFLDB 3.1 L3 datasets (Documentation 2017, sheet 2a) apply 4 kg N to soybean AR and 0, 80 and
60 kg N to peanut AR, CN and IN, without manure.

Regression: no case is a legume, snapshots unchanged. In a test run of soybean BR with the default
fertilisers (rain-fed, 1400 mm), NH3 falls from 54.3 to 21.7 kg/ha and N2O from 7.25 to 3.38 kg/ha,
while nitrate to groundwater rises from 40.8 to 61.0 kg/ha: S and U of the SQCB regression fall
together, the intercept and the soil organic N term stay.

## 21. Mineral P and K from the crop offtake (decision L31, 2026-10-13)

The legacy tool had no default for mineral P and K: `p2O5_from_mineral_fert` and
`k2O_from_mineral_fert` were 0 for every crop ("No default for now, maybe in fertistat"). The
WFLDB L1 method (Guidelines v3.0 sections 3.6.1-3.6.2, Documentation 2017 sections 2.2-2.3)
derives them from the same nutrient balance as N and manure (L28, L29):

- total P2O5 (K2O) = yield per crop cycle x content of the main product (WFLDB Background
  Parameters 2017 sheet 4); for P and K only the products taken off the field count, not the
  residues;
- P2O5 (K2O) of the manure = m3 of liquid manure x undiluted part x content per m3 + t of solid
  manure x content per t (GRUDAF 2009 Table 39), for the manure in use (template or default);
- mineral P2O5 (K2O) = total - manure, 0 when the manure brings more.

The rule applies to 39 crops: the 23 of `n_uptake_crop_parameters.csv` and 16 crops with a sheet-4
content that keep the legacy N uptake and manure matrices (`pk_crop_parameters.csv`). The other 28
crops keep 0. With the yield of the L1 fertilisers the rule reproduces the WFLDB 3.1 datasets with
P and K at L1 within 4 kg (potato RU 5.6 / 42.6 against 6 / 41 kg P2O5 / K2O; carrot IL 0 / 163.8
against 0 / 167; lemon MX 0 / 11.1 against 0 / 10; tea KE and LK 0 / 0).

| Crop | Country | Yield (kg/ha) | P2O5 total | P2O5 manure | P2O5 mineral | K2O total | K2O manure | K2O mineral |
|---|---|---|---|---|---|---|---|---|
| wheat | FR | 6775 | 55.6 | 37.9 | **17.7** | 29.1 | 102.3 | **0.0** |
| wheat | IN | 3534 | 29.0 | 17.5 | **11.5** | 15.2 | 62.4 | **0.0** |
| maizegrain | US | 11091 | 65.4 | 61.5 | **3.9** | 44.4 | 122.6 | **0.0** |
| rice | IN | 4267 | 27.6 | 16.6 | **11.0** | 12.2 | 59.3 | **0.0** |
| potato | IN | 24930 | 32.4 | 18.7 | **13.7** | 134.6 | 67.0 | **67.7** |
| sugarbeet | FR | 80555 | 48.3 | 64.3 | **0.0** | 161.1 | 173.7 | **0.0** |
| soybean | BR | 3243 | 37.9 | 32.3 | **5.6** | 62.6 | 60.9 | **1.7** |
| sugarcane | BR | 74672 | 42.6 | 34.9 | **7.7** | 414.8 | 65.7 | **349.1** |
| palmtree | ID | 17354 | 39.8 | 29.8 | **10.0** | 167.3 | 44.2 | **123.1** |
| tomato_fresh | IT | 61832 | 31.2 | 29.0 | **2.2** | 180.3 | 90.6 | **89.7** |
| apple | IT | 42366 | 10.7 | 6.0 | **4.7** | 62.3 | 18.9 | **43.4** |
| orange_fresh | ES | 20994 | 15.2 | 11.0 | **4.2** | 41.7 | 23.5 | **18.2** |
| coffee_arabica | BR | 1708 | 5.0 | 11.3 | **0.0** | 24.5 | 20.9 | **3.6** |
| tea | KE | 2494 | 18.0 | 23.2 | **0.0** | 49.3 | 74.8 | **0.0** |

kg P2O5 and K2O per ha and crop cycle, defaults of the default yield and manure. Full table (39
crops, 39 countries), confirmed by FC: `Literature/review_mineral_pk_defaults.csv`. The default
manure carries 0.2 x the N uptake as available N and often more P and K than the crop takes off:
K2O is 0 for the cereals, rice, the oil crops and peanut in all countries, P2O5 for sugar beet,
linseed, asparagus and most tree crops. The WFLDB 3.1 L3 datasets apply much more, e.g. potato IN
230 kg P2O5 and 150 kg K2O, sugar beet FR 68 and 146, sunflower FR 25 and 22 (open point).

Regression: the three cases give mineral P and K in the template, snapshots unchanged. In a test
run of rice_IN without them, the default (12.9 kg P2O5, 0 K2O, against 40 and 0 in the template)
changes the P fertiliser exchanges (IN shares), the packaging of the fertilisers (320 -> 266 kg)
and the heavy metals from fertilisers (e.g. Cd to soil 0.0022 -> 0.0008 kg/ha); P run-off stays 0
(slope below 3 %).

## 22. N uptake of the tree crops computed from the yield (decision L32, 2026-10-14)

L28 kept the tree crops on the legacy matrices because their N uptake is not proportional to the
yield. It is affine: in every country of the 15 tree crops with a WFLDB sheet-4 content (46
crop-country rows), GD_crop Nuptake_L1 = yield (2009-2012) x N of the main product + 18.6 kg N/ha.
18.6 kg N = 6000 kg FM of residues per ha x 3.1 g N/kg FM, the N of haulm or stem that sheet 4 gives
for all tree crops. The amount of residues is not stated in the WFLDB reports (parameter tagged
"legacy, undocumented, provisional" by FC), but the rule reproduces the WFLDB 3.1 datasets with N
mineral at L1 (Documentation 2017 Excel annex, sheet 2c), mineral N = 0.8 x N uptake: coconut PH
43.5 against 44 kg N/ha, lemon MX 33.0 against 33, tea KE 82.1 against 82, tea LK 61.8 against 62,
pear BE 36.3 against 36 (at the GD_crop yield).

New: the 16 tree crops are in `n_uptake_crop_parameters.csv` (column `tree_residues` = yes; moved
from `pk_crop_parameters.csv`, which keeps only mint):

- N uptake = yield per crop cycle x N of the main product + `tree_crop_residues_kg_fm_per_ha`
  (6000, `model_parameters.csv`) x N of haulm or stem (`defaultTables.py`
  N_UPTAKE_OF_TREE_RESIDUES_PER_CROP);
- mineral N = 0.8 x N uptake (L28), manure from the N uptake (L29), mineral P and K = offtake minus
  manure (L31), as for the 23 crops of L28;
- citruslime -> Lemon of sheet 4 (proxy: every legacy value of citruslime equals lemon); it now
  also gets the P and K defaults (40 crops).

| Crop | Country | Yield (kg/ha) | N uptake | Mineral N | Liquid manure (m3) | Solid manure (t) | P2O5 mineral | K2O mineral |
|---|---|---|---|---|---|---|---|---|
| almond | CN | 4393 | 78.1 -> 108.1 | 62.5 -> 86.5 | 2.92 -> 4.45 | 2.32 -> 3.11 | 6.2 -> 0.0 | 17.3 -> 2.4 |
| apple | IT | 42366 | 38.2 -> 39.8 | 30.5 -> 31.8 | 1.70 -> 2.40 | 1.28 -> 1.90 | 4.7 -> 1.9 | 43.4 -> 34.8 |
| apricot | TR | 6274 | 34.1 -> 27.4 | 27.2 -> 21.9 | 1.49 -> 0.99 | 1.47 -> 0.75 | 0.0 -> 0.0 | 0.0 -> 7.1 |
| citruslime | MX | 15344 | 41.2 -> 43.8 | 33.0 -> 35.1 | 1.67 -> 2.06 | 1.07 -> 1.13 | 0.0 -> 0.0 | 0.0 -> 12.4 |
| cocoa | CI | 502 | 29.5 -> 27.6 | 23.6 -> 22.1 | 1.19 -> 0.83 | 0.75 -> 0.68 | 0.0 -> 0.0 | 8.4 -> 10.4 |
| coconut | IN | 6425 | 61.9 -> 70.7 | 49.5 -> 56.6 | 1.61 -> 3.70 | 2.17 -> 3.40 | 13.2 -> 7.2 | 86.3 -> 63.7 |
| coffee_arabica | VN | 2927 | 52.3 -> 63.2 | 41.8 -> 50.5 | 1.87 -> 2.45 | 1.43 -> 1.68 | 0.0 -> 0.0 | 18.2 -> 13.0 |
| lemon | TR | 31656 | 79.5 -> 70.6 | 63.6 -> 56.5 | 3.49 -> 2.54 | 3.43 -> 1.93 | 0.0 -> 4.4 | 3.9 -> 26.8 |
| orange_fresh | US | 16706 | 69.6 -> 46.1 | 55.7 -> 36.8 | 2.20 -> 1.94 | 1.85 -> 1.42 | 0.0 -> 0.0 | 3.1 -> 9.1 |
| orange_fresh | ZA | 45029 | 75.6 -> 92.6 | 60.5 -> 74.1 | 3.07 -> 3.76 | 2.14 -> 2.82 | 14.1 -> 8.6 | 54.2 -> 43.8 |
| pear | BE | 31914 | 45.4 -> 44.1 | 36.3 -> 35.3 | 2.56 -> 2.43 | 1.71 -> 1.59 | 0.0 -> 0.0 | 18.5 -> 20.2 |
| tea | KE | 2494 | 102.6 -> 120.1 | 82.1 -> 96.1 | 5.26 -> 5.43 | 4.67 -> 5.22 | 0.0 -> 0.0 | 0.0 -> 0.0 |

kg N, P2O5 and K2O per ha and crop cycle, legacy matrices (P and K: L31 with the legacy manure) ->
new, at the default yield (FAOSTAT 2021-2024, L23) and default manure mix. Full table (16 crops, 39
countries): `Literature/review_tree_crop_n_uptake_manure.csv`. In the 49 rows of the legacy
matrices the new N uptake is 0.66-1.38 x the legacy (median 1.07), the change coming from the
yield; the manure also takes the FAOSTAT 2021-2023 country factors of L29 (e.g. coconut IN liquid
x 2.3). In the other countries the legacy default was the GLO mean of the matrix; the new N uptake
follows the FAOSTAT yield of the country, 0.28-5.8 x the legacy GLO (tea RU 96 kg/ha: 80.7 -> 22.5;
almond IL 22712 kg/ha: 82.7 -> 481 kg N/ha, a FAOSTAT yield to check).

Unchanged (legacy, undocumented, provisional): the berries (blueberry, cranberry, raspberry, added
by Quantis in 2017: N uptake = yield x 1.58 g N/kg, the strawberry row; mineral N and manure flat
values not linked to it) and the 25 crops without default mineral N and manure (their legacy N
uptake, partly with web sources, is used by the nitrate model only; mint included).

Regression: apple_FR gives mineral N, P, K and manure in the template, so only its N uptake
changes: 34.9 (legacy GLO) -> 36.1 kg N/ha (35000 kg/ha x 0.5 g/kg + 18.6); nitrate to
groundwater 131.44 -> 131.10 kg/ha and to surface water 14.60 -> 14.57 (x 0.9974), N2O 2.3762 ->
2.3752 (x 0.9996, indirect N2O of the leached N). wheat_IT and rice_IN unchanged.

## 23. Mineral N, P and K at WFLDB level 2 with the IFA fertiliser use by crop (decision L33, 2026-10-14)

L28-L32 compute the default mineral fertilisers at WFLDB level 1, a nutrient balance: mineral N =
0.8 x N uptake, mineral P2O5 and K2O = offtake minus manure. The WFLDB Guidelines v3.0 (section
3.6.1) define level 2 as correction factors on these values from national fertiliser statistics,
naming IFA, but WFLDB never computed them (Documentation 2017 section 2.4: L2 = an L1 value
adapted by hand). L1 is far below the practice for P and K (L31: the default manure often covers
the offtake) and differs in both directions for N.

Data (supplied by FC, `data/external_data/`, read from the zip files by
`scripts/build_ifa_fertiliser_use.py`):

- IFA Fertilizer Use by Crop, Ludemann, Gruere, Heffer, Dobermann (2022), Dryad
  doi:10.5061/dryad.2rbnzs7qh, version of February 2025 (CC0): mean rate of mineral N, P2O5 and
  K2O over the total crop area per country and crop (`ifa_fubc_rates.csv`). 30 countries of the
  tool are in the 9th survey (FUBC 9, 2017-18); CH, CO, CR, EC, KE, LK have FUBC 5 (1995-2000), CI
  FUBC 4 (1994); GH and CS are not in FUBC and take the FUBC 9 countries of their IFA region.
- FAOSTAT Fertilizers by Nutrient, use per area of cropland (`faostat_fertiliser_use_country.csv`):
  the FUBC 9 and region rates are multiplied by the ratio 2021-2023 / FUBC year of the country
  (median 0.95; from 0.38 for P2O5 ID to 3.34 for P2O5 PH, a single base year). The earlier
  reports are used without it: over 20-30 years the national trend gave factors up to 6 (banana EC
  1686 kg K2O/ha).
- FUBC crop names -> crops of the tool (`ifa_fubc_crop_mapping.csv`, 96 names): exact crop,
  subgroup (e.g. citrus for oranges, lemons and mandarins) or group (fruits and tree nuts,
  vegetables, other cereals, other oil crops, roots and tubers); per country the best level, the
  rows of that level combined by area (e.g. irrigated and rainfed rice KE).

Method (`defaultGeneration.py` _level2), for N, P2O5 and K2O of the 40 crops with L1 coefficients:

- k = (IFA rate + L1 manure) / L1 need, at the default yield of the crop and country with the
  default manure; need = N uptake (N) or offtake (P2O5, K2O), manure = organic N share of the N
  uptake (N) or P2O5 and K2O of the default manure;
- mineral fertiliser = max(0, k x need - manure), with the yield of the dataset and the manure in
  use (P, K); for N this is the IFA rate x N uptake / N uptake at the default yield;
- at the default yield the default equals the IFA rate; without an IFA rate the default stays L1.

| Crop | Country | Yield (kg/ha) | IFA data | Mineral N | P2O5 | K2O | WFLDB L3 N / P2O5 / K2O |
|---|---|---|---|---|---|---|---|
| wheat | FR | 6775 | FUBC 9, Wheat | 129.1 -> **149.5** | 17.7 -> **15.0** | 0.0 -> **13.0** | |
| wheat | IN | 3534 | FUBC 9, Wheat | 67.3 -> **128.1** | 11.5 -> **38.5** | 0.0 -> **4.2** | |
| maizegrain | US | 11091 | FUBC 9, Maize, Total (group) | 186.9 -> **157.5** | 3.9 -> **51.8** | 0.0 -> **57.5** | |
| rice | IN | 4267 | FUBC 9, Rice | 64.0 -> **154.3** | 11.0 -> **59.6** | 0.0 -> **16.2** | 120 / 60 / 60 |
| potato | IN | 24930 | FUBC 9, Roots & Tubers (group) | 72.2 -> **99.0** | 13.7 -> **59.9** | 67.6 -> **31.4** | 250 / 230 / 150 |
| sugarbeet | FR | 80555 | FUBC 9, Sugar beet | 219.1 -> **90.6** | 0.0 -> **39.5** | 0.0 -> **60.7** | 103 / 68 / 146 |
| soybean | BR | 3243 | FUBC 9, Soybeans | 98.6 -> **22.6** | 5.6 -> **101.4** | 1.7 -> **107.7** | |
| soybean | AR | 2565 | FUBC 9, Soybeans | 78.0 -> **0.0** | 4.6 -> **9.7** | 0.4 -> **0.0** | 4 / 12 / 0 |
| sugarcane | BR | 74672 | FUBC 9, Sugar Cane | 106.3 -> **109.8** | 7.7 -> **22.3** | 349.1 -> **79.2** | 52 / 48 / 110 |
| palmtree | ID | 17354 | FUBC 9, Oil palm fruit | 83.3 -> **96.8** | 10.0 -> **18.6** | 123.1 -> **125.3** | - / - / 345 |
| tomato_fresh | IT | 61832 | FUBC 9, Vegetables (group) | 105.0 -> **88.9** | 2.2 -> **38.5** | 89.7 -> **80.6** | |
| apple | IT | 42366 | FUBC 9, Fruits & Treenuts (group) | 31.8 -> **52.8** | 1.9 -> **7.3** | 34.8 -> **16.7** | 50 / 35 / 58 |
| lemon | ES | 19181 | FUBC 9, Fruits & Treenuts (group) | 40.1 -> **49.6** | 1.5 -> **17.3** | 11.5 -> **18.1** | 230 / 90 / 300 |
| coffee_arabica | BR | 1708 | FUBC 9, Coffee | 35.7 -> **232.5** | 0.0 -> **45.9** | 2.5 -> **136.8** | |
| tea | KE | 2494 | FUBC 5 1997, Tea | 96.1 -> **50.0** | 0.0 -> **10.0** | 0.0 -> **10.0** | |
| banana | EC | 38961 | FUBC 5 1995, Banana | 62.9 -> **210.0** | 0.0 -> **14.0** | 168.7 -> **280.0** | 265 / 3 / 131 |

kg per ha and crop cycle, L1 -> L2 at the default yield and default manure. Full table (40 crops,
39 countries, with the FUBC rows, the time factors and k), confirmed by FC:
`Literature/review_ifa_l2_defaults.csv`. Of the 1018 crop-country pairs, 238 have an exact FUBC
crop, 36 a subgroup, 581 a group and 163 no rate (L1 kept). Mean over the pairs with a rate:
mineral N 68 -> 99, P2O5 3 -> 51, K2O 42 -> 58 kg/ha. Against the 57 WFLDB 3.1 datasets with L3 or
L4 data, L2 is closer than L1 for P2O5 in 42 (median deviation 50 -> 33 kg), for N in 35 and for
K2O in 28. A group rate averages different crops: in Europe "Fruits & Treenuts" includes vineyards
and nuts, so intensive crops get less than the WFLDB L3 data (lemon ES 50 against 230 kg N).

Regression: the three cases give the mineral fertilisers in the template, snapshots unchanged.

## 24. Mineral N, P and K of the crops without level 1 coefficients from the IFA rates (decision L34, 2026-10-14)

L28-L33 cover the 40 crops with a nutrient content in the WFLDB Background Parameters 2017 (sheet
4). The other 28 crops had no default mineral fertilisers (25 crops: 0 kg N, P2O5 and K2O, 0
manure) or flat legacy values (blueberry, cranberry, raspberry: mineral N of the Quantis 2017
matrix, e.g. 87 kg N/ha, no P and K). Mint has P and K contents (L31, L33) but no N default.

New: the IFA Fertilizer Use by Crop rates of L33 (`ifa_fubc_rates.csv`, same time scaling and
region fallback) give these crops a default where FUBC has a matching category.

- `ifa_fubc_crop_mapping.csv` (96 -> 110 rows, confirmed by FC):
  - exact: Cotton and Seed cotton -> cotton, Cassava, Pineapple (CR), Vineyards (ZA) and
    Vineyards + Raisins (AR) -> grape, Ginger and Sesame (NG and SN, for GH);
  - subgroup: Millet -> pearl millet (for GH), the three Pulses names -> chick pea, lentil, guar,
    fresh herbs (IL) -> coriander, mint, and the TH fruit and vegetable subgroups (pineapple,
    mango, cashew; bell pepper, chilli);
  - group: the fruit groups of L33 -> berries, grape, mango, cashew, pineapple, pomegranate (in
    Europe 'Fruits & Treenuts' is 'nuts, herbs, bushes, vineyards'); the vegetable groups -> bell
    pepper, chilli, eggplant, red and white cabbage; Roots & Tubers -> cassava; other oil crops ->
    sesame, castor beans; other cereals and Mil - Sorghum (ML) -> pearl millet;
  - not used: rows mixing cereals and pulses (NZ 'Grain and other crops', UA 'Other cereal and
    leguminous crops') for the pulses, UA 'Other industrial crops' for flax and hemp, and the
    residual categories 'Other crops' and 'Residual'.
- Method (`defaultGeneration.py` MineralNitrogenDefaultGenerator.need,
  MineralPhosphorusPotassiumDefaultGenerator.balance): the L33 correction with the nutrient need
  taken proportional to the yield, the content being unknown and cancelling in k:
  - N = IFA rate x yield / default yield (the template manure is not used, as in L28 and L33);
  - P2O5 and K2O = max(0, k x yield - manure in use), k = (IFA rate + P2O5 (K2O) of the default
    manure) / default yield;
  - at the default yield and default manure the default equals the IFA rate; without an IFA rate
    the defaults are unchanged.
- Unchanged: the manure (0 for the 25 crops, legacy matrices for the berries) and the legacy N
  uptake used by the nitrate model.

| Crop | Country | Yield (kg/ha) | IFA data | Mineral N | P2O5 | K2O |
|---|---|---|---|---|---|---|
| cotton | IN | 1265 | FUBC 9, Cotton | 0.0 -> **139.2** | 0.0 -> **56.7** | 0.0 -> **12.1** |
| cotton | US | 2818 | FUBC 9, Cotton | 0.0 -> **81.9** | 0.0 -> **27.6** | 0.0 -> **38.7** |
| cassava | TH | 20837 | FUBC 9, Cassava | 0.0 -> **93.0** | 0.0 -> **44.6** | 0.0 -> **82.7** |
| cassava | VN | 20250 | FUBC 9, Roots and Tubers, Total (group) | 0.0 -> **50.2** | 0.0 -> **10.7** | 0.0 -> **10.3** |
| cassava | BR | 15233 | FUBC 9, Roots & Tubers (group, potato only) | 0.0 -> **212.3** | 0.0 -> **452.8** | 0.0 -> **364.0** |
| chick_pea | IN | 1194 | FUBC 9, Pulses | 0.0 -> **32.4** | 0.0 -> **16.6** | 0.0 -> **1.7** |
| lentil | TR | 1331 | FUBC 9, Pulses | 0.0 -> **56.5** | 0.0 -> **61.5** | 0.0 -> **0.0** |
| pearl_millet | IN | 1416 | FUBC 9, Other Cereals (group) | 0.0 -> **74.7** | 0.0 -> **19.8** | 0.0 -> **2.5** |
| sesame_seed | IN | 490 | FUBC 9, Other Oil Crops (group) | 0.0 -> **56.6** | 0.0 -> **27.0** | 0.0 -> **6.3** |
| grape | ZA | 17795 | FUBC 9, Vineyards | 0.0 -> **58.4** | 0.0 -> **48.5** | 0.0 -> **22.8** |
| grape | FR | 7380 | FUBC 9, Fruits & Treenuts (group) | 0.0 -> **31.9** | 0.0 -> **15.8** | 0.0 -> **16.3** |
| mango | IN | 9758 | FUBC 9, Fruits & Treenuts (group) | 0.0 -> **90.1** | 0.0 -> **33.3** | 0.0 -> **31.4** |
| pineapple | CR | 66568 | FUBC 5 1997, Pineapple | 0.0 -> **160.0** | 0.0 -> **80.0** | 0.0 -> **280.0** |
| bellpepper | ES | 66401 | FUBC 9, Vegetables (group) | 0.0 -> **161.3** | 0.0 -> **55.3** | 0.0 -> **69.9** |
| blueberry | US | 7046 | FUBC 9, Fruits & Treenuts (group) | 87.0 -> **83.6** | 0.0 -> **15.5** | 0.0 -> **50.8** |
| raspberry | DE | 7529 | FUBC 9, Fruits & Treenuts (group) | 99.7 -> **30.8** | 0.0 -> **5.0** | 0.0 -> **35.4** |

kg per ha and crop cycle, current -> new at the default yield (FAOSTAT 2021-2024, L23) and default
manure. Full table (28 crops, 39 countries, with the FUBC rows and the match level), confirmed by
FC: `Literature/review_ifa_other_crops.csv`. Of the 489 crop-country pairs, 23 have an exact FUBC
crop, 18 a subgroup, 281 a group and 167 no rate (all of coriander, turmeric, flax, hemp and mint;
most of ginger, lentil, sesame and chick pea). Mean over the 322 pairs with a rate: mineral N
11.8 -> 101.9, P2O5 0 -> 56.4, K2O 0 -> 59.8 kg/ha; berries N median 87 -> 70 (6-168). No WFLDB 3.1
dataset of these crops to compare with.

Limits: the Roots & Tubers row of BR covers potato only (IFA area 125.5 kha against FAOSTAT 2018
potato 119.6 kha and cassava 1216 kha), so cassava BR gets a potato rate; the vegetable groups
are open-field rates, also for greenhouse yields (bell pepper NL 265 t/ha); a need proportional to
the yield overstates the yield response of tree crops (affine in L32); guar, mulberry and
pomegranate have no default yield, hence no reference, and keep their defaults (guar has the
pulses rate). Open: default manure of the 25 crops.

Regression: the three cases are other crops, snapshots unchanged; the defaults of the 40 crops of
L33 are unchanged.

## 25. Three-year base of the FAOSTAT time factor; soybean mineral N (decisions L35, L36, 2026-10-14)

L33 brings the FUBC 9 and region rates to 2021-2023 with the ratio of the FAOSTAT use per area of
cropland, 2021-2023 mean over the FUBC 9 reference year of the country. One base year is sensitive
to the year-to-year variation of the FAOSTAT series (CS N: 77.5, 41.7, 46.8 kg/ha in 2017, 2018,
2019).

New (L35): the base is the mean over the reference year with the year before and after (e.g.
2017-2019), as the target is a 3-year mean (`scripts/build_ifa_fertiliser_use.py` BASE_WINDOW,
`faostat_fertiliser_use_country.csv` rebuilt; `ifa_fubc_rates.csv` unchanged).

| Country | Nutrient | Base years | Factor, one year | Factor, three years |
|---|---|---|---|---|
| CS | N | 2017-2019 | 1.71 | **1.29** |
| CS | P2O5 | 2017-2019 | 2.80 | **1.74** |
| PH | P2O5 | 2017-2019 | 3.34 | **2.57** |
| PH | K2O | 2017-2019 | 1.67 | **1.38** |
| TH | P2O5 | 2017-2019 | 2.16 | **1.87** |
| TH | K2O | 2017-2019 | 1.53 | **1.73** |
| GH | P2O5 | 2017-2019 | 1.41 | **0.97** |
| PE | N | 2017-2019 | 1.04 | **0.83** |
| CA | K2O | 2018-2020 | 1.93 | **1.57** |
| TR | P2O5 | 2017-2019 | 1.23 | **0.99** |
| ZA | K2O | 2017-2019 | 0.95 | **1.15** |

The 11 largest of the 17 changes above 10 % (of 96 factors). Range of the factors 0.38-3.34 ->
0.44-2.57, median 0.95 -> 0.93. The defaults of the 1033 crop-country pairs with a FUBC 9 or region
rate change, 518 by more than 10 %, all in CA, CL, CS, GH, ID, PE, PH, TH, TR, VN, ZA (e.g. wheat CS
N 225 -> 170 kg/ha, vegetables CS P2O5 145 -> 90). Against the WFLDB 3.1 datasets with L3/L4 data
the change is neutral (median deviation N 42.0 -> 41.9, P2O5 33.0 -> 35.2, K2O 61.2 -> 67.0 kg/ha):
these datasets are older than 2021-2023.

L36: point 5 of the queue (soybean mineral N, about 100 kg N/ha at level 1 after L30) is closed by
L33 without code change: the soybean default is the IFA rate in 27 of 32 countries, median 72 -> 23
kg N/ha (AR 0 against 4 in the WFLDB L3 dataset). Still at level 1: soybean CI, KE, PE, PH, LK and
peanut AR, BR, CN, which have no IFA rate for the crop (region rates since L37, section 26).

Regression: snapshots unchanged.

## 26. IFA region rate for the crops missing in the FUBC data of a country (decision L37, 2026-10-14)

L33 and L34 take the IFA rate from the FUBC data of the country only (GH and CS: their IFA region).
A crop missing there stayed at level 1 (crops with L1 coefficients) or without default (other
crops): e.g. soybean in PE and PH (not in FUBC 9 of these countries) and in CI, KE, LK (earlier
reports without soybean), peanut in AR, BR, CN, the fruits other than apples and citrus in CN.

New (`defaultTables.py` _ifa_region_median):

- the FUBC data of the country first, at any match level and from any report, as before;
- otherwise the FUBC 9 countries of the IFA region of the country: per country the rate at the best
  match level (rows of that level combined by area), then the median over the countries at the best
  level found in the region, with at least 2 countries;
- brought to 2021-2023 with the FAOSTAT factor of the country (L35). The countries with an earlier
  report only (CH, CI, CO, CR, EC, KE, LK) get a factor (base 2017-2019, 21 new rows of
  `faostat_fertiliser_use_country.csv`), used only for these region rates;
- GH and CS follow the same rule (before: area-weighted mean of all the region rows).

| Crop | Country | Region rate from | Current | New | WFLDB L3 |
|---|---|---|---|---|---|
| soybean | PE | Latin America, Soybeans (6 countries) | 66.9 / 2.6 / 5.7 | **1.7 / 21.2 / 15.9** | |
| soybean | CI | Africa, Soybeans (3 countries) | 44.5 / 1.6 / 4.9 | **16.6 / 15.2 / 2.5** | |
| soybean | LK | South Asia, Soybeans (2 countries) | 59.7 / 4.7 / 0.0 | **46.4 / 16.3 / 6.4** | |
| peanut | AR | Latin America, Other Oil Crops (3 countries) | 75.0 / 0.0 / 0.0 | **5.5 / 4.6 / 1.0** | 0 / 0 / 0 |
| peanut | CN | East Asia, Other Oil Crops (3 countries) | 94.7 / 0.0 / 0.0 | **6.1 / 3.5 / 1.8** | 80 / 27 / 28 |
| peach | CN | East Asia, fruit groups (6 countries) | 33.8 / 0.0 / 25.5 | **116.2 / 48.0 / 51.8** | 160 / 40 / 40 |
| cotton | AR | Latin America, Cotton (5 countries) | 0.0 / 0.0 / 0.0 | **63.7 / 35.6 / 43.9** | |
| maizegrain | LK | South Asia, Maize (3 countries) | 56.8 / 2.5 / 0.0 | **113.3 / 22.4 / 23.4** | |
| cassava | CO | Latin America, Roots & Tubers (7 countries) | 0.0 / 0.0 / 0.0 | **97.5 / 49.2 / 68.2** | |
| wheat | CS | Western and Central Europe, Wheat (23 countries) | 169.6 / 42.4 / 16.6 | **158.5 / 40.1 / 12.7** | |
| maizegrain | GH | Africa, Maize (8 countries) | 43.0 / 12.0 / 4.3 | **40.0 / 15.0 / 8.4** | |

kg N / P2O5 / K2O per ha and crop cycle at the default yield, current (after L35) -> new. Full
table (233 changed pairs), confirmed by FC: `Literature/review_ifa_region_fallback.csv`.

- 179 pairs get a rate (exact 35, subgroup 9, group 135): mean N 29.4 -> 72.8, P2O5 1.0 -> 31.8,
  K2O 14.5 -> 32.0 kg/ha.
- 49 pairs of GH and CS change with the median (mean N 105 -> 88 kg/ha); 5 pairs of GH lose a rate
  that came from Nigeria alone (cassava, coffee arabica and robusta, ginger, processing tomato).
- 1351 of the 1504 pairs with a default yield now have an IFA rate.

Rejected: the area-weighted mean over the region rows, dominated by China in East Asia (cotton PH
282 / 477 / 65, vegetables TH 360 / 339 / 242); region rates from one country (tea of Latin America
0, coriander TR 313 / 149 / 354 from the fresh herbs of IL, citrus TH 445 / 505 / 418 from CN).

Limits: the factor of the country multiplies the region rate, so marginal crops in countries with
a high factor get high values (TH P2O5 1.87: wheat TH 202 / 234 / 127, tea TH 533 / 215 / 206).

Regression: snapshots unchanged.

## 27. NH3 of mineral N fertilisers and NO from EMEP/EEA 2023 (decisions L38, L39, 2026-10-14)

The NH3 after mineral N fertiliser application used the factors of EMEP/EEA 2016 3.D Table 3-2,
written in `fertilisermodel.py` without a source comment: 10 fertiliser types x 3 climates
(cool, temperate, warm) x 2 pH classes, in kg NH3-N per kg N, times 17/14.

New: EMEP/EEA 2023 3.D Tier 2, Table 3-2 (p. 17), in `data/emep2023_3d_table3_2.csv`:

- g NH3 per kg N applied, on soils of normal pH (<= 7.0) and high pH (> 7.0); the 2023 table has
  no climate classes (the meta-analysis of Annex 1 A1.1.2 found no significant effect of the
  temperature);
- NH3 = sum over the types of kg N x (p x EF normal pH + (1 - p) x EF high pH), with p =
  `soil_with_ph_under_or_7`; hydroponic greenhouses keep p = 1 as in the legacy code;
- legacy types to Table 3-2 rows in `data/emep2023_fertiliser_type_mapping.csv`, signed by FC.

| Legacy type | Table 3-2 row | Legacy, temperate (normal / high pH) | 2023 (normal / high pH) |
|---|---|---|---|
| ammonium nitrate | AN | 0.012 / 0.036 | **0.024 / 0.052** |
| urea | Urea | 0.158 / 0.170 | **0.195 / 0.206** |
| urea AN | N solutions (note e) | 0.097 / 0.097 | **0.087 / 0.161** |
| MAP, DAP | AP (note c) | 0.049 / 0.097 | **0.084 / 0.187** |
| ammonium nitrate phosphate | NP mixtures | 0.073 / 0.097 | **0.084 / 0.187** |
| calcium ammonium nitrate | CAN | 0.012 / 0.012 | **0.024 / 0.052** |
| ammonium sulphate | AS | 0.097 / 0.170 | **0.084 / 0.187** |
| potassium nitrate | NK mixtures | 0.073 / 0.097 | **0.024 / 0.052** |
| liquid ammonia | Anhydrous ammonia (AH) | 0.024 / 0.036 | **0.020 / 0.020** |

kg NH3 per kg N. The legacy warm-climate factors were higher than the temperate ones (urea 0.194 /
0.206). Ammonium nitrate phosphate and potassium nitrate were both "other complex NK, NPK" in the
2016 table; in 2023 they follow the IFA categories of Annex Table A1.1 (Other NP, N K compound).

Transcription: the `-layout` text of the PDF shifts the rows; `-table` and `-raw` agree with each
other and with Annex Table A1.1 (pp. 32-33), where each factor is the NH3-N % of the base model
category x 17/14. Exception: Other straight N compounds prints 24 g for normal pH, the Annex gives
84 (its weighted average agrees only with 84). The row is transcribed as printed with a note; no
legacy type uses it.

With the default N fertiliser mix and pH share of the 39 countries, the mean factor per kg N changes
by x0.93 (FI) to x1.49 (NL), median x1.23 (`Literature/review_emep2023_fertiliser_nh3.csv`).

Not applied: the 22 % for urea and AS on rice paddies cited in Annex 1 (Yan et al. 2003, guidance
kept from the 2019 Guidebook, not a Table 3-2 factor). Open.

Regression (kg/ha and crop cycle):

| Case | ammonia_total | N2o_air | Nox_as_n2o_air | nitrate_to_groundwater |
|---|---|---|---|---|
| apple_FR | 6.822 -> 7.829 | 2.375 -> 2.387 | 4.554 -> 4.521 | 131.10 -> 130.86 |
| wheat_IT | 31.704 -> 35.400 | 4.835 -> 4.877 | 6.795 -> 6.673 | 81.58 -> 80.27 |
| rice_IN | 34.118 -> 34.104 | 1.8027 -> 1.8026 | 5.2608 -> 5.2613 | 137.85 -> 137.88 |

`nitrate_to_surfacewater` follows the groundwater change (apple_FR 14.567 -> 14.540, wheat_IT
34.961 -> 34.401). No other output changes.

NO (decision L39): the NO emission factor of fix F1 (L3) cited EMEP/EEA 2016 3.D Table 3-1. The
2023 Table 3-1 (p. 14) keeps 0.04 kg NO2 per kg fertiliser and manure N applied (note a: NO reported
as NO2; Skiba et al. 2021, 95 % CI 0.005-0.104), so `ef_nox_n` stays 0.012174 kg NOx-N/kg N; only
the citations change. No numerical change.

## 28. Default manure of the crops without level 1 coefficients (decision L40, 2026-10-15)

L29 and L32 compute the default manure of the 40 crops with WFLDB level 1 coefficients from the N
uptake: available N of the manure = 0.2 x N uptake. The other 28 crops (L34) had no default manure
(25 crops: 0) or flat legacy values (blueberry, cranberry, raspberry: Quantis 2017, without source;
available N 1.5-2.4 x the legacy N uptake, so not the WFLDB rule). L34 gave them a mineral N from the
IFA rates where FUBC has a matching category.

New (`defaultGeneration.py` ManureDefaultGenerator.organic_n):

- available N of the manure (GRUDAF 2009 Table 39 Nverf) = (1 - s) / s x level 2 mineral N, with s =
  `mineral_n_share_of_n_uptake` = 0.8: the WFLDB L1 split of the N input (Guidelines v3.0 section
  3.6.2, 20 % organic and 80 % mineral) applied to the IFA-based mineral N, i.e. 0.25 x IFA rate x
  yield / default yield;
- split into liquid and solid manure and converted to m3 and kg as in L29 (FAOSTAT 2021-2023 share of
  manure N applied as liquid manure, manure mix in use, dilution of the liquid manure);
- the default manure follows the default mineral N, not the mineral N of the template;
- the mineral N, P2O5 and K2O at the default yield stay the IFA rates: the L33 factor k includes the
  default manure, which comes on top of the IFA rate (IFA counts mineral fertilisers only); the
  reference of the factor is now computed per nutrient, since the default manure of these crops
  depends on the N factor;
- no IFA N rate or no default yield: the legacy matrix stays (0 for these pairs).

| Crop | Country | Yield (kg/ha) | Mineral N | Manure (m3 + t) | Available N | Total N | P2O5 | K2O |
|---|---|---|---|---|---|---|---|---|
| cotton | IN | 1265 | 137.8 | 0.00 + 0.00 -> **9.00 + 8.26** | 0.0 -> **34.4** | 0.0 -> **72.8** | 0.0 -> **35.7** | 0.0 -> **127.7** |
| cotton | BR | 4170 | 337.4 | 0.00 + 0.00 -> **21.04 + 13.23** | 0.0 -> **84.3** | 0.0 -> **166.0** | 0.0 -> **110.6** | 0.0 -> **208.5** |
| cassava | TH | 20837 | 90.1 | 0.00 + 0.00 -> **4.59 + 3.14** | 0.0 -> **22.5** | 0.0 -> **44.9** | 0.0 -> **29.8** | 0.0 -> **55.5** |
| chick_pea | IN | 1194 | 32.1 | 0.00 + 0.00 -> **2.09 + 1.92** | 0.0 -> **8.0** | 0.0 -> **17.0** | 0.0 -> **8.3** | 0.0 -> **29.7** |
| pearl_millet | IN | 1416 | 73.9 | 0.00 + 0.00 -> **4.83 + 4.43** | 0.0 -> **18.5** | 0.0 -> **39.1** | 0.0 -> **19.2** | 0.0 -> **68.5** |
| grape | FR | 7380 | 31.8 | 0.00 + 0.00 -> **2.08 + 1.62** | 0.0 -> **8.0** | 0.0 -> **16.4** | 0.0 -> **9.3** | 0.0 -> **25.2** |
| grape | ZA | 17795 | 58.8 | 0.00 + 0.00 -> **2.98 + 2.24** | 0.0 -> **14.7** | 0.0 -> **28.7** | 0.0 -> **19.1** | 0.0 -> **36.3** |
| mango | IN | 9758 | 89.1 | 0.00 + 0.00 -> **5.82 + 5.35** | 0.0 -> **22.3** | 0.0 -> **47.1** | 0.0 -> **23.1** | 0.0 -> **82.6** |
| pineapple | CR | 66568 | 160.0 | 0.00 + 0.00 -> **10.90 + 8.24** | 0.0 -> **40.0** | 0.0 -> **82.6** | 0.0 -> **47.4** | 0.0 -> **126.1** |
| chilli | CN | 22458 | 248.5 | 0.00 + 0.00 -> **12.80 + 8.93** | 0.0 -> **62.1** | 0.0 -> **121.9** | 0.0 -> **80.8** | 0.0 -> **151.2** |
| bellpepper | ES | 66401 | 160.7 | 0.00 + 0.00 -> **11.83 + 7.41** | 0.0 -> **40.2** | 0.0 -> **78.2** | 0.0 -> **49.7** | 0.0 -> **106.6** |
| blueberry | US | 7046 | 82.9 | 2.81 + 2.36 -> **4.36 + 3.19** | 14.6 -> **20.7** | 29.9 -> **41.9** | 19.7 -> **27.3** | 38.5 -> **54.4** |
| raspberry | DE | 7529 | 29.5 | 1.87 + 8.70 -> **2.06 + 1.44** | 27.3 -> **7.4** | 64.0 -> **14.9** | 42.2 -> **8.9** | 89.1 -> **21.8** |
| raspberry | CS | 5361 | 55.7 | 0.00 + 20.00 -> **3.78 + 2.61** | 58.4 -> **13.9** | 137.7 -> **27.8** | 92.1 -> **16.8** | 194.6 -> **40.0** |

kg per ha and crop cycle at the default yield (FAOSTAT 2021-2024, L23), current -> new; mineral N
unchanged (IFA rate); the nutrients are those of the default manure (GRUDAF 2009 Table 39, liquid
manure x undiluted part). Full table (28 crops, 39 countries): `Literature/review_manure_other_crops.csv`.
Of the 489 crop-country pairs of `default_yield.csv`, 389 get the new manure; 279 more pairs with the
GLO default yield follow the same rule; 424 pairs keep the legacy manure, which is 0 (all of flax,
ginger, hemp and turmeric; guar, mulberry and pomegranate without default yield; the pairs of other
crops without IFA N rate). Mean over the 389 pairs: available N 2.5 -> 23.3 kg/ha, total N 5.4 ->
46.6, P2O5 3.6 -> 30.2, K2O 7.1 -> 60.8.

WFLDB check (Documentation 2017 Excel annex, sheets 2a-2c, WFLDB 3.0 datasets): the 20 datasets with
manure at L1 all have about 20 % organic N (median 0.19 of available plus mineral N); of the 71
datasets with manure at L3, 42 have none and the mean organic share is 6 % (strawberry and mint 0).
The L1 rule is the WFLDB default but likely overstates the manure of horticultural and perennial
crops. Mint (IN, US) is the only one of the 28 crops in WFLDB 3.0, without manure.

Rejected: 0.2 x the legacy N uptake of these crops (undocumented, already rejected in L32; it would
give manure to mint and coriander without mineral N and none to lentil); keeping 0.

Regression: the three cases are other crops, snapshots unchanged; the defaults of the 40 crops of
L28-L33 are unchanged.

## 29. N uptake of the crops without level 1 coefficients (decision L41, 2026-10-15)

The SQCB nitrate model uses the N uptake of the crop (U, kg N/ha): more uptake, less leaching. For the 40 crops with
WFLDB level 1 coefficients U follows the yield (L28, L32). The other 28 crops kept the legacy GD_crop matrix: flat
values per crop, mostly the IN value copied to GLO, independent of the yield, without source; pineapple had a rule
in the code (2 % of the dry yield). At the GLO default yield some legacy values give implausible contents (cashew 155,
sesame 65, pearl millet 60, coriander 52 g N/kg); lentil had 0. Only the nitrate model uses this uptake: the mineral
N (L34) and the manure (L40) of these crops follow the IFA rates.

New (`defaultTables.py` N_UPTAKE_PER_KG_MAIN_PRODUCT_OTHER_CROPS, `n_uptake_other_crop_parameters.csv`, signed by
FC): U = yield per crop cycle x N per kg of main product, legumes x 0.4 (L30).

- N of the crop product: Ludemann et al. 2023, Global data on crop nutrient concentration and harvest indices
  (Dryad doi:10.5061/dryad.n2z34tn0x, CC0, zip supplied by FC), Tier 1 world coefficients of the 2023 FAO Cropland
  Nutrient Budget (`ludemann2023_world_crop_coefficients.csv`, all 158 items, built by
  `scripts/build_ludemann_crop_coefficients.py`); FAO item as for the default yield (L23); turmeric -> Ginger, guar ->
  Pulses nes, pomegranate -> Fruit, fresh nes. Tier 2 (countries) is almost empty for these crops.
- Fibre flax and fibre hemp: GRUDAF 2009 Tab. 1, main and by-product (Faserlein: 45 dt fibres 45 kg N, 15 dt seeds
  82 kg N; Faserhanf: 100 dt stems 30 kg N, 40 dt seeds and leaves 110 kg N); the Ludemann items are fibre and tow
  and 'Hemp tow waste' with generic fibre contents.
- Field crops: plus the above-ground residues of IPCC 2019 Refinement Vol. 4 Table 11.1a, DRY x R_AG x N_AG
  (`ipcc2019_table11_1a.csv`, 21 rows transcribed): Beans and Pulses 15.3 g N/kg (chick pea, lentil, guar), Millet
  8.8 (pearl millet), Potatoes and Tubers 1.7 (cassava), generic row 6.8 (cotton, sesame, castor beans, coriander).
  Vegetables, fruit, berries and spices: product only (no source for their residues).
- Mulberry keeps the legacy matrix (no source).

| Crop | Country | Yield (kg/ha) | Source | U (kg N/ha) |
|---|---|---|---|---|
| cotton | IN | 1265 | Seed cotton + IPCC generic | 41.0 -> **82.6** |
| cassava | TH | 20837 | Cassava + IPCC Potatoes and Tubers | 100.0 -> **86.3** |
| chick_pea | IN | 1194 | Chick peas + IPCC Beans and Pulses, x 0.4 | 14.8 -> **20.4** |
| lentil | TR | 1331 | Lentils + IPCC Beans and Pulses, x 0.4 | 0.0 -> **27.2** |
| pearl_millet | IN | 1416 | Millet + IPCC Millet | 84.3 -> **44.9** |
| grape | FR | 7380 | Grapes | 30.0 -> **23.4** |
| mango | IN | 9758 | Mangoes, mangosteens, guavas | 120.0 -> **39.4** |
| pineapple | CR | 66568 | Pineapples | 173.1 -> **68.6** |
| chilli | CN | 22458 | Chillies and peppers, green | 150.0 -> **48.6** |
| cabbage_white | IN | 23306 | Cabbages and other brassicas | 247.0 -> **89.6** |
| ginger | IN | 11577 | Ginger | 92.3 -> **145.8** |
| turmeric | IN | 11577 | Ginger | 42.5 -> **145.8** |
| flax | FR | 5438 | GRUDAF Faserlein | 20.0 -> **153.5** |
| hemp | CN | 5653 | GRUDAF Faserhanf | 100.0 -> **79.1** |
| blueberry | US | 7046 | Blueberries | 11.4 -> **7.3** |
| mint | IN | 21510 | Peppermint | 160.0 -> **245.8** |

At the default yield (FAOSTAT 2021-2024, L23), legacy -> new. Full table (28 crops, 39 countries):
`Literature/review_n_uptake_other_crops.csv`, confirmed by FC. Over the 489 crop-country pairs of
`default_yield.csv`, mean U 102.8 -> 80.5 kg N/ha, lower in 334 pairs (vegetables, tropical fruit), higher in 155
(cotton, ginger, turmeric, flax, mint, lentil). Guar and pomegranate have no default yield: U is 0 at the default and
follows the yield of the template.

Cross-check of Ludemann Tier 1 against WFLDB sheet 4 for the crops of L28: wheat 1.02, maize 0.95, rice 1.00, potato
0.91, soybean 0.93, tomato 0.88, banana 0.94; carrot and onion 1.3; tree fruit and strawberry 2-5 x (apple 4.8, pear
2.9, peach 2.2, strawberry 5.4). For grape Tier 1 gives 3.2 kg N/t, Tier 2 Europe 0.42. Other local sources checked:
PRIC 2024 chapter 14 (berries: N fertilisation norms, which include the soil mineralisation, not an uptake),
Agribalyse 3.1 Table 114 (U of grape only, per t DM), IPCC 2019 Table 11.1a (residues only).

Open: seed cotton 58.5 kg N/t (mean of 4.75 % and 6.4 % N in fresh seed cotton; Zhang et al. 2021 give 3.34 % in the
dry matter) and castor beans 14.4 kg N/t (the mean includes the row 'Oil of Castor Beans' with 0 N; the seed row of the
same source is 28.8), both kept as published; no residues for vegetables, fruit, berries and spices, so their U is
underestimated (vegetables especially); fruit contents above WFLDB sheet 4.

Regression: the three cases are other crops, snapshots unchanged.

## 30. Liquid and solid manure split from the IPCC 2019 manure management systems (decision L42, 2026-10-15)

The FAOSTAT manure N applied to soils (L13, L29) is given per livestock item, not per manure form. Until now the N
of the items that exist in both forms (cattle, buffalo, pigs, laying hens) was split 50/50 for the country defaults
(WFLDB Guidelines v3.0 section 3.6.2, no regional source) and counted in full in both world 'other' mixes (L13).

New: the share of each item's N managed in liquid systems comes from the animal waste management systems (AWMS) of
IPCC 2019 Refinement Vol. 4 Annex 10A.2, Tables 10A.6-10A.9 (file `Literature/19R_V4_Ch10_Livestock.pdf`), in the IPCC
region of the country (`models/manuremodel.py` ManureModel._ipcc_liquid_share):

- Transcription: `ipcc2019_table10a_awms.csv`, all 116 rows (cattle and buffalo, swine, sheep and goats, poultry);
  checked cell by cell against the PyMuPDF table extraction of the PDF (0 differences); every row sums to 100 %.
- Forms (`ipcc2019_awms_forms.csv`, Table 10A.10, IPCC vs EMEP/EEA systems): liquid = lagoon, liquid/slurry, pits
  (laying hens: poultry manure without litter, EMEP 'laying hens - slurry'), digester (digestate as uncovered slurry,
  Table 10.22 note 3); solid = solid storage, poultry manure with litter, dry lot, daily spread (the last two have no
  EMEP equivalent: FC choice); not applied = pasture/range/paddock, burned for fuel. Share = liquid / (liquid + solid).
- Productivity class: IPCC Tier 1 rule (Table 10.14 note 1, Table 10.16A note 1), high productivity rows in North
  America, Europe and Oceania, low productivity rows elsewhere (swine, laying hens; `ipcc2019_regions.csv`).
- FAOSTAT items -> IPCC categories (`ipcc2019_faostat_item_awms_mapping.csv`): buffalo = mean of the dairy and non-dairy
  buffalo rows, non-dairy cattle where the region has none (Table 10.14 note 6); Russian Federation: own rows for
  swine and laying hens, Eastern Europe rows for cattle and buffalo. No managed system in the tables (non-dairy
  cattle and buffalo of Oceania): WFLDB 50/50.
- Regions: UNSD M49 sub-regions with country exceptions (`ipcc2019_m49_region_mapping.csv`, signed by FC) for the 198 FAOSTAT
  areas (`ipcc2019_country_region.csv`), built with the N per region (`faostat_manure_n_applied_ipcc_region.csv`) by
  `scripts/build_faostat_manure_ipcc_region.py` from the FAOSTAT download and the M49 table supplied by FC.
- Sheep, goats (also the proxy of horses, asses and mules, Table 10A.9 note 1) and broilers have no liquid system in
  the tables and stay solid only, as before.

| Region | Dairy cattle | Non-dairy cattle | Buffalo | Pigs (market) | Pigs (breeding) | Laying hens |
|---|---|---|---|---|---|---|
| North America | 0.59 | 0.02 | 0.52 | 0.93 | 0.93 | 0.30 |
| Western Europe | 0.58 | 0.42 | 0.35 | 0.85 | 0.84 | 0.44 |
| Eastern Europe | 0.06 | 0.93 | 0.17 | 0.44 | 0.44 | 0.34 |
| Russian Federation | 0.06 | 0.93 | 0.17 | 0.24 | 0.24 | 1.00 |
| Oceania | 0.83 | 50/50 | 50/50 | 0.91 | 0.91 | 1.00 |
| East Asia and South-East Asia | 0.02 | 0 | 0 | 0.60 | 0.56 | 0 |
| South Asia, Latin America, Near East and North Africa, Sub-Saharan Africa | 0 | 0 | 0 | 0.63 | 0.63 | 0 |

Liquid share of the manure N per item and IPCC region (low productivity outside North America, Europe and Oceania).

| Country | Liquid N share before | after | Default manure per kg N uptake, before | after |
|---|---|---|---|---|
| IN | 0.43 | **0.01** | 0.0522 m3 + 48.0 kg | **0.0009 m3 + 91.7 kg** |
| CN | 0.38 | **0.17** | 0.0412 m3 + 28.8 kg | **0.0214 m3 + 42.3 kg** |
| BR | 0.41 | **0.24** | 0.0499 m3 + 31.4 kg | **0.0293 m3 + 49.8 kg** |
| US | 0.36 | **0.33** | 0.0421 m3 + 30.7 kg | **0.0400 m3 + 35.1 kg** |
| FR | 0.43 | **0.45** | 0.0523 m3 + 40.6 kg | **0.0553 m3 + 40.5 kg** |
| ES | 0.47 | **0.65** | 0.0589 m3 + 36.9 kg | **0.0807 m3 + 29.6 kg** |
| NZ | 0.44 | **0.66** | 0.0552 m3 + 46.2 kg | **0.0821 m3 + 24.0 kg** |

Full table (39 countries and the two 'other' mixes), confirmed by FC: `Literature/review_manure_ipcc_mms.csv`. The available N of the
default manure stays 0.2 x N uptake (L29); only its split between liquid and solid manure and the mix of each form
change. The world 'other' mixes: liquid N 5.41 -> 5.18 kg/m3 (pig share 0.30 -> 0.55), solid N 7.58 -> 7.70 kg/t
(pig share 0.22 -> 0.09).

Data fix: `faostat_manure_n_applied_world.csv` summed the FAOSTAT aggregate 'China' (M49 159) together with its parts
(China, mainland; Taiwan; Hong Kong; Macao); rebuilt by the script without it (pigs, market 6.54 -> 5.13 Tg N,
laying hens 3.48 -> 2.51, buffalo 2.31 -> 1.92).

Open: FAOSTAT applied N is not always consistent with the IPCC regional systems (AU non-dairy cattle, 81 Gg N applied
with 100 % pasture in IPCC: WFLDB 50/50 kept); dry lot and daily spread solid and the M49 exceptions are judgment.

Regression (`scripts/compare_regression.py`): wheat_IT and apple_FR unchanged (manure from the template); rice_IN:

| Key | Before | After |
|---|---|---|
| liquid manure, cattle / laying hens / pig (kg) | 4824 / 105 / 62 | 0 / 0 / 87 |
| solid manure, cattle / laying hens / sheep-goat (kg) | 3676 / 98 / 684 | 7679 / 166 / 714 |
| ammonia_total | 34.10 | 33.33 |
| N2o_air | 1.803 | 1.836 |
| Nox_as_n2o_air | 5.261 | 5.718 |
| nitrate_to_groundwater | 137.9 | 134.3 |
| heavymetal_to_soil_zn / cu | 0.180 / 0.0327 | 0.245 / 0.0472 |

## 31. Default total pesticides from the WFLDB 3.1 Documentation 2017 (decision L43, 2026-10-16)

The default total of pesticide active ingredients (`pest_total`) came from the legacy GD_crop sheet Pesticides_L1. The
WFLDB 3.1 Documentation 2017 (Excel annex, sheets 2a-2c, row 19 "Total amount of active ingredient (a.i.), any kind of
pesticides") gives the same quantity for 104 datasets. Of the 102 crop-country pairs both tables have, 52 agreed within
1 %, 50 differed, 30 of them by a factor of 2 or more. Within a crop the ratio is the same for every country (almond CN
and US x2.29, apple CL, CN and US x1.54, mandarin CN and ES x2.43): the L1 values are MEXALCA extrapolations from an
origin country (Guidelines v3.0 section 3.7, X_t = X_o x sqrt(ind_t / ind_o)), whose country ratios stayed while the
value of the origin country changed. GD_crop was probably built from an earlier WFLDB version.

New (`defaultMatrixTotalPesticides.py`):

- Transcription: `wfldb2017_pesticides_total_ai.csv`, all 104 datasets with their data level (L0-L4), checked by the
  tests against the workbook.
- Mapping: `wfldb2017_pesticides_crop_mapping.csv` (signed by FC). Each tool crop takes the datasets of its crop; tomato, orange and
  coffee take the dataset of their grade or species and, where WFLDB has only one grade or species in a country, that
  one for both (tomato IT, NL, MX; orange ES, ZA, BR; coffee CO, ID, VN). Strawberry CH takes the heated greenhouse, as
  the legacy table. Not used: strawberry CH non-heated greenhouse, vanilla MG.
- GLO = simple mean of the direct datasets of the crop, also of countries outside the tool (palm MY, coffee HN).
- Strawberry MX and MA, which repeated the legacy GLO, take the new GLO. Tomato CH, raspberry, blueberry, cranberry and
  the 24 crops with GLO 0 keep the legacy rows of `default_pesticides.csv` (legacy, undocumented, provisional).
- 18 new rows: maize AR, rapeseed CA, soybean AR, sugar beet DE and RU, onion IN, coconut ID, IN and PH, coffee CO and
  IN, palm ID and MY, sugarcane BR and IN, coffee Arabica HN.

| Crop, country | Legacy (kg a.i./ha) | WFLDB 2017 (kg a.i./ha) | Data level |
|---|---|---|---|
| pear AR | 0.87 | 13.78 | L0 |
| coffee ID / VN | 8.07 / 9.63 | 0.23 / 0.50 | L3 |
| strawberry ES | 217.8 | 26.3 | L3 |
| sugar beet FR / US | 4.08 / 2.55 | 0.67 / 6.53 | L3 / L1 |
| peanut AR / IN | 12.29 / 4.07 | 2.56 / 0.81 | L3 |
| wheat CA | 2.15 | 0.50 | L3 |
| cocoa CI / GH / ID | 2.16 / 2.16 / 16.59 | 9.59 / 7.14 / 7.71 | L3 |
| banana CO / CR | 29.1 / 21.9 | 9.67 / 64.8 | L3 |
| almond CN / US | 4.84 / 4.76 | 11.10 / 10.92 | L1 / L3 |
| sunflower HU / RU | 1.72 / 0.80 | 4.50 / 2.05 | L1 |
| tomato fresh ES / tomato IT | 19.3 / 37.9 | 32.3 / 21.8 | L3 |
| sugarcane GLO / maize GLO | 2.48 / 0.05 | 8.91 / 0.13 | - |

Full table (200 rows, legacy and new value with the source cell), confirmed by FC: `Literature/review_wfldb_pesticides.csv`.

The default only sets the pesticide packaging (`models/packmodel.py`); the pesticide emissions come from the active
ingredients of the template. Regression (`scripts/compare_regression.py`): apple_FR and wheat_IT unchanged (total from
the template); rice_IN 1498.06 -> 1500 g/ha, `wfldb_packaging_liquid` 2.996 -> 3.000 and
`ecoinvent_packaging_liquid` 4.494 -> 4.500 kg/ha.

Open: the values are to be replaced by the Global atlas of pesticide use (Zhang et al., Research Square preprint 2026,
doi 10.21203/rs.3.rs-10665000/v1; 2016-2020, 131 crops, 167 countries, annual load in kg/ha/year; data on Zenodo,
doi 10.5281/zenodo.15282367, files restricted) once its data are accessible, with Eurostat aei_pestuse and USDA NASS
Chemical Use as checks for the EU and the US (FC, 2026-10-16). The 24 crops with GLO 0 (e.g. grape, cotton, mango,
pineapple) have no default pesticides; blueberry and cranberry (97.4 kg/ha) and raspberry (33.9 kg/ha) stay legacy. Done by decision L48 (section 36).

## 32. Default irrigation water from Pfister & Bayer (2014) and AQUASTAT irrigation techniques (decision L44, 2026-10-19)

The default irrigation water (`water_use_total`, used when the template gives no water) is the withdrawal

    withdrawal [m3/ha and crop cycle] = ETirr [m3/t] x yield [kg/ha and crop cycle] / 1000 / EFirr

(WFLDB Guidelines v3.0 section 3.5.2). The irrigation model puts ETirr x yield / 1000 to air and splits the rest
between river and groundwater. Units: ETirr is m3 of irrigation water consumed per t of harvested crop (FAOSTAT item
of the year 2000); the yield is per crop cycle (L24); tea is made tea in both (Pfister production 2000: 2.86 Mt,
1/4.4 of the green leaf of the current FAOSTAT item), so no conversion.

ETirr (`defaultMatrixEvapoTranspiration.py`):

- Source: Pfister & Bayer (2014), Appendix B, sheet 'Blue water consumption (m3_ton)': expected value = geometric
  mean of deficit irrigation (CROPWAT x reported irrigated proportion) and full irrigation, production-weighted per
  country (`pfister2014_blue_water_country.csv`). GLO = world value of the sheet 'Global Averages'. A country with
  'No production' takes GLO.
- The legacy matrix GD_crop ETirr_m3t_L1 is this table for 859 of its 955 country values. Sweet corn took the maize
  grain values; mandarin, 19 values of India and 4 others differed; 32 pairs have no production in Pfister.
- Range: minimum (deficit) and maximum (full irrigation), production-weighted from the watershed file of the same
  study, in the same table. Partitions per watershed (WaterGAP basin) and month in
  `pfister2014_blue_water_watershed.csv`. Neither is used by the model yet.
- Flax, hemp, mint and mulberry keep the legacy values (Pfister has fibre or no crop).

EFirr: technique shares x 0.45 surface, 0.75 sprinkler, 0.90 localized (Guidelines v3.0 Tab. 3,
`model_parameters.csv`). The shares per country are the AQUASTAT 2020 area equipped for full control irrigation per
technique (`aquastat_irrigation_technique_area.csv`, `irrigation_technique_source.csv`) instead of the legacy ICID 2012
or level 0 shares; NL keeps the legacy shares.

| Crop, country | ETirr legacy -> new (m3/t) | Pfister min-max (m3/t) | EFirr legacy -> new | Withdrawal legacy -> new (m3/t) |
|---|---|---|---|---|
| wheat FR | 111.2 -> 111.2 | 36.1-454.5 | 0.61 -> 0.75 | 183 -> 148 |
| wheat AR | 361.7 -> 361.7 | 22.0-1541.2 | 0.46 -> 0.59 | 780 -> 608 |
| rice IN | 446.6 -> 446.6 | 262.8-806.2 | 0.48 -> 0.46 | 932 -> 969 |
| maize US | 170.1 -> 170.1 | 41.1-413.7 | 0.63 -> 0.62 | 270 -> 272 |
| cotton IN | 1526.5 -> 2990.9 | 1518.4-6318.9 | 0.48 -> 0.46 | 3187 -> 6490 |
| potato US | 85.4 -> 85.4 | 55.1-127.1 | 0.63 -> 0.62 | 136 -> 137 |
| almond US | 3221.3 -> 3221.3 | 2843.4-3676.5 | 0.63 -> 0.62 | 5114 -> 5156 |
| sweet corn FR | 127.2 -> 53.2 | 18.9-191.8 | 0.61 -> 0.75 | 209 -> 71 |
| mandarin CN | 195.1 -> 151.2 | 62.9-356.7 | 0.48 -> 0.47 | 409 -> 322 |
| cranberry US | 13.0 -> 22.8 (GLO) | - | 0.63 -> 0.62 | 21 -> 36 |

Cross-check with Mialyk et al. (2024, national blue water footprint from irrigation 2010-2019,
`mialyk2024_*.csv`, `scripts/compare_mialyk_pfister.py`): of 1151 crop-country pairs, 383 inside the Pfister range
(24 % of the production), 731 below the minimum (74 %), 37 above the maximum (2 %, mostly rice ID, VN, PH). The gap
stays with the Mialyk values of 1999-2001 including capillary rise (58 % below), so it is a model difference; Mialyk
also has zero for crops whose irrigated area its input does not resolve (potato US, olive IT, citrus CN).

Regression (`scripts/compare_regression.py`): no change (the three cases give water and irrigation techniques).

Open: uncertainty and regionalised water flows in the ecoSpold writer (range and partitions are ready); input data of
the year 2000; legacy electricity / diesel split, NL techniques, river / groundwater split 20/80 and EI_IRR ratios.

## 33. Mineral fertiliser mixes from IFASTAT (decision L45, 2026-10-19)

The default mixes of mineral fertiliser types per country (`n_fertiliser_proportions`, `p_fertiliser_proportions`,
`k_fertiliser_proportions`, used when the template gives no mix) are the shares of the N, P2O5 and K2O consumed in
2021-2023 according to IFA, IFASTAT, indicator 'Fertilizer consumption' by product and nutrient (export of 2026-10-19
downloaded by FC). The IFASTAT values are IFA member data: the repository holds only the derived shares
(`ifastat_fertiliser_mix.csv`), `scripts/build_ifastat_fertiliser_mix.py` rebuilds them from the export in
`data/external_data/`.

Products -> tool types (`ifastat_product_type_mapping.csv`, signed by FC):

| IFASTAT product | N | P2O5 | K2O |
|---|---|---|---|
| ammonia, AN, AS, CAN, urea, UAN, MAP, DAP, KNO3, TSP, SSP, KCl, K2SO4 | same type | same type | same type |
| phosphate rock | - | raw phosphate | - |
| NK | potassium nitrate | - | potassium nitrate |
| NP | ammonium nitrate phosphate | ammonium nitrate phosphate | - |
| NPK | 1/3 each MAP, DAP, ammonium nitrate phosphate (FC, option B) | 1/3 each MAP, DAP, ammonium nitrate phosphate | left out (FC, option B) |
| PK | - | 1/3 each MAP, DAP, ammonium nitrate phosphate | left out (FC, option B) |
| Other | left out | 1/2 raw phosphate, 1/2 basic slag | patent potassium |

Left out = the shares of the other products are scaled to 1; FI, whose K2O is only in NPK, takes the world mix of the
export. All other rules are those of the legacy mixes.

The legacy mixes (GD_crop; WFLDB 3.1 Documentation 2017 Appendix 2, IFA 2009-2012) are reproduced from IFASTAT
2009-2012 with these rules plus five more: IFA urea split 50/50 between urea and urea AN, urea AN (N solutions) as liquid
ammonia, MAP + DAP split 50/50, NPK N as 1/2 potassium nitrate + 1/6 each MAP, DAP, ammonium nitrate phosphate, and NPK
and PK K2O as potassium nitrate (FI, mean 2009-2012: CAN 46.0, NPK 99.25, urea 0.75 kt N give CAN 0.31507, MAP = DAP =
ammonium nitrate phosphate 0.11330, potassium nitrate 0.33990, urea = urea AN 0.0025685, the legacy values). The new
mixes drop these rules:

- Urea and urea AN, MAP and DAP are separate products in IFASTAT.
- NPK N with the legacy rule had the NH3 factors 54 and 120 g NH3/kg N (pH <= 7 and > 7) instead of 84 and 187 of
  EMEP/EEA 2023 Table 3-2 'NPK mixtures'; 1/3 each MAP, DAP, ammonium nitrate phosphate gives exactly 84 and 187.
- NPK and PK K2O as potassium nitrate made potassium nitrate the main K2O type in many countries (CN 80 %, GH 64 % with
  the 2021-2023 data), while potassium nitrate is 0-17 % of the K2O as a product.

| Country | urea | urea AN | liquid ammonia | NH3 factor pH <= 7 (g NH3/kg N) | KCl (% K2O) | potassium nitrate (% K2O) |
|---|---|---|---|---|---|---|
| FR | 8 -> 27 | 8 -> 29 | 29 -> 0 | 46 -> 93 | 42 -> 74 | 51 -> 1 |
| DE | 14 -> 21 | 14 -> 14 | 15 -> 0 | 62 -> 78 | 63 -> 90 | 29 -> 0 |
| US | 12 -> 26 | 12 -> 29 | 56 -> 25 | 57 -> 96 | 71 -> 91 | 24 -> 4 |
| IN | 40 -> 81 | 40 -> 0 | 0 -> 0 | 128 -> 174 | 70 -> 100 | 29 -> 0 |
| CN | 38 -> 40 | 38 -> 0 | 5 -> 0 | 120 -> 128 | 72 -> 60 | 22 -> 6 |
| BR | 26 -> 56 | 26 -> 0 | 0 -> 0 | 101 -> 141 | 97 -> 99 | 2 -> 0 |
| TH | 36 -> 77 | 36 -> 0 | 0 -> 0 | 122 -> 170 | 0 -> 98 | 100 -> 1 |
| FI | 0 -> 0 | 0 -> 0 | 0 -> 0 | 45 -> 60 | 0 -> 90 | 100 -> 3 |

(% of kg N unless stated.) P2O5: MAP and DAP are no longer equal (IN 37/37 -> 5/63, AR 38/38 -> 64/20); other P2O5 goes
half to raw phosphate and half to basic slag (CA 12 + 12 %, BE 10 + 10 %); raw phosphate LK 20 -> 71 %. MA and CS get
mixes with a source.

Not adopted: Menegat et al. (2022) Sci Rep 12:14490, supplementary table 2 (IFASTAT N shares of 2018, CC BY 4.0; consistent
with IFASTAT, N only); FAOSTAT Fertilizers by Product (t of product): no data 2021-2023 for 13 of the 39 countries, the
straight products explain 0.9-1.1 of the FAOSTAT nutrient total in only 5-8 countries per nutrient, no nutrient contents
for compounds.

Regression (`scripts/compare_regression.py`): no change (the three cases give the N, P and K mixes).

Open: a real NPK (NP, NK, PK) type in the tool (Master Data "NPK (15-15-15) fertiliser", EMEP "NPK mixtures"; input
template, product, NH3 and heavy-metal mappings; P and K contents of the Master Data product); the shares need a new
IFASTAT export to be updated.

## 34. Default seed of the sown crops from FAOSTAT SUA and the FAO Technical Conversion Factors (decision L46, 2026-10-19)

The default seed (`seeds`, `seed_quantities`, kg per ha and crop cycle, used when the template gives no seed) of the 16
crops with use `sua_tcf` in `seed_rate_crop_mapping.csv` (signed by FC 2026-10-20) comes from `default_seed.csv`, built
by `scripts/build_default_seed.py` from two FAO sources:

- FAOSTAT Supply Utilization Accounts, element 5525 Seed (t), bulk download supplied by FC, divided by the FAOSTAT QCL
  area harvested of the next year (the seed of year t is the seeding rate x the area sown in year t + 1, FAOSTAT New
  Food Balances, section V Seed); mean of the seed years 2021-2023; GLO = FAOSTAT World;
- FAO Technical Conversion Factors for Agricultural Commodities, column 'Seeding rates' (kg/ha, national averages
  1992-1996), extracted from the PDF for the 39 countries (`fao_tcf_seed_rates.csv`, 354 rates, confirmed by FC).

Rule (FC, option 1): a country takes its SUA rate when it lies within a factor 2 (`seed_rate_max_ratio`) of its TCF
rate, otherwise the TCF rate; without a TCF rate, the SUA rate when within a factor 2 of GLO, otherwise GLO. The
column `source` of `default_seed.csv` gives the origin of each value.

| Crop | Legacy GLO | New GLO (SUA World) | Countries SUA / TCF / GLO |
|---|---|---|---|
| wheat | none (0) | 156.4 | 29 / 3 / 7 |
| maize grain | 25 | 37.8 | 28 / 10 / 1 |
| oat | 190 | 264.7 | 22 / 6 / 11 |
| rice | 141 | 111.1 | 22 / 7 / 10 |
| potato | 2500 | 1706.5 | 32 / 5 / 2 |
| soybean | 110 | 62.6 | 21 / 3 / 15 |
| sunflower | 3.75 | 28.9 | 15 / 8 / 16 |
| rapeseed | 5.6 | 14.7 | 9 / 9 / 21 |
| linseed | 40 | 52.0 | 11 / 9 / 19 |
| lentil | 0 | 48.4 | 12 / 7 / 20 |
| chick pea | 0 | 41.0 | 9 / 3 / 27 |
| peanut | 100 | 81.5 | 17 / 8 / 14 |
| pearl millet | 100 | 19.2 | 6 / 10 / 23 |
| castor beans | 0 | 9.0 | 5 / 6 / 28 |
| cotton (seed 329 / area 328) | 0 | 35.5 | 20 / 3 / 16 |
| sesame | 100 | 15.4 | 9 / 4 / 26 |

(kg/ha.) The legacy values (GD_crop Seeds_L0) were one GLO value per crop without source, the same for all countries.

| Crop, country | SUA | TCF | Default (source) |
|---|---|---|---|
| wheat FR | 149.3 | 162 | 149.3 (SUA) |
| wheat IN | 95.9 | 185 | 95.9 (SUA) |
| wheat IT | 314.0 | 284 | 314.0 (SUA) |
| rice IN | 69.4 | 163 | 163 (TCF) |
| rice CN | 226.1 | 140 | 226.1 (SUA) |
| maize grain NL | 908.3 | 25 | 25 (TCF; seed of silage maize) |
| sunflower DE | 805.0 | 11 | 11 (TCF) |
| potato PH | 25.3 | 2250 | 2250 (TCF) |
| soybean ZA | 9.7 | 75 | 75 (TCF) |
| chick pea CO | 3576 | - | 41.0 (GLO) |
| castor beans MX | 2248 | - | 9.0 (GLO) |

Of the 1110 SUA seed values of the 39 countries in 2021-2023, 841 (76 %) are FAO estimates or imputations; 243 of the
328 SUA-TCF pairs of the same country agree within a factor 2. The SUA rate divides by the area harvested (QCL has no
sown area) and includes the seed of crops harvested green or for fodder.

Flagged for review (FC: rule kept as is):

- the TCF rates of UA oat (450, SUA 144.6), UA sunflower (65, SUA 11.2) and PL rapeseed (100, SUA 7.7) win over plausible
  SUA rates; the three values are printed so in the PDF;
- CH sunflower and rapeseed (SUA 4.5 and 5.0, no TCF rate) take the GLO 28.9 and 14.7;
- the TCF linseed rate of BE (150) is probably fibre flax.

The 9 sown crops without usable data keep the legacy GLO values (`_LEGACY_SEEDS` in `defaultMatrixSeed.py`, legacy,
undocumented, provisional): carrot 4.2, sugar beet 2.1, sweet corn 25, turmeric 100, cassava, coriander, flax, guar and
hemp 0; the reason per crop is in the note column of the mapping.

Effect: wheat gets a default seed for the first time (seed exchange and heavy metals of the seed); castor beans, chick
pea, cotton and lentil from 0 to 9-48 kg/ha.

Regression (`scripts/compare_regression.py`): no change (the three cases give the seed).

Open: the factor 2 and the flagged cases above; the 9 legacy crops; seedlings and trees (part B, ecoinvent 3.12: done in
section 35, which also corrects the statement first written here that the legacy onion (3.30) and tomato (3.125) values
are seedlings per kg of product).

## 35. Default seedlings and trees from ecoinvent 3.12 (decision L47, 2026-10-20)

The default number of seedlings (`nb_seedlings`) and trees (`nb_planted_trees`) per ha, used when the template gives no
planting, comes from the ecoinvent 3.12 cut-off datasets of the crops. `scripts/build_ecoinvent_planting_rates.py`
reads the release file 'exchanges (3.12, cut-off).xlsx' (copied to `data/external_data/`) and stores only values per ha
(`ecoinvent312_planting_rates.csv`, 133 datasets):

- per ha and year = inputs '..., for planting' (unit per kg) x 10000 / occupation (m2a per kg);
- per ha and crop cycle = the same / transformation from (m2 per kg; the land is transformed once per planting);
- lifetime = occupation / transformation.

Crops -> activities, excluded geographies, quantity and proxies are in `ecoinvent312_planting_crop_mapping.csv` (signed
by FC; review table `Literature/review_planting_defaults.csv` confirmed by FC):

| Crops | Quantity | Default in the tool |
|---|---|---|
| trees, asparagus (planting amortised over the lifetime, `crop_types.csv`) | per ha and year | x orchard lifetime in use (default 20 years): the yearly planting of the tool (number / lifetime) equals ecoinvent |
| onion, tomato, strawberry, cabbages, bell pepper | per ha and crop cycle | as is |
| mint (perennial in ecoinvent, 20 years; annual in the tool) | per ha and year | as is (one crop cycle per year) |

Country value = mean of the datasets of the country and its regions (BR-SP, BR-MG -> BR; IN-HP, IN-MH -> IN; Swiss
regional and organic variants; the production systems of strawberry and fresh tomato). GLO = mean of the RoW datasets,
or the mean of the country values when there is no RoW dataset with a planting input (grape: IN and CH; palm: ID;
white cabbage: CH). Not used, because they have no planting input: grape RoW, palm CO, MY, RoW, fresh tomato open field
IN-MH, IN-UP, bell pepper IN-UP. Excluded by FC: onion IN (the legacy default, see below), IN takes GLO. Proxies:
lime -> lemon, green asparagus -> white asparagus, red cabbage -> white cabbage. No ecoinvent dataset with a planting
input, legacy values kept (0): blueberry, cranberry, pineapple, sugarcane, chilli, eggplant, ginger, raspberry.

| Crop | Legacy | New GLO | Countries (new) |
|---|---|---|---|
| apple | 0 | 2581 | CH 2667, CL 1385, CN 2659, IT 2659, US 1385, ZA 1281 |
| pear | 0 | 1193 | AR 1187, BE 2239, CH 2667, CN 1187, ZA 1298 |
| peach | 0 | 1575 | CN, ES, IT 1575 |
| apricot | 0 | 350 | ES 156, FR 499, IT 472, TR 299 |
| almond | 0 | 242 | CN 171, US 244 |
| lemon, lime | 0 | 172 | ES 171, MX 171, TR 183 |
| mandarin | 0 | 171 | CN, ES 171, ZA 32,088 |
| orange fresh / processing | 0 | 262 / 246 | ES 332, US 219, ZA 288 / BR 216, US 319 |
| olive | 0 | 125 | ES, IT 125 |
| grape | 0 | 4490 | CH 5600, IN 3380 |
| coffee arabica | 0 | 5772 | BR 4464, CO 4667, IN 2952 |
| coffee robusta | 0 | 908 | BR 2513, ID 459, IN 1097, VN 997 |
| cocoa | 0 | 140 | CI, GH, ID 140 |
| coconut | 0 | 666 | ID 739, IN 175, PH 739 |
| tea | 0 | 131 | CN, KE, LK 131, IN 7500 |
| banana | 0 | 131 | CO, CR, EC, IN 131 |
| cashew, mango, palm | 0 | 128, 251, 113 | IN 128; BR 251; ID 113 |
| mulberry, pomegranate | 0 | 13,838, 875 | IN |
| asparagus (white, green) | 0 | 71,236 | CN, FR, PE 71,236 |
| onion | 3.30 | 608,619 | CH 1,027,480, CN 443,560, NL and NZ 1,130,000 (IN: GLO) |
| tomato fresh | 3.125 | 24,606 | ES 28,000, MX 23,000, NL 28,000 |
| tomato processing | 3.125 | 32,786 | IT 34,000 |
| strawberry (fresh, processing) | 0 | 48,434 | CH 43,000, ES 70,000, US 56,511 |
| mint | 0 | 36,162 | IN 36,900, US 27,703 (per year) |
| white and red cabbage | 0 | 7113 | CH 7113 |
| bell pepper | 0 | 326 | IN 25,000 |

(Trees and asparagus: number planted per ha at the default lifetime of 20 years; seedlings: per ha and crop cycle.
Legacy 0 = empty table, default 0.)

The legacy onion (3.30) and tomato (3.125) values have no source. As values per ha they are 4 to 5 orders of magnitude
below the ecoinvent datasets. The ecoinvent onion IN dataset has exactly 3.30189 seedlings per ha, and its land use is
'calculated by using the ecoinvent LCI calculation tool for crop production': it was produced with this tool and the
legacy default; FC excluded it (IN takes GLO). Section 34 called these values seedlings per kg of product; that is not
established.

Effect: the default planting of the tree crops changes from 0 to the values above, with the yearly planting input,
the rooting up of the trees (1 / lifetime) and, from 500 trees per ha (legacy rule of `outputMapping.py`), the trellis
system: apple, pear, peach, coffee (not robusta ID), grape, mulberry, pomegranate, coconut ID, PH and GLO, tea IN,
mandarin ZA. The ecoinvent datasets of these crops have the trellis input, and so do apricot FR and RoW (499 and 350
trees here), coconut IN, coffee robusta ID and orange fresh (tiny amounts).

Regression (`scripts/compare_regression.py`): no change (the three cases give the plantings).

Flagged for review (FC: kept, not excluded): tea CN, KE, LK, RoW 131 trees per ha against IN-HP 7500; banana 131 plants
per ha; cocoa 7 trees per ha and year (350 per ha in 50 years); mandarin ZA 32,088; bell pepper RoW 326. Densities
from the land use differ from some dataset comments: white cabbage CH 5830 and 8395 against 25,000 and 30,000 seedlings
per ha, tomato NL 28,000 against 25,000, broccoli CH 27,500 against 50,000.

Open: the orchard lifetime of 20 years (legacy); bell pepper, chilli, eggplant, cabbages, ginger and sugarcane have no
seedling exchange in the tool (no_exchange), so their values have no effect yet; the ecoinvent findings (onion IN,
tea, datasets without a planting input) to be reported to the ecoinvent data team.

## 36. Default total pesticides from the Global atlas of pesticide use (decision L48, 2026-10-21)

The default total pesticides (`pest_total`, g a.i. per ha and crop cycle, used when the template gives no total) come
from the Global atlas of pesticide use (Zhang, Gladbach, Kosnik, Settles, Norinder, Glas, Fantke 2026, Research Square
preprint v1, doi 10.21203/rs.3.rs-10665000/v1, CC BY 4.0; reference years 2016-2020). The Zenodo data record is still
restricted; the two public supplementary files (supplied by FC) give, in Table S1, the annual applied mass per country,
crop and active ingredient. `scripts/build_atlas_pesticides.py` writes `atlas2026_pesticides_country.csv`:

- tool crop -> atlas crop by the FAOSTAT item code of `faostat_crop_item_mapping.csv` and Table S6 (57 of 67 crops);
  tool country -> atlas country by ISO alpha-3 (Table S4) and M49 (39 of 39 countries, all with reported data);
- applied mass = all active ingredients, target classes and treatments, soil fumigants included (FC);
- value = applied mass / FAOSTAT area harvested, mean 2016-2020: per ha and crop cycle, as the yield (L24). The atlas
  annual load (per ha of mapSPAM 2020 physical area) is not in the public files; FC chose the FAOSTAT area;
- GLO = applied mass of all countries and regions of the atlas / FAOSTAT World area.

Flags (`pesticide_outlier_factor` 10, `pesticide_min_active_ingredients` 5 in `model_parameters.csv`): no FAOSTAT area,
at most 5 a.i., or outside x10 / ÷10 of the median of the tool-country values of the crop. The 74 flagged values are
decided in `atlas2026_pesticides_review.csv` (signed by FC):

| Flag | Values | Use |
|---|---|---|
| above the range, soil fumigants > 50 % of the mass | 9: strawberry ES, US, IL, MA; raspberry ES; carrot IT, US; onion IL; groundnut IL | atlas value kept (real use) |
| above the range, forage types in the atlas crop | 4: maize NL, NZ (silage maize); cabbage AU, NZ (forage brassicas) | fallback |
| above the range, no evident cause | 5: almond IL, oats ZA, onion TH, tomato AU, EC | fallback |
| below 1/10 of the median | 25, e.g. onion VN, banana PE, cocoa PE, potato RU, UA | fallback |
| at most 5 a.i. | 17, e.g. onion CN (4), rice, cotton, tea KE (1) | fallback |
| no FAOSTAT area | 14, e.g. onion NZ, olive CN, apple ID | fallback |

Fallback, and countries without an atlas value: the WFLDB 2017 value of the country (L43; e.g. onion CN 10.6, potato
RU 0.87, pear AR 13.8, strawberry CH 45.8 kg/ha), else the GLO of the atlas. The soil fumigants (12 CAS RN,
`soil_fumigant_active_ingredients.csv`) are stored as an information column; the atlas class 'Others' is mostly sulfur,
copper and mineral oils, not fumigants.

| Crop | Old GLO (kg a.i./ha) | New GLO | Countries (old -> new) |
|---|---|---|---|
| wheat | 1.37 | 0.97 | FR 1.37 -> 2.19, IT 1.37 -> 0.76 |
| maize grain | 0.13 | 1.81 | US 0.13 -> 3.68 |
| rice | 2.53 | 1.25 | IN 1.50 -> 0.65 |
| soybean | 0.92 | 3.38 | BR 0.92 -> 5.63 |
| potato | 1.64 | 6.06 | US 1.64 -> 90.4 (soil fumigants 82 %) |
| apple | 14.5 | 15.6 | FR 14.5 -> 33.2 |
| grape | 0 | 22.6 | IT 0 -> 38.3 |
| tomato fresh | 39.2 | 10.6 | ES 32.3 -> 66.2 |
| strawberry | 38.0 | 19.2 | ES 26.3 -> 229 (soil fumigants 84 %) |
| banana | 23.5 | 5.87 | CR 64.8 -> 71.3 |
| coffee arabica | 4.49 | 1.70 | BR 7.82 -> 5.04 |
| cocoa | 8.15 | 1.04 | CI 9.59 -> 1.61 |
| cotton | 0 | 3.83 | US 0 -> 7.37 |
| mango, pineapple | 0, 0 | 3.45, 4.70 | |
| cabbage, bell pepper | 0, 0 | 12.7, 8.59 | |
| blueberry, raspberry | 97.4, 33.9 (legacy) | 1.56, 8.17 | |

Over the 547 tool-crop and country values with an old value above 0, the median ratio new/old is 1.0 (226 within x2, 171
below half, 150 above double); 184 values change from 0. Full table: `Literature/atlas_6b_step1/review_atlas_values.csv`
(770 values, confirmed by FC). `default_pesticides.csv` keeps 9 legacy rows (castor beans, flax, guar, hemp, mulberry,
pomegranate GLO 0; cranberry 97.4 kg/ha); coconut, mint and sweet corn keep WFLDB 2017 (no atlas crop).

The default only sets the pesticide packaging (`models/packmodel.py`). Regression (`scripts/compare_regression.py`):
apple_FR and wheat_IT unchanged (total from the template); rice_IN 1500 -> 645 g/ha, `wfldb_packaging_liquid`
3.000 -> 1.290 and `ecoinvent_packaging_liquid` 4.500 -> 1.935 kg/ha.

Open: the preprint is under review (check the published version and the Zenodo data); the atlas maize and cabbage
include forage types; flax, mint, mulberry and pomegranate are only in aggregated atlas crops.

## 37. Data never used by the model (decision L49, 2026-10-26)

Analysis of 2026-10-21: every module-level table of `defaultTables.py` and of the `defaultMatrix*.py` modules wrapped in
an access tracker, then every default of `DEFAULTS_VALUES_GENERATORS` computed for the 67 crops and 39 countries
(scripts in the git-ignored `Literature/unused_data_check/`).

Removed (no code change, results unchanged): the five P parameters of `model_parameters.csv` (`p_gw_arable` 0.07,
`p_gw_grassland` 0.06, `p_ro_arable` 0.175, `p_ro_grassland_intensive` 0.25, `p_ro_grassland_extensive` 0.15 kg P/ha
and year), duplicates of `p_landuse_classes.csv`, the only table read by `models/pmodel.py`.

Files of `data/` read only outside the model: `elementary_flow_alignment.csv`, `intermediate_exchange_alignment.csv`
and `fertiliser_product_basis.csv` (checks and tests, for the ecoSpold writer); `pfister2014_blue_water_watershed.csv`
and the `mialyk2024_*.csv` tables (cross-check, L44); `faostat_manure_n_applied_world.csv` (built and tested, not read
since L42); the inputs of the build scripts (`fao_tcf_seed_rates.csv`, `ifastat_country_mapping.csv`,
`ifastat_product_type_mapping.csv`, `ipcc2019_m49_region_mapping.csv`, `pfister2014_country_mapping.csv`,
`soil_fumigant_active_ingredients.csv`). `ecoinvent_flows_md312.csv`, read by nothing, removed (FC does not need it; the flooded-crop land flow UUIDs are in
`docs/java_changes_pending.md`).

Open, because they need code changes:

| Item | Entries | Read by the model |
|---|---|---|
| soil constants in `model_parameters.csv` (`soil_volume_m3` 5000, `bulk_density_kg_m3` 1300, `soil_cn_ratio` 11, `norg_ntot_ratio` 0.85) | 4 | 0 (same values hardcoded in `defaultGeneration.py`) |
| `defaultMatrixNUptake.py` | 215 | 3 (mulberry CN, IN, GLO = 400) |
| `defaultMatrixTotalManure.py`, liquid and solid | 191 each | 25 each (all GLO = 0) |
| `defaultMatrixTotalMineralFert.py` | 191 | 25 (all GLO = 0) |
| `_LEGACY_EVAPO` (`defaultTables.py`) | 1024 | 9 (flax, hemp, mint, mulberry) |
| WFLDB 2017 total pesticides (L43) | 158 | 28 reach the final table |

Unused code: `NotFoundGenerator`, `ConvertRatioToValueDefaultGenerator` and `OneRatioToValueConvertor` in
`defaultGeneration.py`; the package `src/agritool/` (only `tests/test_agritool.py`).

Files of `data/external_data/` not read by any script: `Inputs_FertilizersProduct_E_All_Data_(Normalized).zip` and
`SMMenegat2022.xlsx` (rejected in L45), `spam2020V0r1_global_physical_area.zip` (rejected in L48),
`national_wf_175_crops_annual_1990_2019.csv` (L44 uses the 2010-2019 average), `ER_updated_scope_irrigation_activities_and_geos.xlsx`
(consulted by hand in L44), the FAOSTAT QCL metadata files (`Production_Crops_Livestock_E_AreaCodes.csv`, `_Elements`,
`_Flags`, `_ItemCodes`), `WSMix Implementation in betav2.xlsx` (regional water supply mixes: water withdrawal and tap water
treatment technologies adapted to local conditions, tap water transport losses and average transport distance per
country) and `Mialyk_WaterFootprints.pdf` (description of the Mialyk et al. 2024 water footprint data).


## 38. Default orchard lifetime from ecoinvent 3.12 (decision L50, 2026-10-26)

Before: `orchard_lifetime` = 20 years for every crop, 3 for sugarcane (legacy, undocumented, provisional). It divides
the plantings of the amortised crops (seedlings and trees per year, rooting up of the trees), the perennial land
transformation (10000 m2 / lifetime) and the greenhouse.

Now: per crop and country from the ecoinvent 3.12 undefined release (`ecoinvent312_orchard_lifetime.csv`, lifetime =
occupation / transformation of each dataset; `orchard_lifetime_crop_mapping.csv`), or set by FC.

| Crop | Before | Now |
|---|---|---|
| almond, apricot, banana, coffee arabica and robusta, lemon, lime, mango, olive, orange processing, palm, peach, tea | 20 | 20 (WFLDB datasets; mango, palm MY/CO from their formulas) |
| apple, pear | 20 | 20; CH 15 |
| grape | 20 | GLO 25 (FC), CH 25, IN 20 |
| mandarin | 20 | 20; ZA 25 |
| orange fresh | 20 | 20; ZA 33 |
| cocoa | 20 | 50 |
| coconut | 20 | 60 |
| asparagus green and white | 20 | 9 |
| cashew | 20 | 25 (FC) |
| blueberry / cranberry / raspberry / pineapple | 20 | 25 / 20 / 8 / 2 (FC) |
| sugarcane | 3 | 5 (FC; ecoinvent GLO comment, Macedo et al. 2004) |
| mulberry, pomegranate | 20 | 20 (ecoinvent datasets made with this tool; legacy) |
| all other crops | 20 | 20 (`orchard_lifetime_other_crops`, legacy; greenhouse only) |

Default plantings per ha planted (L47 rate per ha and year x lifetime), before -> now: cocoa 140 -> 349, coconut GLO
666 -> 1997 (ID, PH 739 -> 2216; IN 175 -> 524), grape GLO 4490 -> 5612, CH 5600 -> 6999, apple and pear CH 2667 -> 2000,
mandarin ZA 32,088 -> 40,110, orange fresh ZA 288 -> 476, cashew 128 -> 159, asparagus 71,236 -> 32,056 seedlings. The
yearly planting is unchanged; it now matches the ecoinvent transformation per planting (cocoa CI 349 against 350).

Regression cases: no change (apple_FR gives 25 years in the template; rice_IN and wheat_IT are annual).

## 39. Greenhouse and plastic tunnel per m2 and year (decision L51, 2026-10-26)

Template fields `greenhouse_glass_roof`, `greenhouse_plastic_roof`, `greenhouse_plastic_tunnel`: m2 of infrastructure
measured on the soil, per ha. The ecoinvent 3.12 products 'greenhouse, glass walls and roof', 'greenhouse, plastic walls
and roof' (m2*year) and 'plastic tunnel' (m2) stand for 1 m2 used over 1 year; the construction is amortised inside.

| Field | Before (per ha and crop cycle) | Now |
|---|---|---|
| `greenhouse_glass_roof`, `greenhouse_plastic_roof` | m2 / orchard lifetime | m2 / crop cycles per year |
| `greenhouse_plastic_tunnel` | m2 / 25 / orchard lifetime | m2 / crop cycles per year |

Example, 1 ha fully covered, 1 crop cycle per year, former default lifetime 20 years: glass or plastic greenhouse 500 ->
10,000 m2*year (x 20); plastic tunnel 20 -> 10,000 m2 (x 500). The new amount equals the land occupation, as in the
ecoinvent tomato and strawberry greenhouse and tunnel datasets.

`orchard_lifetime_other_crops` (20 years, legacy) removed from `model_parameters.csv`: the orchard lifetime is read only
for the crops of `orchard_lifetime_crop_mapping.csv` (L50).

Regression cases: no change (no greenhouse in apple_FR, rice_IN, wheat_IT).

Reference for the check: the ecoinvent 3.12 greenhouse and tunnel crop datasets, where the greenhouse or tunnel amount
equals the land occupation (tomato, fresh grade, in heated greenhouse NL and GLO and in unheated greenhouse ES and GLO;
strawberry in heated and unheated greenhouse CH and GLO; strawberry, open field, macro tunnel ES, US and GLO).

Known limits:

- Unit of the tunnel. The ecoinvent product 'plastic tunnel' is declared in m2 but means m2*year (1 m2 used over 1
  year). The model needs no conversion, but a reader who sees only "m2" could reintroduce a division by a lifetime;
  the code comment in `outputMapping.py` says so.
- Years of use. The ecoinvent datasets use the actual years of use of the crop cycle; 1 / `crop_cycle_per_year` is an
  approximation that is exact when the cycles of the year have the same length, the usual case of the templates. A
  cycle duration would be needed only for greenhouse rotations with very different cycles. The land occupation uses
  the same rule, so greenhouse and occupation stay aligned.
- Fixed lifetimes. The annualised ecoinvent datasets contain a lifetime of the structure and of the film that the model
  cannot change. For now this keeps the tool equal to ecoinvent. Distinguishing e.g. a single-use film from a
  three-year film, or assigning the film only to the covered cycle of a mixed rotation, would need the film as a
  separate material input. Not planned.

## 40. Soil constants from `model_parameters.csv`, unused code removed (decision L52, 2026-10-26)

Code part of the clean-up of section 37. The defaults of four inputs of the SQCB nitrate model are now read from
`model_parameters.csv` instead of being written in `defaultGeneration.py`:

| Input | Parameter | Value |
|---|---|---|
| `considered_soil_volume` | `soil_volume_m3` | 5000 m3/ha |
| `bulk_density_of_soil` | `bulk_density_kg_m3` | 1300 kg/m3 |
| `c_per_n_ratio` | `soil_cn_ratio` | 11 |
| `norg_per_ntotal_ratio` | `norg_ntot_ratio` | 0.85 |

A value given in the template is still used. Removed: `NotFoundGenerator`, `ConvertRatioToValueDefaultGenerator` and
`OneRatioToValueConvertor`, never called. The package `src/agritool/` is kept as a reference (FC).

Regression cases: no change.

## 41. IFASTAT time factor of the IFA rates, upper bound of the region rates (decision L53, 2026-10-26)

Side item of L37 (section 26): the region rate of a crop missing in a country gave high values where the crop is
marginal (wheat TH 202 / 234 / 127 kg N / P2O5 / K2O per ha). The cause was mostly the time factor, the FAOSTAT RFN use
per area of cropland 2021-2023 / FUBC year, whose series have breaks:

| Country, nutrient | FAOSTAT RFN | IFASTAT | Remark |
|---|---|---|---|
| TH P2O5 | 1.87 | 0.75 | FAOSTAT 13 kg/ha in 2021, 31 and 36 in 2022-2023, 15.5 in 2024 |
| TH K2O | 1.73 | 0.86 | same peak |
| PH P2O5 | 2.57 | 1.16 | 2023 almost twice 2022, 2024 = 2023 |
| CS P2O5 | 1.74 | 1.08 | |
| ID P2O5 | 0.44 | 0.90 | |
| IT P2O5 | 0.58 | 0.95 | |
| CH P2O5 | 0.54 | 1.10 | region rates only |

New (FC decisions 2026-10-26):

- Time factor = IFASTAT consumption of the country, summed over the products, mean 2021-2023 / mean over the base
  years of L35 (`ifastat_fertiliser_time_factor.csv`, `scripts/build_ifastat_time_factor.py`, export of 2026-10-19).
  Only the ratios are stored (IFASTAT values reserved for IFA members, as for L45). It replaces
  `faostat_fertiliser_use_country.csv` for the FUBC 9 rates and the region rates; the own rates of the earlier
  reports (CH, CI, CO, CR, EC, KE, LK) stay without time scaling.
- A region rate (median of the region countries x factor of the country) is at most the highest rate of these
  countries, each brought to 2021-2023 with its own factor. The FUBC 9 countries are mapped to IFASTAT by
  `ifastat_fubc_country_mapping.csv` (71 rows, by name, signed by FC 2026-10-26). Bolivia (not a country of the export) and Burkina Faso (no
  value before 2020) have no factor and count unscaled.

Effect on the IFA table (6155 values of crop, country and nutrient): median ratio new / old 1.00, 5-95 % 0.63-1.29.
22 of the 117 factors of the tool countries differ by more than 30 %. The bound applies to 77 values, mostly by a
few percent (palm AR 166 -> 142 kg N/ha; sugar beet CI and ZA from Egypt and Morocco, up to 318 -> 237 kg N/ha).

| Crop, country | Before (kg N / P2O5 / K2O per ha) | After |
|---|---|---|
| wheat TH (region) | 202 / 234 / 127 | 127 / 94 / 63 |
| tea TH (region) | 533 / 215 / 206 | 336 / 86 / 103 |
| soybean PH (region) | 21 / 118 / 37 | 20 / 53 / 26 |
| rice TH (own) | 128 / 37 / 30 | 81 / 15 / 15 |
| rice PH (own) | 82 / 51 / 21 | 75 / 23 / 14 |
| palm ID (own) | 103 / 22 / 135 | 97 / 44 / 129 |
| wheat FR (own) | 149 / 15 / 14 | 140 / 13 / 11 |
| rice IN (own) | 153 / 59 / 17 | 152 / 58 / 17 |

Rejected: the median of the region countries each with its own factor (1354 of 1359 region values change, and the
FAOSTAT break of JP P2O5 74 -> 7 kg/ha in 2021 would enter).

Limit still open: the region median of a marginal crop comes from the countries where the crop is intensive (tea TH
336 kg N/ha from CN and JP).

Regression cases: no change (the cases give the mineral fertilisers in the template).

## 42. NH3 of urea and AS on flooded rice (decision L54, 2026-10-26)

Open point of L38 (section 27). EMEP/EEA 2023 Table 3-2 does not cover rice paddies: Annex 1 (pp. 34-35) says that
rice was not included in the 2023 analysis and keeps the text of the 2019 Guidebook, where an EF of 22 % for urea on
rice paddies is proposed by Yan et al. (2003) and the same EF is used for AS.

New: on the flooded crops of `crop_types.csv` (rice only), urea and AS take 22 % of the N applied as NH3-N, i.e.
0.22 x 17/14 = 0.2675 kg NH3 per kg N, for both pH classes (`emep2023_flooded_rice_nh3.csv`). The other fertiliser
types, and all types on the other crops, keep Table 3-2. FC choices (2026-10-26): apply the value; read it as NH3-N
(Yan et al. 2003 was not accessible, so the unit is not checked); all countries; only urea and AS.

| kg NH3 per kg N | Table 3-2 (normal / high pH) | Flooded rice |
|---|---|---|
| Urea | 0.195 / 0.206 | 0.2675 |
| AS | 0.084 / 0.187 | 0.2675 |

With the default N fertiliser mix and pH share of the countries, the mean NH3 factor of rice changes by x1.00 (FI,
no urea or AS) to x1.54 (PH), median about x1.3.

Regression, rice_IN (120 kg N urea):

| Key | Before | After |
|---|---|---|
| `ammonia_total` | 33.331 | 41.371 |
| `N2o_air` | 1.8362 | 1.8975 |
| `Nox_as_n2o_air` | 5.7177 | 5.4533 |
| `nitrate_to_groundwater` | 134.35 | 118.82 |

NOx and nitrate decrease because they are computed on the N left after the NH3 loss. apple_FR and wheat_IT: no change.

Limit: EMEP notes (Hayashi et al. 2006, 2008) that the high losses of paddy fields may reflect high temperatures and
apply less to temperate regions; the tool has no climate classes since L38, so the value applies everywhere.

## 43. Legacy crop x country matrices removed (decision L55, 2026-10-27)

Open point of section 37. Of the legacy matrices of N uptake, liquid and solid manure, mineral N and irrigation water
consumption, only 12 values were still read; they were hardcoded in the code. No value changes in this step.

| Legacy table | Values | Read | Now |
|---|---|---|---|
| `defaultMatrixNUptake.py` | 215 | 3: mulberry CN, IN, GLO = 400 kg N/ha | `data/legacy_n_uptake.csv` |
| `_LEGACY_EVAPO_TRANSPI_PER_CROP_PER_COUNTRY` | 1024 | 9: flax, hemp, mint, mulberry | `data/legacy_irrigation_water_consumption.csv` |
| `defaultMatrixTotalManure.py`, liquid and solid | 191 each | GLO = 0 only | explicit 0 in `ManureDefaultGenerator` |
| `defaultMatrixTotalMineralFert.py` | 191 | GLO = 0 only | explicit 0 in `MineralNitrogenDefaultGenerator` |

Irrigation water consumption kept, m3 per t of main product (legacy, undocumented, provisional):

| Crop | Values |
|---|---|
| flax | CN 229.87, FR 7.8, GLO 229.87 |
| hemp | CN 51.73, GLO 51.73 |
| mint | GLO 0 |
| mulberry | CN 300, IN 164.74, GLO 300 |

The default mineral N and the default manure are 0 for the crops without level 1 coefficients where IFA gives no rate,
or where the crop has no default yield as reference for the level 2 factor (guar, mulberry, pomegranate). This is the
result the legacy matrices gave (GLO cell 0), now written as a rule.

Check: every default of `DEFAULTS_VALUES_GENERATORS` for the 67 crops x 39 countries, with the default yield and with a
yield of 1000 kg, computed on `main` and on the branch: 689 832 values, no difference. Snapshots unchanged.

Open:

- sourced values for the 12 legacy values; mint GLO 0 is implausible (separate branch);
- 0 default mineral N and 0 default manure in 428 crop-country pairs: turmeric, ginger, flax, hemp, mulberry, guar and
  pomegranate in all 39 countries, mint and coriander in 38, cassava 16, cotton, chick pea and lentil 15, grape and
  sesame 4, ten crops in one country (mostly AU).

## 44. Sources for the remaining legacy values (decision L56, 2026-10-27)

Follow-up of section 43. The 12 legacy values moved to `data/` in L55, now with a source where one fits the basis of
the default yield.

Irrigation water consumption, m3 per t of main product:

| Crop | Before (legacy) | Now | Source |
|---|---|---|---|
| mint | GLO 0 | AR 101.3, MX 185.2, MA 154.8, GLO 150.9 | Mialyk et al. (2024), item 748, 2010-2019 |
| hemp | CN 51.73, GLO 51.73 | 17 countries, e.g. CN 0.5, FR 0, ES 357.8; GLO 3.86 | Mialyk et al. (2024), item 777, 2010-2019 |
| mulberry | IN 164.74, CN 300, GLO 300 | IN 164.73, GLO 164.73 | ecoinvent 3.12 'mulberry production, IN', irrigation (interview data) x 0.5 |
| flax | CN 229.87, FR 7.8, GLO 229.87 | unchanged (legacy) | no source on the basis of the default yield |

Not used:

- Pfister & Bayer (2014) 'flax' and 'hemp': their world production of 2000 (341 kt and 29 kt) is 1/2.4 and 1/3.9 of
  FAOSTAT 771 and 777 (824 kt and 113 kt), so they are per t of another product.
- Mialyk item 773 'Flax, processed but not spun': not the item of the default yield.
- The WFLDB datasets 'mint production' (US, IN; Fuchs et al. 2000) as a source: one literature value for the US, the
  IN dataset a proxy of it. They are the check: about 95 m3/t to air and 200-210 m3/t irrigation; the new default
  withdrawal for mint US is 242 m3/t at 1 t/ha.

N uptake of mulberry: kept at 400 kg N/ha (legacy). Published range: recommended doses for irrigated mulberry 168 kg
N/ha and year (CSR&TI Berhampore, Central Silk Board) and 350 kg N/ha and year (Dandin et al. 2003, South India); N
removed with the leaves 52-484 kg N/ha and year in Indian trials. Mulberry has no default yield and no leaf N content
with a source, so the uptake cannot be computed as for the other crops.

Changed defaults (67 crops x 39 countries): only the irrigation water of hemp, mint and mulberry (585 values), e.g.
withdrawal at 1 t/ha mint IN 0 -> 327 m3, hemp FR 69 -> 0 m3, hemp ES 68 -> 472 m3, mulberry CN 640 -> 351 m3.
Snapshots unchanged.

Limit: Mialyk is below the Pfister range for 74 % of the production (L44), so the hemp and mint values are probably on
the low side compared with the other crops.

## 45. Default mineral N without an IFA rate (decision L57, 2026-10-27)

Since L55 the crops without WFLDB level 1 coefficients had 0 kg mineral N and no manure where IFA gives no N rate for
the country: 428 crop-country pairs. New rule per crop (column `mineral_n_without_ifa_rate` of
`n_uptake_other_crop_parameters.csv`):

| Rule | Crops | Mineral N |
|---|---|---|
| `ifa_crop_median` | 19 crops with IFA rates in other countries | median of IFA rate / default yield over the countries with a rate, x yield |
| `n_uptake` | flax, hemp, ginger, turmeric, coriander, mint, guar, pomegranate | 0.8 x N uptake (WFLDB L1, N uptake of L41) |
| none | mulberry | 0 (legacy N uptake) |

The default manure follows the mineral N (L40). Examples at the default yield, kg N/ha (before 0):

| Crop | Country | Rule | Mineral N |
|---|---|---|---|
| cotton | ES | crop median | 105 |
| chick pea | AU | crop median | 38 |
| lentil | CN | crop median | 40 |
| cassava | CI / KE | crop median | 55 / 134 |
| bell pepper | AU | crop median | 122 |
| flax | FR | N uptake | 123 |
| hemp | FR | N uptake | 74 |
| ginger | IN | N uptake | 117 |
| mint | MX | N uptake | 114 |
| coriander | IN | N uptake | 16 |

Guar and pomegranate have no default yield: 0 at the default, 0.8 x N uptake with the yield of the template (guar IN at
1 t/ha: 13 kg N). Still 0: mulberry; chick pea and lentil FR, IT (IFA pulses rate 0).

Changed defaults (67 crops x 39 countries, default yield and 1000 kg): 4456 of 689 832 values (mineral N, manure,
fertiliser mixes of 24 crops; P2O5 and K2O of mint, level 1 minus the new default manure). Snapshots unchanged.

Limits: the L1 split is below the IFA rates for herbs (coriander IL x12), so coriander is probably low; the crop median
scales with the yield, so high default yields give high N (cassava GH 233, coriander KE 217 and MX 237, ginger and
turmeric US 327 kg N/ha; the coriander yields of FAOSTAT 711 in KE and MX, 13-15 t/ha, are to be checked).

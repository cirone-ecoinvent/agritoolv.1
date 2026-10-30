# data/

Input tables of the crop LCI model (`src/legacy_model`). Every file is registered in `sources.csv`, which gives
the full reference, edition, table or page and history of each file. This README is the short guide: where each
file comes from and what the model does with it. Decision numbers (L.., R..) refer to `docs/DECISIONS.md`.

Rules:

- All external values live in these CSV files and are read through `src/legacy_model/dataloader.py` or
  `defaultTables.py`. None is hardcoded.
- Tables derived from large downloads are rebuilt by the `scripts/build_*.py` named below. The raw files are
  in `external_data/`, which is git-ignored (see `external_data/README.md`).
- Values kept from the legacy tool without a source carry the note "legacy, undocumented, provisional".
- Mapping and review tables have `status` and `reviewed_by` columns. `scripts/review_status.py` checks that every
  row is reviewed; unreviewed rows stop the run.

The **Use** column below means:

- **model:** read when the model runs.
- **build:** read only by a build script that writes another table of this folder.
- **check:** read only by checks, tests or comparisons, never by the model.

## Registry

| File | Source | Use |
|---|---|---|
| `sources.csv` | AgriToolV.1 | Registry of all files: reference, edition, table or page, date added, notes. |
| `SOURCES.md` | AgriToolV.1 | Notes on the transcription of the Quantis (2019) tables and on the heavy-metal decisions backed by Nemecek et al. (2023). `sources.csv` is the registry. |

## General parameters and crop lists

| File | Source | Use | How it is used |
|---|---|---|---|
| `model_parameters.csv` | Quantis (2019) sections 2.2-2.7; EMEP/EEA 2023 3.D; IPCC 2006 Vol. 4 ch. 11; Faist Emmenegger et al. 2009; Prasuhn 2006; SALCA 2023; WFLDB Guidelines v3.0 (irrigation efficiencies); FC judgement (seed and pesticide thresholds). Source per row in column `source`. | model | Scalar parameters: emission factors (NH3, N2O, NOx), the nitrate and P model, heavy metals, irrigation efficiency, liquid manure density, the mineral N share of the N uptake, legume share, tree residues. Four soil constants are also hardcoded in `defaultGeneration.py` (open, L49). |
| `crop_types.csv` | Legacy `lucmodel.py`; FC decisions (flooded rice F7, planting amortisation, legumes L30) | model | Annual / perennial / flooded type of the 67 crops: selects the land use and LUC flows, the N2O factor of flooded rice, the amortisation of planting material and the legume rule of the N uptake. |
| `crop_key_aliases.csv` | Legacy `crops.properties` | model | Translates 16 legacy crop codes into the keys of `seed_exchange_mapping.csv`. |
| `faostat_country_mapping.csv` | FAOSTAT area codes (QCL download 2026-10-13) | model, build | Tool country -> FAOSTAT area code and M49 code. Used by all FAOSTAT-based build scripts and by the manure model for the IPCC region of the country. |
| `faostat_crop_item_mapping.csv` | FAOSTAT QCL item list; ecoinvent "crop mapping EI FAO.xlsx" | model, build | Tool crop -> FAOSTAT item, with the type of match. Defines the item of the default yield (L23) and links the crops to the Global atlas of pesticide use (L48). |

## Yield, seed and planting material

| File | Source | Use | How it is used |
|---|---|---|---|
| `default_yield.csv` | FAOSTAT QCL 2021-2024, element Yield; tea converted with Thevathasan & Thevadasan (1987). Built by `build_default_yield.py`. | model | Default yield per crop cycle and country, mean of the latest 4 years (L23, L24). |
| `default_seed.csv` | FAOSTAT SUA (seed) and QCL (area harvested) 2021-2024; FAO Technical Conversion Factors. Built by `build_default_seed.py`. | model | Default seed rate of the 16 sown crops with a usable source (L46). Column `source` = faostat_sua, fao_tcf or glo. |
| `seed_rate_crop_mapping.csv` | AgriToolV.1 (FAOSTAT and TCF item names) | model, build | Sown crop -> FAOSTAT seed item, area item and TCF item. `use` = sua_tcf or legacy (legacy seed kept). |
| `fao_tcf_seed_rates.csv` | FAO Technical Conversion Factors for Agricultural Commodities (data 1992-1996), extracted from the PDF | build | Seeding rates per country, used by `build_default_seed.py` as reference for the SUA rates. |
| `ecoinvent312_planting_rates.csv` | ecoinvent 3.12 cut-off, release file `exchanges (3.12, cut-off).xlsx`. Built by `build_ecoinvent_planting_rates.py`. | model | Planting material per ha and year or per ha and crop cycle, and plantation lifetime, of 133 ecoinvent datasets (L47). Only derived per-ha values are stored. |
| `ecoinvent312_planting_crop_mapping.csv` | AgriToolV.1 | model, build | Seedling and tree crops -> ecoinvent activities and quantity used (`use` = ecoinvent, proxy or legacy). |
| `ecoinvent312_orchard_lifetime.csv` | ecoinvent 3.12 undefined, release file `exchanges (3.12, undef).xlsx`. Built by `build_orchard_lifetime.py`. | model | Plantation lifetime (occupation / transformation) of 102 datasets of perennial crops, with a flag for the datasets made with this tool (L50). |
| `orchard_lifetime_crop_mapping.csv` | AgriToolV.1, values of FC | model, build | Crops with amortised planting -> ecoinvent activities of the lifetime, or lifetime set by FC (`use` = ecoinvent, proxy, fc or legacy). Gives the default `orchard_lifetime` (L50). |
| `seed_exchange_mapping.csv` | ecoinvent Master Data v3.12, IntermediateExchanges | model | Crop -> seed or seedling product written in the ecoSpold output. |

## Nitrogen uptake and mineral fertilisers

| File | Source | Use | How it is used |
|---|---|---|---|
| `wfldb2017_crop_nutrient_contents.csv` | WFLDB 3.1 Background Parameters 2017, sheet 4 | model | N, P2O5 and K2O per kg of product: default N uptake (L28) and default mineral P and K (L31); N of tree residues (L32). |
| `grudaf2009_table1_reference_yields.csv` | GRUDAF 2009 (Flisch et al.) Table 1 | model | Residue / main product ratio of the arable crops (L28) and N uptake of fibre flax and hemp (L41). |
| `n_uptake_crop_parameters.csv` | AgriToolV.1 | model | The 39 crops with WFLDB coefficients: WFLDB crop, GRUDAF row, residue ratio, tree residues. Their N uptake follows the yield; mineral N and manure are derived from it (L28, L29). |
| `n_uptake_other_crop_parameters.csv` | AgriToolV.1 | model | The 27 crops without WFLDB coefficients -> Ludemann item, GRUDAF row, IPCC residue row (L41); rule of the default mineral N without an IFA rate (L57). |
| `ludemann2023_world_crop_coefficients.csv` | Ludemann et al. (2023), Dryad, Tier 1 world coefficients. Built by `build_ludemann_crop_coefficients.py`. | model | N concentration of the product of the crops of `n_uptake_other_crop_parameters.csv` (L41). |
| `ipcc2019_table11_1a.csv` | IPCC 2019 Refinement Vol. 4 ch. 11, Table 11.1a | model | Residue N of the field crops without WFLDB coefficients (DRY x R_AG x N_AG, L41). |
| `legacy_n_uptake.csv` | Quantis GD_crop (legacy, undocumented, provisional) | model | Default N uptake of mulberry, the only crop without coefficients (L55); published range in the notes (L56). |
| `pk_crop_parameters.csv` | AgriToolV.1 | model | Mint -> WFLDB crop for the default mineral P and K (L31). |
| `ifa_fubc_rates.csv` | Ludemann et al. (2022) IFA Fertilizer Use by Crop, Dryad (FUBC 9 and earlier reports). Built by `build_ifa_fertiliser_use.py`. | model | Mineral N, P2O5 and K2O per ha by crop and country: default mineral fertiliser of the crops without WFLDB coefficients (L33-L37, L53). |
| `ifa_fubc_country_mapping.csv` | AgriToolV.1 | model, build | Tool country -> FUBC country and IFA region; the region gives the rate of a crop missing in the country (L37). |
| `ifa_fubc_crop_mapping.csv` | AgriToolV.1 | model, build | FUBC crop names -> tool crops (exact, subgroup, group). |
| `ifastat_fertiliser_mix.csv` | IFA IFASTAT, consumption by product 2021-2023. Built by `build_ifastat_fertiliser_mix.py`. Only derived shares (IFASTAT values are not stored). | model | Default split of mineral N, P2O5 and K2O into fertiliser types per country (L45). |
| `ifastat_fertiliser_time_factor.csv` | IFA IFASTAT, consumption 2015-2023. Built by `build_ifastat_time_factor.py`. Only derived ratios (IFASTAT values are not stored). | model | Ratio of fertiliser consumption 2021-2023 to the FUBC years: brings the FUBC rates to 2021-2023 and bounds the region rates (L35, L53). |
| `ifastat_country_mapping.csv` | AgriToolV.1 | build | Tool country -> IFASTAT country. |
| `ifastat_fubc_country_mapping.csv` | AgriToolV.1 | build | FUBC country -> IFASTAT country (L53). |
| `ifastat_product_type_mapping.csv` | AgriToolV.1 | build | IFASTAT products -> tool fertiliser types. |
| `emep2023_3d_table3_2.csv` | EMEP/EEA Guidebook 2023, 3.D Table 3-2 and Annex Table A1.1 | model | NH3 emission factors of the mineral fertilisers (L38). |
| `emep2023_fertiliser_type_mapping.csv` | AgriToolV.1 | model | Tool fertiliser types -> rows of Table 3-2. |
| `emep2023_flooded_rice_nh3.csv` | EMEP/EEA Guidebook 2023 3.D Annex 1 (text of 2019; Yan et al. 2003) | model | NH3 of urea and AS on flooded rice, 22 % of the N as NH3-N (L54). |
| `fertiliser_product_basis.csv` | AgriToolV.1 / Master Data 3.12 | check | Master Data product, amount basis and nutrient property of each mineral fertiliser exchange (R8). Read by `dataloader.py` for the ecoSpold writer and its tests; the contents themselves are read from the Master Data at run time. |

## Manure and other organic fertilisers

| File | Source | Use | How it is used |
|---|---|---|---|
| `grudaf2009_table39.csv` | GRUDAF 2009 chapter 11, Table 39 | model | N, soluble N, available N, P2O5 and K2O of farmyard manure: NH3 and N inputs of the manure (L12), conversion of the default organic N into m3 and t (L29), P and K of the manure subtracted from the default mineral P and K (L31). |
| `manure_type_composition.csv` | AgriToolV.1 | model | Tool manure types -> rows of GRUDAF Table 39 and EMEP Table 3-9, with weights (L12). |
| `emep2023_3b_table3_9.csv` | EMEP/EEA Guidebook 2023, 3.B Table 3-9 | model | NH3 emission factor at application, as share of TAN (L12). |
| `faostat_manure_n_applied_country.csv` | FAOSTAT Emissions from Livestock (GLE), manure applied to soils, 2021-2023. Built by `build_faostat_manure_country.py`. | model | Manure N per animal and country: default liquid / solid split and manure type shares per country (L29, L42). |
| `faostat_manure_n_applied_ipcc_region.csv` | FAOSTAT GLE 2021-2023 summed by IPCC region. Built by `build_faostat_manure_ipcc_region.py`. | model | World mix of the "other" liquid and solid manure (L13, L42). |
| `faostat_manure_n_applied_world.csv` | FAOSTAT GLE 2021-2023, sum of the countries | check | World totals; replaced in the model by the regional table since L42, kept as its control sum. |
| `manure_other_faostat_mapping.csv` | AgriToolV.1 | model, build | FAOSTAT livestock items -> tool manure types per form (L13). |
| `ipcc2019_table10a_awms.csv` | IPCC 2019 Refinement Vol. 4 ch. 10, Tables 10A.6-10A.9 | model | Manure management systems per region: liquid share of the N of cattle, buffalo, pigs and laying hens (L42). |
| `ipcc2019_awms_forms.csv` | IPCC 2019 Table 10A.10; EMEP/EEA 2016 | model | Form (liquid, solid, not applied) of each management system. |
| `ipcc2019_regions.csv` | IPCC 2019 Refinement Vol. 4 ch. 10 | model | Productivity class and fallback region of each IPCC region. |
| `ipcc2019_faostat_item_awms_mapping.csv` | AgriToolV.1 | model | FAOSTAT livestock items -> IPCC animal categories. |
| `ipcc2019_country_region.csv` | FAOSTAT GLE areas; UNSD M49. Built by `build_faostat_manure_ipcc_region.py`. | model | IPCC region of every FAOSTAT area. |
| `ipcc2019_m49_region_mapping.csv` | AgriToolV.1 (UNSD M49 sub-regions) | build | M49 sub-regions and exceptions -> IPCC regions. |
| `organic_fertiliser_composition.csv` | GRUDAF 2009 Table 42 (compost); Agribalyse 3.1 Tables 59 and 142 (sludge, feather meal, poultry droppings); some legacy values | model | N, TAN and P2O5 of compost, sewage sludge and other organic fertilisers, and their EMEP source category (L15, L20, L21). |
| `emep2023_3d_table3_1.csv` | EMEP/EEA Guidebook 2023, 3.D Table 3-1 | model | NH3 factors of sewage sludge and other organic wastes (L15). |

## Phosphorus and soil

| File | Source | Use | How it is used |
|---|---|---|---|
| `p_landuse_classes.csv` | Prasuhn (2006) SALCA-Phosphor, Tab. 1 and 2 | model | Average P leaching and run-off per land use class (`pmodel.py`). |
| `wfldb2017_agr_system_parameters.csv` | WFLDB 3.1 Background Parameters 2017, sheet 1 | model | Default site parameters per country (`defaultTables.py`): annual precipitation, clay and sand content, soil organic carbon, share of soils with pH <= 7, share of precipitation as snow; the soil-type shares give the soil erodibility (L22, L26, L27). MA and CS are legacy values. |
| `wfldb2017_soil_type_k_factors.csv` | WFLDB 3.1 Documentation 2017, Tab. 6 (Panagos et al. 2014) | model | K factor per soil type: default soil erodibility per country (L27). |

## Erosion factors (pending)

Transcribed for the erosion defaults of the template v3 specification (`docs/template_v3_spec.md`
section 5.13); awaiting confirmation by FC and not read by the model yet.

| File | Source | Use | How it is used |
|---|---|---|---|
| `panagos2015a_crop_c_factors.csv` | Panagos et al. (2015a), Table 1 | pending | C factor per arable crop (C_crop of C = C_crop x C_management). |
| `panagos2015a_tillage_factors.csv` | Panagos et al. (2015a), Eq. 4a | pending | Tillage factor of C_management: conventional 1, conservation or ridge 0.35, no till 0.25. |
| `borrelli2017_crop_group_c_factors.csv` | Borrelli et al. (2017), Supplementary Table 2 | pending | C factor of the crops not in Panagos Table 1, by crop group. |
| `borrelli2017_faostat_crop_groups.csv` | Borrelli et al. (2017), Supplementary Data 1 | pending | FAOSTAT crop -> crop group. |
| `ah537_p_factors.csv` | USDA Agriculture Handbook 537, Tables 13-15 | pending | P factor by support practice and slope class. |

## Irrigation and water

| File | Source | Use | How it is used |
|---|---|---|---|
| `aquastat_irrigation_technique_area.csv` | FAO AQUASTAT, area equipped by technique (export 2025-07-31). Built by `build_aquastat_irrigation_techniques.py`. | model | Default shares of surface, sprinkler and localized irrigation per country, hence the irrigation efficiency (L44). |
| `irrigation_technique_source.csv` | AgriToolV.1 | model | Per country: AQUASTAT or the legacy shares. |
| `wfldb2017_irrigation_water_sources.csv` | WFLDB 3.1 Background Parameters 2017, sheet 2 (Siebert et al. 2010) | model | Groundwater, surface water and tap water shares of irrigation water (L22). |
| `pfister2014_blue_water_country.csv` | Pfister & Bayer (2014), Appendix B and watershed data. Built by `build_pfister_blue_water.py`. | model | Default irrigation water per t of crop and country (expected value, with min and max) (L44). |
| `pfister2014_crop_mapping.csv` | AgriToolV.1 | model, build | Tool crops -> Pfister crops; hemp and mint -> Mialyk, flax and mulberry -> legacy table (L56). |
| `legacy_irrigation_water_consumption.csv` | Quantis GD_crop (flax, legacy, undocumented, provisional); ecoinvent 3.12 'mulberry production, IN' (mulberry) | model | Irrigation water per t of flax and mulberry, the crops without a Pfister or Mialyk value (L44, L55, L56). |
| `pfister2014_country_mapping.csv` | AgriToolV.1 | model, build | Tool countries -> Pfister countries. |
| `pfister2014_blue_water_watershed.csv` | Pfister & Bayer (2014), watershed and monthly data | check | Water use per watershed and month, kept for a future regionalisation of water scarcity; not read by the model. |
| `mialyk2024_national_blue_wf.csv` | Mialyk et al. (2024), national water footprints 2010-2019. Built by `build_mialyk_blue_water.py`. | model, check | Default irrigation water of hemp and mint (L56); cross-check of the Pfister default (`compare_mialyk_pfister.py`). |
| `mialyk2024_crop_mapping.csv` | AgriToolV.1 | model, check | Tool crops -> Mialyk items. |

## Pesticides

| File | Source | Use | How it is used |
|---|---|---|---|
| `atlas2026_pesticides_country.csv` | Zhang et al. (2026) Global atlas of pesticide use, Tables S1, S4, S6; FAOSTAT area harvested 2016-2020. Built by `build_atlas_pesticides.py`. | model | Default total pesticides (kg a.i. per ha) per crop and country (L48). |
| `atlas2026_pesticides_review.csv` | AgriToolV.1 | model | Flagged atlas values and whether the atlas or the fallback value is used. |
| `soil_fumigant_active_ingredients.csv` | Atlas Table S1 (active ingredient names) | build | Soil fumigants, for the information column and the review of flagged values only. |
| `wfldb2017_pesticides_total_ai.csv` | WFLDB 3.1 Documentation 2017, Excel annex | model | Total pesticides of the WFLDB datasets: fallback of the atlas and value of the crops not in the atlas (L43, L48). |
| `wfldb2017_pesticides_crop_mapping.csv` | AgriToolV.1 | model | WFLDB datasets -> tool crops. |
| `default_pesticides.csv` | Legacy GD_crop sheet Pesticides_L1 | model | The 9 crops without atlas or WFLDB value; legacy, undocumented, provisional. |
| `pesticide_crop_archetype_mapping.csv` | OLCApest mapping tool (AG updated) | model | Tool crops -> OLCA-Pest crop archetypes. |
| `olca_pest_default_fractions.csv` | Nemecek et al. (2022) OLCA-Pest, Online Resource 2, via the OLCApest mapping tool | model | Share of each pesticide reaching soil, crop, air and off-field: soil input of the metals in pesticides (L14). |

## Heavy metals

| File | Source | Use | How it is used |
|---|---|---|---|
| `hm_salca2023_table1.csv` | Nemecek et al. (2023) SALCAheavymetal V1.0, Table 1 | model | Metal contents of plant products, fertilisers, manure, organic fertilisers and pesticides for the heavy-metal balance (L10). |
| `hm_crop_product_mapping_salca2023.csv` | AgriToolV.1 | model | Tool crops -> SALCA plant products (harvest export and seed input). |
| `hm_coproduct_mapping.csv` | AgriToolV.1 | model | By-products -> SALCA "co-product, mean". |
| `hm_fertiliser_row_mapping.csv` | AgriToolV.1 | model | Mineral fertiliser types -> SALCA fertiliser rows. |
| `hm_manure_class_mapping.csv` | AgriToolV.1 | model | Manure types -> SALCA farmyard manure rows. |
| `hm_organic_fertiliser_mapping.csv` | AgriToolV.1 | model | Compost and sludge types -> SALCA organic fertiliser rows. |
| `hm_pesticide_mapping.csv` | AgriToolV.1 (contents from Perkow & Ploss 1994 via SALCA) | model | Metal-containing pesticides -> SALCA pesticide rows. |

## Land use change

| File | Source | Use | How it is used |
|---|---|---|---|
| `luc_blonk_country_expansion.csv` | WFLDB-adapted Blonk direct LUC tool 2016-06-09a, sheet 5 | model | Area expansion of all crops per country (L16). |
| `luc_blonk_crop_expansion.csv` | Same tool, sheet 6 | model | Area expansion per crop and country (L16). |
| `luc_product_mapping.csv` | AgriToolV.1 / Master Data 3.12 | model | Crop type and flooding -> LUC product of the Master Data. |

## Alignment with the ecoinvent Master Data

| File | Source | Use | How it is used |
|---|---|---|---|
| `elementary_flow_alignment.csv` | ecoinvent Master Data v3.12, ElementaryExchanges | check | Every elementary flow written by the ecoSpold writer, aligned with its Master Data name, UUID and unit. Maintained by `check_master_data.py`. |
| `intermediate_exchange_alignment.csv` | ecoinvent Master Data v3.12, IntermediateExchanges | check | Same for the intermediate exchanges. |

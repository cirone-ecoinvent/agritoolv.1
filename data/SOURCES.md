# Data sources

Tables transcribed from Quantis (2019), *Models integrated in ecoinvent LCI calculation tool
for crop production* (Ecoinvent_Tool_Model_Description_20191015.pdf), unless stated otherwise.

| File | Doc table | Original source |
|---|---|---|
| model_parameters.csv | sections 2.2-2.7 | see `source` column |
| hm_leaching_mg_per_ha_yr.csv | Tab. 2 | Wolfensberger & Dinkel 1997 (Ni n.a. -> 0, as in SALCAheavymetal 2023 Tab. 1) |
| hm_soil_content_mg_per_kg.csv | Tab. 3 | Keller & Desaules 2001 |
| hm_deposition_mg_per_ha_yr.csv | Tab. 4 | Freiermuth 2006 |
| hm_plant_content_mg_per_kg_dm.csv | Tab. 5 | Freiermuth 2006 (empty = NA; the code uses 0, see below) |
| hm_mineral_fertiliser_mg_per_kg_nutrient.csv | Tab. 6 | Desaules & Studer 1993 via Freiermuth 2006 (no Hg data) |
| hm_manure_mg_per_kg_dm.csv | Tab. 7 | Menzi & Kessler 1998; Desaules & Studer 1993; DM: Walther et al. 2001 |
| seed_exchange_mapping.csv | Annex 2/3, Tab. 5 crop lists | crop key -> IntermediateExchange of ecoinvent Master Data v3.12 (names and units verified); status proposed / to_decide / no_exchange until reviewed |
| ecoinvent_flows_md312.csv | - | elementary flows (name, compartment, UUID) from Master Data v3.12 for every flow the tool writes, incl. flooded-rice land use |

## Decisions backed by Nemecek et al. (2023), Int J LCA, Online Resources

* NA in plant contents -> 0: SALCAheavymetal V1.0 (ESM7) Tab. 1 reports 0 for the Hg values
  that are NA in Freiermuth 2006 (barley, straws, rice).
* Heavy-metal balance: ESM7 Eq. 3-7 (allocation applied once; algebraically identical to
  Msoil = (inputs + deposition - unallocated outputs) * A of Freiermuth 2006 / Quantis 2019).
* Drainage factor 6.0 and run-off slope threshold 3 %: SALCAfieldP V1.0 (ESM5) Eq. 2 and 5,
  both attributed to Prasuhn 2006.
* Split between ground and surface water by drained fraction: SALCAnitrate (ESM2) Eq. 11-12,
  SALCAheavymetal (ESM7) Eq. 5-6. For phosphate the same split is an assumption (ESM5 Eq. 5
  does not state it).

* N_som: SALCAfieldN V1.01 (ESM1) Eq. 5 puts N_som (SOM mineralisation after land use
  change) in the field N2O with EF 0.01; C:N ratios from Quantis 2.9.1.2.
* NOx: SALCAfieldN still uses 0.012 kg NOx-N/kg N (0.026 * 14/30), numerically the same as
  the corrected EEA 2016 value (0.04 * 14/46 = 0.0122). Only Quantis 2019 (0.0187) deviates.

## Master Data v3.12 remarks

* 'rice seed, for sowing' has CPC '01161: Rye, seed'; other questionable CPCs: 'grass seed'
  (01940 beet seeds), 'lentil seed' (01449 other oilseeds), 'carrot/oat/linseed/peanut seed,
  for sowing' (86112 seed processing services).
* Seedlings are in 'unit', seeds in 'kg'.

## Plausibility flags (for the new version)

* Rape seed Cd 1.6 / Pb 5.25 (Freiermuth 2006) vs 0.047 / 0.035 in SALCAheavymetal 2023
  (Koch & Salou 2015): the old values look wrong.
* Superphosphate Pb 578.95 vs triple superphosphate 7.61.
* Deposition in SALCAheavymetal 2023 differs strongly from Tab. 4 (e.g. Cu 23800 vs 2400 mg/ha/yr).
* SALCAfieldN Eq. 5 gives 0.025 for non-TAN organic N while calling it lower than 0.01
  (likely 0.0025); Eq. 8 lists NO3 among gaseous losses (likely N2O).
* SALCAfieldP 2023 states fertiliser amounts in kg P, Prasuhn 2006 as used by WFLDB/Quantis in
  kg P2O5 (factor 2.29): check against the original before the new version.

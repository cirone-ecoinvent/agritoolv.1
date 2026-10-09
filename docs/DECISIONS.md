# Decision log

Every methodological or organisational decision of the AgriTool project, newest last. Each entry
records the date, who decided, the decision, the reason and the alternatives that were rejected.
Decisions taken in chat with Claude Code are copied here; this file, the git history and the
review columns of the data tables (`status`, `reviewed_by`) are the authoritative record.
FC = Francesco Cirone (Sector Manager Agriculture, ecoinvent).

## Project organisation

| # | Date | By | Decision | Reason / alternatives |
|---|---|---|---|---|
| O1 | 2026-10-08 | FC | Chat in Italian; code, docstrings, comments, commits, reports in English. | Team and repository language is English. |
| O2 | 2026-10-08 | FC | Data rules: every external value (factor, parameter, table) lives in `data/*.csv`, is registered in `data/sources.csv`, is loaded through one data-loading module, never hardcoded, never taken from the web or from the assistant's knowledge; extracted tables are shown to FC before use. | Provenance and reproducibility of every number in an ecoinvent dataset. |
| O3 | 2026-10-09 | FC | `C:\python\sri-crop-tool` (legacy Quantis tool) is never modified; it is only consulted. All work happens in `C:\python\AgriToolV.1`; the goal is to use only AgriToolV.1 and delete sri-crop-tool later. | Clean separation between the reference and the new tool. Before this rule, fixes F1-F9 had been applied on a local branch `legacy-fixes` of sri-crop-tool following `legacy_fixes/CLAUDE_CODE_PROMPT.md`; that work was moved here (see M1). |
| O4 | 2026-10-09 | FC | The ecoinvent Master Data (`C:\python\external_data\MasterData (3.12, undef).xlsx`) is never changed and never copied into a repository; the tool harmonises with it. Its path is set in the git-ignored `agritool.cfg` or in `AGRITOOL_MASTER_DATA_PATH`. | The Master Data is the basis of ecoinvent. |
| O5 | 2026-10-09 | FC | Git in AgriToolV.1, pushed to the private repository github.com/cirone-ecoinvent/agritoolv.1 on top of its existing history (no force push; Copilot PR #2 left untouched); decisions recorded in this file. | Track every change during development. Rejected: keeping the project only on the local disk. |
| O6 | 2026-10-09 | FC | Review workflow: mapping and alignment tables carry `status` and `reviewed_by`; a row is final only when signed. `scripts/review_status.py` lists open rows. | The tables contain judgements (mappings, proposals) and unsourced legacy values that need an explicit owner. |

## Legacy analysis and fixes

| # | Date | By | Decision | Reason / alternatives |
|---|---|---|---|---|
| L1 | 2026-10-08 | FC | Analyse the legacy tool before changing anything: `docs/legacy_analysis.md`. | Baseline understanding. |
| L2 | 2026-10-09 | FC | Apply fixes F1-F9 of the specification package `legacy_fixes/` (read-only) to the legacy model, one fix per commit, with regression snapshots on three reference cases (wheat IT, rice IN, apple FR) showing every numerical change. | Details and old/new values: `docs/legacy_fixes_report.md`. |
| L3 | 2026-10-09 | FC | NOx: 0.04 kg NO2/kg N (EEA 2016 3.D Tab. 3-1) on N applied minus NH3-N, i.e. 0.012174 kg NOx-N/kg N (F1). | Deviation from Quantis 2019 (0.018667, conversion as NO). |
| L4 | 2026-10-09 | FC | D1: SQCB-NO3 regression applied per crop cycle; intercept and soil-N term scaled by the occupation period t = 1 / crop_cycle_per_year (from the harvest dates of the template, 1 when unknown); S and U as cycle totals. | Rejected: fixed 1-year period; keeping the legacy scaling of the water term only. |
| L5 | 2026-10-09 | FC | D5: one drained-fraction input, the template field `drainage` (ratio, default 0), used for NO3, phosphate and heavy-metal leaching. | Already the single input of the legacy tool. |
| L6 | 2026-10-09 | FC | P run-off slope rule: the template has no slope field, so the slope is unknown (factor s = 1) for all crops except flooded rice (0 %, run-off 0). | Rejected: s = 1 also for rice; adding a slope field to the template now. |
| L7 | 2026-10-09 | FC | Heavy-metal export with the harvest: main-product dry yield x Freiermuth 2006 Tab. 5 content via a crop-to-product mapping (generic mean when the crop is not in Tab. 5); by-products excluded. | Replaces 7 unsourced legacy uptake coefficients. Rejected: including by-products; keeping the legacy coefficients. |
| L8 | 2026-10-09 | FC | No Java changes (no JDK available); the requirements for the ecoSpold writer are listed in `docs/java_changes_pending.md`. | With O3 the Java code will not be changed at all; the list now serves as requirements for the new writer of AgriToolV.1. |
| L9 | 2026-10-09 | FC | Terminology of flows and products follows Master Data 3.12. Pure renames (e.g. "Cadmium, ion" -> "Cadmium II", capitalisation) are final without signature; proposals and decisions are reviewed in `data/elementary_flow_alignment.csv` and `data/intermediate_exchange_alignment.csv`. | O4. Open: Chromium III or VI; mineral fertilisers as generic "inorganic ... fertiliser" (same nutrient basis) or as products in kg (needs nutrient contents). |

## Data reviews (signed in the tables)

| # | Date | By | Table | Decision |
|---|---|---|---|---|
| R1 | 2026-10-09 | FC | `seed_exchange_mapping.csv` | All 72 rows reviewed: 58 confirmed, 14 no_exchange. Instructions applied: grass -> "grass seed, Swiss integrated production, for sowing"; chick pea -> "pea seed, for sowing"; sesame -> "sesame seed"; fruit trees and banana, grape, berries, mulberry, pineapple -> "fruit tree seedling, for planting"; cashew, olive, cocoa, coconut, palm, coffee, tea -> "tree seedling, for planting". |
| R2 | 2026-10-09 | FC | `seed_exchange_mapping.csv` / `crop_types.csv` | Asparagus and mango seedlings are amortised over the plantation lifetime ("yes"), like all perennial plantings: new column `planting_amortised_over_lifetime` in `crop_types.csv`. Open: asparagus uses the default lifetime of 20 years. |
| R3 | 2026-10-09 | FC | `hm_fertiliser_row_mapping.csv` | All 27 rows confirmed as proposed (legacy rows, generic means for compound fertilisers, Ca as CaO for the lime row, Zn stoichiometric). |
| R4 | 2026-10-09 | FC | `hm_manure_class_mapping.csv` | All 20 rows confirmed as proposed (legacy shares of the Tab. 7 manure classes). |

## Moves

| # | Date | By | Decision |
|---|---|---|---|
| M1 | 2026-10-09 | FC | Moved from sri-crop-tool (branch `legacy-fixes`, 15 commits from `9dbf8cc` to `6a6bcc9`, plus FC's uncommitted reviews) to AgriToolV.1: the Python model layer with fixes F1-F9 (`src/legacy_model/`), data and review tables (`data/`), tests and regression cases (`tests/legacy_model/`), scripts (`scripts/`), the Excel input template (`templates/`). Not moved: Java backend, Dart frontend, `bootstrap.py` (HTTP bridge to Java). The alignment script no longer reads the Java sources: the alignment tables are now the inventory of names. |

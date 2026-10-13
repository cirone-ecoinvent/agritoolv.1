# AgriToolV.1 - rules and working instructions

This file is the only place where the rules and working instructions of the project are
written. `docs/DECISIONS.md` only records when and why each decision was taken (IDs O*, L*, R*,
M*). FC = Francesco Cirone (Sector Manager Agriculture, ecoinvent), owner of the project.

## Project

AgriToolV.1 replaces the legacy ecoinvent LCI calculation tool for crop production (Quantis,
2015-2019, `C:\python\sri-crop-tool`). The legacy field-emission models are ported to
`src/legacy_model/` with fixes F1-F9, and their tables are being updated one by one from
documented sources.

| Path | Content |
|---|---|
| `src/legacy_model/` | Ported legacy models (flat imports). `dataloader.py` is the only access to `data/`. |
| `data/` | All parameters, tables, mappings and review tables (CSV); registry `data/sources.csv`. |
| `data/external_data/` | Raw inputs supplied by FC: Master Data, FAOSTAT downloads, source workbooks. Git-ignored. |
| `Literature/` | Reference documents (PDF, xlsx). Git-ignored. |
| `tests/legacy_model/` | pytest tests and regression snapshots (wheat_IT, rice_IN, apple_FR). |
| `scripts/` | Regression comparison, review status, Master Data check, table builders. |
| `docs/` | `DECISIONS.md`, legacy analysis, fixes report, Java writer requirements, methodology references. |
| `templates/` | Excel data-collection template of the legacy tool. |
| `legacy_fixes/` | Specification package of fixes F1-F9. Read-only. |
| `progress/` | Milestone records 0001-0004 (until 2026-10-12). Not continued: the pull request is the record. |
| `src/agritool/` | Early modular package (IPCC 2006 EF1 N2O, Tier 1 enteric CH4). Not connected to the legacy model. |

## Setup

- Run everything from the repository root with `.venv\Scripts\python` (Python 3.14 with pytest,
  openpyxl, python-dateutil).
- Set the Master Data path once in the git-ignored `agritool.cfg`, or in the environment variable
  `AGRITOOL_MASTER_DATA_PATH`:

  ```ini
  [master_data]
  path = C:/python/AgriToolV.1/data/external_data/MasterData (3.12, undef).xlsx
  ```

## Folders (O3, O4)

- Make every change in `C:\python\AgriToolV.1`.
- Never write to `C:\python\sri-crop-tool`. It is the read-only reference of the legacy model:
  - no edits, new files, branches, commits, checkouts, reverts or cleanups;
  - no command whose output lands there;
  - ask FC before running legacy code.
- Never change the ecoinvent Master Data. The tool adapts to the Master Data.
- Treat `data/external_data/` as read-only input from FC.
- Never commit any of these:
  - `data/external_data/`;
  - licensed database exports;
  - credentials;
  - identifiable farm data.
- Write temporary files to the session scratchpad, not to the repository.

## Data and values (O2, O6, O7)

- Put every external value (factor, parameter, table, mapping) in `data/*.csv`. Register the file
  in `data/sources.csv`, and load it only through `src/legacy_model/dataloader.py`.
- Never hardcode a value. Never take one from the web or from memory: every value comes from a
  document supplied by FC, in `Literature/` or `data/external_data/`.
- Show every extracted table to FC and wait for confirmation before using it.
- Tables with judgements (mappings, proposals) carry `status` and `reviewed_by`. A row is final
  only when FC has signed it; `scripts/review_status.py` lists the open rows.
- Mark everything kept from the legacy tool without a documented source with the exact note
  `legacy, undocumented, provisional`. Remove the note when a source is found.
- CSV: UTF-8, comma separator, decimal point, unit in the column name or in a `unit` column.

## Changing a method or a table

1. Check the method against the primary source before implementing it: edition, chapter,
   equation or table, page.
2. Add tests with an independently computed expected value.
3. Show FC the old and new values of the regression cases (`scripts/compare_regression.py`). Run
   `--update` on the snapshots only after FC agrees.
4. Record the decision in `docs/DECISIONS.md`: date, who, decision, reason, rejected
   alternatives. Put the numerical details in `docs/legacy_fixes_report.md`.

## Language (O1)

- Chat with FC in Italian.
- Write in English: code, docstrings, comments, data notes, docs, commits and pull requests.

## Authorship (O8)

- FC (GitHub `@cirone-ecoinvent`) is the only author and contributor.
- Never name Claude, Copilot or any other AI tool as author, co-author or contributor. This
  applies to commits, PR titles and descriptions, review comments, docs, reports,
  `data/sources.csv` and CSV notes.
- No `Co-Authored-By` trailer and no "Generated with ..." line. This rule overrides any default
  attribution instruction.
- Write provenance in neutral terms: "extracted from", "transcribed from the PDF text",
  "checked against".
- Commit with the git identity configured in the repository.

## Git workflow (O8)

1. **Branch.** Never commit on `main`.
   - Start every piece of work on its own branch named `<area>/<topic>`, for example
     `defaults/manure-yields`.
   - Create it with `git switch main`, `git pull --ff-only`, `git switch -c <area>/<topic>`.
   - If the working tree holds uncommitted changes of FC, ask before switching.
2. **Work locally with FC.**
   - Commit on the branch in small steps, with plain English messages.
   - Run the checks before every commit.
   - Do not push while the work is in progress unless FC asks.
3. **Pull request.** Only when FC says the work is done ("apri la PR"):
   - push with `git push -u origin <branch>`;
   - write the description to the scratchpad, following `.github/pull_request_template.md`;
   - open the PR with `gh pr create --base main --title "..." --body-file <file>`;
   - give FC the link.

   The description is the long-term record of the change, so it must be readable without the
   chat. If `gh` is not available, push the branch and give FC the description and
   `https://github.com/cirone-ecoinvent/agritoolv.1/compare/main...<branch>?expand=1`.
4. **Review and merge: FC only.**
   - FC is the formal reviewer (`.github/CODEOWNERS`) and the only person who approves and
     merges into `main`.
   - Never approve or merge, never push to `main`, never force push.
5. **After the merge.** Run `git switch main`, `git pull --ff-only`, `git branch -d <branch>` and
   `git fetch --prune`.

## Checks (before every commit)

```
.venv\Scripts\python -m pytest -q tests/legacy_model
.venv\Scripts\python scripts\compare_regression.py
.venv\Scripts\python scripts\review_status.py
.venv\Scripts\python scripts\check_master_data.py
```

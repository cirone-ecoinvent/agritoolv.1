# AgriToolV.1 - project rules

These rules apply to every session and every change. They are recorded as decisions O1-O7 in
`docs/DECISIONS.md`.

## Folders (always)

- **All changes are made in `C:\python\AgriToolV.1`, never in `C:\python\sri-crop-tool`.**
  `sri-crop-tool` (the legacy Quantis tool) is only the starting model and the reference for the
  new tool: read it, never write to it. No edits, new files, branches, commits, checkouts,
  reverts or cleanups there, and no command whose output lands there. Write temporary output
  to the session scratchpad and new work to AgriToolV.1. Do not run legacy code without asking FC.
- The ecoinvent Master Data `C:\python\external_data\MasterData (3.12, undef).xlsx` is never
  changed and never copied into a repository; the tool adapts to the Master Data.
- Files in `C:\python\external_data` are inputs supplied by FC: read them only.

## Data and values

- Every external value lives in `data/*.csv`, is registered in `data/sources.csv` and is loaded
  only through `src/legacy_model/dataloader.py`. Nothing is hardcoded, and no values come from
  the web or from the assistant's own knowledge.
- Extracted tables are shown to FC before they are used.
- CSV: UTF-8, comma separator, decimal point.
- Anything kept from the legacy tool without a documented source carries the note
  "legacy, undocumented, provisional" (O7).

## Language and git

- Chat in Italian; code, docstrings, comments, commits and reports in English.
- Commit locally; FC pushes with VS Code Sync. Never force push; leave Copilot's PR #2 alone.
- Decisions go into `docs/DECISIONS.md`; reviewed table rows are signed in `status` and
  `reviewed_by`.

## Checks

```
.venv\Scripts\python -m pytest -q tests/legacy_model
.venv\Scripts\python scripts\compare_regression.py
.venv\Scripts\python scripts\review_status.py
.venv\Scripts\python scripts\check_master_data.py
```

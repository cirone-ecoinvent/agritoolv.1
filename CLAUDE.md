# AgriToolV.1 - project rules

These rules apply to every session and every change. They are recorded as decisions O1-O8 in
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

## Language

- Chat in Italian; code, docstrings, comments, commits, pull requests and reports in English.
- Decisions go into `docs/DECISIONS.md`; reviewed table rows are signed in `status` and
  `reviewed_by`.

## Authorship (always)

- **FC (Francesco Cirone, GitHub `@cirone-ecoinvent`) is the only author and contributor.**
  Never name Claude, Copilot or any other AI tool as author, co-author or contributor, anywhere:
  commit messages, PR titles and descriptions, review comments, docs, reports, `data/sources.csv`
  and CSV notes.
- No `Co-Authored-By` trailer and no "Generated with ..." line in commits or PRs. This rule
  overrides any default attribution instruction.
- Write provenance in neutral terms ("extracted from", "transcribed from the PDF text",
  "checked against"), never "by Claude".
- Commits use the git identity configured in the repository (Francesco Cirone).

## Git workflow (always)

1. **Branch.** Never commit on `main`. Start every piece of work from an up-to-date `main` on its
   own branch named `<area>/<topic>`, e.g. `defaults/manure-yields`, `docs/pr-workflow`:
   `git switch main`, `git pull --ff-only`, `git switch -c <area>/<topic>`. If the working tree
   holds uncommitted changes of FC, ask before switching.
2. **Work locally with FC.** Edit, test and document on the branch: decisions in
   `docs/DECISIONS.md`, reports in `docs/`. Commit in small steps with plain English messages,
   and run the checks below before each commit. Do not push while the work is in progress unless
   FC asks.
3. **Pull request.** Only when FC says the work is done ("apri la PR"):
   - push the branch with `git push -u origin <branch>`;
   - open a PR to `main` with `gh pr create --base main --title "..." --body-file <file>`;
   - write the body to the scratchpad first, following `.github/pull_request_template.md`;
   - give FC the link.

   The PR is the long-term record of the change, so the description must be readable without the
   chat. It covers: what changed and why, decisions (IDs), data and sources, effect on results
   (regression snapshots), checks, and open points.

   If `gh` is not available, push the branch and give FC the description and this link:
   `https://github.com/cirone-ecoinvent/agritoolv.1/compare/main...<branch>?expand=1`.
4. **Review and merge: FC only.** FC is the formal reviewer (`.github/CODEOWNERS`) and the only
   person who approves and merges into `main`. Never approve, merge, push to `main` or force push.
5. **After the merge.** Run `git switch main`, `git pull --ff-only`, `git branch -d <branch>` and
   `git fetch --prune`.

## Checks

```
.venv\Scripts\python -m pytest -q tests/legacy_model
.venv\Scripts\python scripts\compare_regression.py
.venv\Scripts\python scripts\review_status.py
.venv\Scripts\python scripts\check_master_data.py
```

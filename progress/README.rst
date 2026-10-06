Progress records and recovery
=============================

This folder is the tracked record of AgriTool's development milestones.
Git is the authoritative history of source code; this folder explains what was
verified at each milestone, rather than holding duplicate source backups.

Recording a milestone
---------------------

Add a numbered ``.rst`` record (for example ``0002-soil-extension.rst``) after
validating a meaningful change. Include:

* Date and a short description of the milestone.
* Affected calculation blocks and scientific references.
* Tests and manual checks performed, with their outcomes.
* Known limitations and next steps.
* The earlier checkpoint commit or tag, if relevant.

Commit the record with its implementation. Find its exact checkpoint later with
``git log --oneline -- progress/``; a record need not contain the hash of its own
commit. Optional local data and scratch files belong in ``progress/local/``
(ignored by Git), never in tracked milestone records.

Safe recovery
-------------

Before recovering, inspect ``git status`` and commit or stash uncommitted work.
From the repository root:

1. Find and inspect the milestone::

       git log --oneline -- progress/
       git show <checkpoint-commit>

2. Inspect an old version without changing the working tree::

       git show <checkpoint-commit>:src/agritool/crop.py

3. Undo a specific faulty, non-merge commit while preserving shared history::

       git revert <faulty-commit>

4. Alternatively restore only the affected file from a known-good checkpoint::

       git restore --source=<checkpoint-commit> -- src/agritool/crop.py
       python -m unittest discover -s tests -v
       git add src/agritool/crop.py
       git commit -m "Restore crop block from verified checkpoint"

Replace placeholders with actual commit identifiers. Restore any coupled tests
and contracts as needed, then validate the complete change before committing.
Run tests after a revert as well. Do not use destructive resets or force pushes
to undo shared development history.

Initial milestone: modular foundation
-------------------------------------

Date: 2026-10-06

* Added independently editable crop, livestock, model, and inventory blocks.
* Implemented the IPCC 2006 EF1 soil nitrogen-input N2O term and Tier 1 annual
  enteric CH4 calculation with caller-supplied, sourced factors.
* Added standard-library tests for calculations, units, provenance, invalid
  inputs, overflow, and product normalization.
* Defined package installation, development guidelines, and this recovery
  workflow.
* Validation: 11 unit tests passed; editable package installation succeeded.
* Limits: partial methodology coverage; no verified ecoinvent flow mapping,
  licensed database content, or full agricultural inventory model.
* Next steps: select and review additional crop/livestock pathways and the
  intended ecoinvent release before adding blocks or database adapters.

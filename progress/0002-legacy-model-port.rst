Milestone 0002: legacy model port with fixes F1-F9
=================================================

Date: 2026-10-09

What was added
--------------

* ``src/legacy_model/``: the Python model layer of the legacy ecoinvent LCI calculation tool for
  crop production (Quantis, lci-generator 1.3.4-EI, 2015-2019), with the fixes F1-F9 of the
  specification package ``legacy_fixes/`` applied one per commit in the former local branch
  ``legacy-fixes`` of sri-crop-tool. All parameters and tables touched by the fixes are read from
  ``data/*.csv`` through ``src/legacy_model/dataloader.py``; provenance in ``data/sources.csv``.
* ``data/``: specification tables (Quantis 2019 Tab. 2-7, model parameters, Master Data 3.12 flows),
  mapping tables and review tables with ``status`` / ``reviewed_by`` columns.
* ``scripts/``: ``compare_regression.py`` (old vs new outputs of the reference cases),
  ``check_master_data.py`` (alignment of flow and product names with Master Data 3.12),
  ``review_status.py`` (open review rows).
* ``tests/legacy_model/``: unit tests per fix, regression snapshots for wheat IT, rice IN, apple FR,
  Master Data checks (skipped when the Master Data is not configured).
* ``templates/LCI-Database_Data-collection_Crop_v2.xlsx``: the input template of the legacy tool.
* ``docs/``: legacy analysis, fixes report, Java requirements, decision log.

Scientific references
---------------------

Quantis (2019) Models integrated in ecoinvent LCI calculation tool for crop production;
EEA (2016) EMEP/EEA Guidebook 3.D; IPCC (2006) Vol. 4 ch. 11; Faist Emmenegger et al. (2009);
Prasuhn (2006); Freiermuth (2006); Nemecek et al. (2023) SALCA ESM1, ESM2, ESM5, ESM7.
Per-fix references: ``docs/legacy_fixes_report.md``.

Validation
----------

* ``tests/legacy_model``: 70 passed (``.venv\Scripts\python -m pytest tests/legacy_model -q``),
  including the checks against Master Data 3.12.
* ``legacy_fixes`` specification: 22 passed (unchanged, hash verified).
* ``tests/test_agritool.py`` (milestone 0001): passes with ``src`` on the path.

Known limitations and next steps
--------------------------------

* The legacy Excel reader and ecoSpold2 writer (Java) are not ported: the model runs on the raw
  input dictionaries of the regression cases. Next: a Python reader for the template and a
  Python ecoSpold2 writer using the alignment tables.
* Open reviews: ``scripts/review_status.py`` (crop-to-product mapping, manure TAN values,
  Chromium III/VI, fertiliser products, pesticide names).
* The modular ``src/agritool`` package of milestone 0001 and the legacy port coexist; their
  integration is to be decided (docs/DECISIONS.md).

AgriTool development guidelines
==============================

Purpose and module boundaries
-----------------------------

AgriTool connects agricultural activity data to traceable LCA emissions.
Keep calculation blocks small and independently editable:

* ``models.py`` owns shared validation, factor metadata, and result contracts.
* ``crop.py`` and ``livestock.py`` own domain equations, not file I/O.
* ``inventory.py`` owns normalization and inventory preparation, not equations.
* ``__init__.py`` exposes the supported public API.

Use one authoritative implementation per equation. Add domain-specific modules
only when an existing block would otherwise mix unrelated responsibilities.
Do not embed database identifiers in scientific calculations.

Required workflow for every change
---------------------------------

1. Define the affected block, intended behavior, assessment boundary, and units.
2. Verify the method against a primary reference before implementing it. Record
   the guideline edition, chapter, equation/table, tier, applicable conditions,
   factor source, and exclusions. Never silently substitute a default factor.
3. Make a focused change. Prefer pure functions and standard-library tools;
   add dependencies only when necessary. Preserve existing public behavior or
   explicitly document a breaking change.
4. Add tests for an independently calculated reference value, unit conversions,
   zero inputs, invalid inputs, and relevant boundary cases. Reject negative and
   non-finite masses and keep mass emissions separate from CO2-equivalents.
5. Run targeted tests first, then all tests once the change is complete::

       python -m unittest discover -s tests -p test_agritool.py -v
       python -m unittest discover -s tests -v

6. Run the README example when changing the public API or inventory structure.
   Check packaging with ``python -m pip wheel --no-deps --wheel-dir /tmp/agritool-dist .``.
   Review the diff for scope, generated files, secrets, and sensitive field data.
7. Update the README for changed behavior. Record a verified milestone in
   ``progress/``, then commit the code, tests, and documentation together.

Set up the environment using the README. Tests use ``unittest`` and do not
require a third-party runner. Build outputs, virtual environments, and local
checkpoint data must remain untracked. No linter is currently configured.

Scientific and inventory review
-------------------------------

Before accepting a new block, a reviewer must check:

* Input units, time basis, geographic scope, livestock category where relevant,
  and whether activity data are totals or rates.
* Factor provenance and applicability, especially when using revised IPCC
  guidance or national factors instead of the 2006 defaults.
* Conversion between nitrogen mass and N2O mass, and any other stoichiometry.
* Explicit exclusions and no double counting between crop and livestock blocks.
* Consistent assessment periods, production normalization, and documented
  allocation for multi-product systems.
* An independently derived expected result, not just reproduction of the code.
* Verified target-release flow mapping before calling an inventory
  ecoinvent-compatible. The initial inventory output remains unmapped.

Do not commit licensed database exports, credentials, or identifiable farm data.
Use synthetic examples in tests and keep private working data outside the
repository. Recovery instructions and the initial milestone are in
``progress/README.rst``.

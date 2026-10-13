Milestone 0001: modular foundation
==================================

Date: 2026-10-06

* Added independently editable crop, livestock, model, and inventory blocks.
* Implemented the IPCC 2006 EF1 soil nitrogen-input N2O term and Tier 1 annual
  enteric CH4 calculation with caller-supplied, sourced factors.
* Added standard-library tests for calculations, units, provenance, invalid
  inputs, overflow, and product normalization.
* Defined package installation, development guidelines, and a recovery
  workflow.
* Validation: 11 unit tests passed; editable package installation succeeded.
* Limits: partial methodology coverage; no verified ecoinvent flow mapping,
  licensed database content, or full agricultural inventory model.
* Next steps: select and review additional crop/livestock pathways and the
  intended ecoinvent release before adding blocks or database adapters.

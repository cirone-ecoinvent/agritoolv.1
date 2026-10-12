Milestone 0004: names of the written flows aligned with Master Data 3.12
========================================================================

Date: 2026-10-12

What changed
------------

* ``data/elementary_flow_alignment.csv`` (402 rows) and ``data/intermediate_exchange_alignment.csv``
  (587 rows) are fully reviewed: every flow and product the ecoSpold writer will write has a
  Master Data 3.12 name and UUID (decisions R7, R8 in ``docs/DECISIONS.md``).
* Mineral fertilisers are written as specific Master Data products in kg of product. The nutrient
  content per kg of product is read from the Master Data sheet ``IntermediateExchanges prop.``
  at run time (``dataloader.fertiliser_nutrient_content``); the basis per model variable is in
  ``data/fertiliser_product_basis.csv``.
* Chromium emissions are written as Chromium III (FC choice).

Validation
----------

* ``tests/legacy_model``: all tests pass; the Master Data tests check that every fertiliser
  product has a positive content and that MAP, DAP, ANP, KCl and urea match their stated
  compositions.
* Regression snapshots unchanged (the writer is not implemented yet).

Gaps to report to the Master Data team
--------------------------------------

* ``urea``: no "nitrogen content" property (the tool uses the stoichiometric 0.4665 of CH4N2O).
* ``phosphate rock, beneficiated``: no "phosphorus content" property (raw phosphate is written
  as the generic "inorganic phosphorus fertiliser, as P2O5").
* Metiram: no elementary flow (Zineb used as proxy).

Open points
-----------

* The ecoSpold writer must apply the compound-fertiliser rule (one MAP / DAP / ANP / KNO3
  exchange, mass = min over its nutrients, rest on the generic product).
* CO2 from seaweed lime: biogenic carbon in the Master Data, fossil in ``co2model.py``.
* Land use change (decision L16): the exchange is in ha and is linked by geography. Master Data
  3.12 has no "land use change, annual crop" dataset for CL, CO, CR, CI, EC, GH, ID, KE, MA, PH,
  ZA, LK, TR, VN (BE, PL and CS are covered by the market group RER), no "land use change,
  perennial crop" dataset for AU, CA, FI, DE, HU, IL, MA, NL, NZ, PL, RU, CS, CH, TH, UA, and
  "land use change, paddy rice" only for CN and IN. The writer must handle crops with a non-zero
  amount in these countries (to be agreed with the Master Data team).

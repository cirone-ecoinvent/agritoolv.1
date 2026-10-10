Milestone 0003: heavy-metal model on SALCAheavymetal 2023
=========================================================

Date: 2026-10-10

What changed
------------

* All heavy-metal tables of ``src/legacy_model`` come from Table 1 of SALCAheavymetal V1.0
  (Nemecek et al. 2023, Int J LCA, Appendix 7), transcribed to ``data/hm_salca2023_table1.csv``
  and read through ``dataloader.hm_entry``: deposition, leaching, soil contents (7 land-use
  classes), plant contents (harvest and seed), mineral fertilisers (now with Hg and Mg), farmyard
  manure, compost and sewage sludge, metal-containing pesticides.
* Equations follow Eq. 2-7 of the document; implementation choices in ``docs/DECISIONS.md`` L10,
  L11 (co-products and 5 % of pesticide metals in the harvest export, compound fertilisers via
  the unspecified N row, sewage sludge per kg fresh matter, seedlings and trees at zero).
* The Quantis 2019 / Freiermuth 2006 heavy-metal tables were removed from ``data/`` (they remain
  in ``legacy_fixes/data`` and in the git history).

Validation
----------

* ``tests/legacy_model``: 80 passed; expected values use the numbers of Table 1.
* Regression snapshots updated in each of the eight commits ``HM 2023 (1/8)`` to ``(8/8)``.

Open points
-----------

* Rows still proposed: lime-ammonium nitrate and potassium nitrate (fertiliser mapping), compost
  DM 1.0 and five compost proxies (organic fertiliser mapping).
* Pesticide share reaching the field (0.95) to be replaced when Nemecek et al. 2022 is provided.
* Soil and deposition values are Swiss averages applied to all countries.

# AgriTool for ecoinvent

AgriTool is a Python-based agricultural emissions calculator for preparing
life cycle assessment (LCA) inventories from field crop and livestock data.
Independent calculation blocks keep methodologies, inputs, and inventory
preparation separate so each block can be reviewed and maintained on its own.

**Status: initial foundation, not a complete agricultural inventory model.**
The current package implements two IPCC calculation terms and prepares
traceable emissions per unit of product. It does not ship ecoinvent data or
produce a ready-to-import ecoinvent dataset.

## Setup

Requires Python 3.10 or newer. Run from the repository root:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

On Windows, activate with `.venv\Scripts\activate` instead.
There are no runtime dependencies; installation uses setuptools as the build
backend.

## Project structure

```text
pyproject.toml          Package metadata and build configuration
src/agritool/
    models.py          Shared validation, factor metadata, and emission results
    crop.py            Field crop calculation blocks
    livestock.py       Livestock calculation blocks
    inventory.py       Per-product inventory preparation, separate from equations
    __init__.py        Public Python API
tests/                 Standard-library unit tests
DEVELOPMENT.rst        Development rules and methodology review checklist
progress/              Tracked milestone records and recovery instructions

src/legacy_model/      Port of the legacy ecoinvent crop tool models, with fixes F1-F9
data/                  All external parameters, tables, mappings and review tables (CSV)
scripts/               Regression comparison, Master Data alignment, review status
tests/legacy_model/    Tests and regression cases of the legacy model port (pytest)
templates/             Excel data-collection template of the legacy tool
legacy_fixes/          Specification package of the fixes (read-only)
docs/                  Legacy analysis, fixes report, decision log, writer requirements
```

Keep one implementation of each equation in its calculation module; do not
copy equations into export code, notebooks, or milestone folders.

## Supported calculations and boundaries

The initial blocks follow the
[2006 IPCC Guidelines, Volume 4 (AFOLU)](https://www.ipcc-nggip.iges.or.jp/public/2006gl/vol4.html):

| Block | Calculation | Required units and scope |
| --- | --- | --- |
| `direct_soil_n2o` | Chapter 11, Equation 11.1, EF1 nitrogen-input term: `N × EF1 × 44/28` | Total kg N over the assessment period; factor in kg N₂O-N/kg N; result in kg N₂O |
| `enteric_methane` | Chapter 10, Equation 10.19, Tier 1: `annual mean animals × EF` | One livestock category; factor in kg CH₄/head/year; result in kg CH₄/year |

For the soil block, include only nitrogen inputs governed by the chosen EF1
(synthetic fertilizer, eligible organic additions, returned crop residues, and
eligible soil organic matter mineralization). Call separately where input
categories require different factors. This is **not** the full Equation 11.1:
grazing urine/dung and cultivated organic soils require separate terms.
Inputs are total nitrogen mass, not fertilizer mass or per-hectare rates.

Factors must be explicitly supplied with units and a source. Select the
appropriate guideline edition, climate, region, species, and management
system; no universal livestock factor is assumed. Review the 2019 Refinement
and applicable national guidance before using results in a study.
Ammonia, NOx, indirect N₂O, rice methane, manure management, upstream emissions,
uncertainty propagation, and full Tier 2/3 methods are not implemented.

## Example: a crop inventory

After installation, run:

```python
import json

from agritool import EmissionFactor, build_inventory, direct_soil_n2o

factor = EmissionFactor(
    value=0.01,
    unit="kg N2O-N/kg N",
    source="IPCC 2006 Volume 4 Chapter 11 Table 11.1, default EF1",
)
emission = direct_soil_n2o(nitrogen_kg=100, factor=factor)
inventory = build_inventory(
    [emission],
    reference_product="Wheat grain",
    production_amount=1000,
    production_unit="kg",
)
print(json.dumps(inventory, indent=2, allow_nan=False))
```

This illustrative scenario emits approximately **1.57143 kg N₂O in total**,
or **0.00157143 kg N₂O per kg grain**. Use measured activity data and justified
factors for real assessments.

`build_inventory` accepts emissions from either calculation block. Production
and emissions must cover the same system and period; do not combine unrelated
crop and herd results without defining allocation. Production must be positive.
Negative, non-finite, and incorrectly typed numeric inputs are rejected.

The JSON-compatible output records flow names, mass units, compartment,
methodology, and factor source. Its `mapping_status` is `unmapped`: before
ecoinvent use, map and verify each flow against the target release's identifiers,
subcompartments, and units, and define geography, time period, system boundary,
allocation, and reference product. This is an intermediate inventory, not an
EcoSpold exporter or an assertion of database compatibility.

## Development and recovery

Follow [DEVELOPMENT.rst](DEVELOPMENT.rst) for every change. Run the tests with:

```sh
python -m unittest discover -s tests -v
```

There is no configured linter or separate application server.
Record validated milestones in [progress/](progress/README.rst). Use Git
commits to recover earlier code; do not store duplicate source trees or
confidential field data in the progress folder.

## Legacy model port (`src/legacy_model`)

The field-emission models of the legacy ecoinvent LCI calculation tool for crop production
(Quantis, 2015-2019) were ported here with the verified fixes F1-F9
(`docs/legacy_fixes_report.md`). The legacy repository itself is not modified and will be
retired; every decision is recorded in [docs/DECISIONS.md](docs/DECISIONS.md).

Rules that apply to every change:

* All external values live in `data/*.csv`, are registered in `data/sources.csv` and are read
  only through `src/legacy_model/dataloader.py`; nothing is hardcoded.
* The ecoinvent Master Data is never changed or committed: the tool harmonises with it. Set its
  path once in a local, git-ignored `agritool.cfg`:

  ```ini
  [master_data]
  path = C:/python/external_data/MasterData (3.12, undef).xlsx
  ```

Run from the repository root with the project virtual environment (needs `pytest`,
`openpyxl` and `python-dateutil`):

```sh
.venv\Scripts\python -m pytest tests/legacy_model -q        # tests and regression snapshots
.venv\Scripts\python scripts\compare_regression.py          # old vs new outputs of the reference cases
.venv\Scripts\python scripts\review_status.py               # rows still to review in data/
.venv\Scripts\python scripts\check_master_data.py           # align names with the Master Data
```

Review workflow: the tables with columns `status` and `reviewed_by` are confirmed row by row
(status `confirmed`, `no_exchange` or `not_needed` plus the reviewer's initials). Unreviewed rows
of `seed_exchange_mapping.csv` stop a calculation; the other tables are listed by
`review_status.py` until they are signed.

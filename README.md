# AgriTool for ecoinvent

AgriToolV.1 calculates the field emissions of crop production for ecoinvent life cycle
inventories. It replaces the legacy ecoinvent LCI calculation tool for crop production (Quantis,
2015-2019). The legacy models are ported to `src/legacy_model/` with fixes F1-F9, and their
tables are being updated one by one from documented sources.

- Rules, setup, folder layout, checks and git workflow: [CLAUDE.md](CLAUDE.md)
- Decision log: [docs/DECISIONS.md](docs/DECISIONS.md)
- Reports:
  - [legacy analysis](docs/legacy_analysis.md)
  - [fixes report](docs/legacy_fixes_report.md)
  - [requirements for the new ecoSpold writer](docs/java_changes_pending.md)

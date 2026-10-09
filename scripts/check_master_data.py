"""Align the flow and product names used by the tool with the ecoinvent Master Data.

The tool must harmonise with the Master Data, never the other way round: the Master Data workbook
(path in agritool.cfg or AGRITOOL_MASTER_DATA_PATH) is only read.

The names to check are the rows of two review tables in data/:

  elementary_flow_alignment.csv       elementary flows written by the tool
  intermediate_exchange_alignment.csv intermediate exchanges (products) written by the tool

They were generated on 2026-10-09 from the ecoSpold writer of the legacy tool (Java templates and
pesticide mappings of sri-crop-tool); since then the tables themselves are the inventory of
names, so the legacy code is no longer needed. To add a flow, add a row with source,
model_variable, legacy_name, legacy_unit (and compartment / subcompartment for elementary flows)
and run this script.

For every row not yet signed in reviewed_by the script recomputes:

  status       ok        exact match in the Master Data, nothing to do
               renamed   same flow, Master Data spelling (documented rule below)
               proposed  proposal for the Master Data name: confirm or change it
               decision  several Master Data names are possible (see candidates): choose one
               missing   no candidate found: give a name or mark not_needed
  md312_name, md312_uuid, md312_unit, candidates, note

Signed rows (reviewer set status confirmed / not_needed and reviewed_by) are kept; only their
UUID and unit are refreshed, and names that do not exist in the Master Data are reported.

Usage (repository root):  .venv\\Scripts\\python scripts\\check_master_data.py
"""
import csv
import difflib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "legacy_model"))

import config  # noqa: E402

DATA = ROOT / "data"
ELEMENTARY_FILE = DATA / "elementary_flow_alignment.csv"
INTERMEDIATE_FILE = DATA / "intermediate_exchange_alignment.csv"

# Legacy names (ecoinvent 3.4 era) -> Master Data 3.12 name of the same flow. Master Data 3.12
# has only the ionic forms of these metals in water and agricultural soil.
RENAME_RULES = {
    "Cadmium, ion": "Cadmium II", "Cadmium": "Cadmium II",
    "Lead": "Lead II", "Mercury": "Mercury II",
    "Nickel, ion": "Nickel II", "Nickel": "Nickel II",
    "Zinc, ion": "Zinc II", "Zinc": "Zinc II",
    "Copper, ion": "Copper ion",
}

# Proposals that rely on a judgement (spelling variant, synonym, generic product with the same
# reference basis): status "proposed" with the reason, to be confirmed by the reviewer.
PROPOSAL_RULES = {
    "Phenol, pentachloro-": ("Pentachlorophenol", "same substance, index name vs common name"),
    "Dimethenamid": ("Dimethenamide", "racemic dimethenamid; Dimethenamid-P is the S-enantiomer"),
    "2-Amino-3-chloro-1,4-naphthoquinone": ("Quinoclamine", "chemical name of quinoclamine (CAS 2797-51-5)"),
    "Fosetyl-aluminium": ("Fosetyl-Al", "same substance, abbreviated name"),
    "Iprodion": ("Iprodione", "German spelling"),
    "Prothioconazol": ("Prothioconazole", "German spelling"),
    "Pyraclostrobin (prop)": ("Pyraclostrobin", "suffix (prop) dropped"),
    "Thiophanat-methyl": ("Thiophanate-methyl", "German spelling"),
    "nitrogen fertiliser, as N": ("inorganic nitrogen fertiliser, as N", "generic mineral N fertiliser, same basis (kg N)"),
    "phosphate fertiliser, as P2O5": ("inorganic phosphorus fertiliser, as P2O5", "generic mineral P fertiliser, same basis (kg P2O5)"),
    "potassium fertiliser, as K2O": ("inorganic potassium fertiliser, as K2O", "generic mineral K fertiliser, same basis (kg K2O)"),
    "ammonia, liquid": ("ammonia, anhydrous, liquid", "same product, amount already in kg NH3"),
    "triazine-compound, unspecified": ("triazine-compound", "', unspecified' dropped in 3.12"),
    "transport, tractor and trailer, agricultural": ("transport, freight, tractor and trailer, diesel, agricultural", "same service, unit metric ton*km"),
    "cotton seed": ("cottonseed, for sowing", "superseded by the seed mapping of Fix F6"),
}

# Several Master Data names are possible; the reviewer chooses.
DECISION_RULES = {
    "Chromium, ion": (["Chromium III", "Chromium VI"], "two different substances"),
    "Chromium": (["Chromium III", "Chromium VI"], "two different substances"),
    "Cyfluthrin": (["Beta-cyfluthrin"], "only the beta isomer mixture exists: use it or drop the flow"),
    "Pyrethrine": (["Pyrethrins", "Pyrethrin I", "Pyrethrin II"], "group vs single components"),
    "Pyrethrum": (["Pyrethrum, natural", "Pyrethrins"], "natural extract vs active components"),
    "ammonium nitrate, as N": (["inorganic nitrogen fertiliser, as N", "ammonium nitrate"],
                               "generic as N (same basis) or product in kg (needs N content)"),
    "urea, as N": (["inorganic nitrogen fertiliser, as N", "urea"], "generic as N (same basis) or product in kg (needs N content)"),
    "ammonium sulfate, as N": (["inorganic nitrogen fertiliser, as N", "ammonium sulfate"],
                               "generic as N (same basis) or product in kg (needs N content)"),
    "potassium chloride, as K2O": (["inorganic potassium fertiliser, as K2O", "potassium chloride"],
                                   "generic as K2O (same basis) or product in kg (needs K2O content)"),
    "potassium sulfate, as K2O": (["inorganic potassium fertiliser, as K2O", "potassium sulfate"],
                                  "generic as K2O (same basis) or product in kg (needs K2O content)"),
    "phosphate rock, as P2O5, beneficiated, dry": (["phosphate rock, beneficiated", "inorganic phosphorus fertiliser, as P2O5"],
                                                   "product in kg (needs P2O5 content) or generic as P2O5"),
    "lime": (["limestone, milled, packed", "limestone, milled, loose", "limestone, crushed, washed", "limestone, from algae"],
             "'lime' no longer exists; the model amount is kg CaCO3 (seaweed lime: Ca(OH)2)"),
}

REVIEW_STATUSES = ("confirmed", "not_needed")


def read_sheet(workbook, name):
    it = workbook[name].iter_rows(values_only=True)
    header = [str(h) for h in next(it)]
    return [dict(zip(header, r)) for r in it]


def read_table(path):
    with open(path, newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if any((v or "").strip() for v in r.values())]


def propose(legacy_name, lookup, pool):
    """(status, md312_name, candidates, note) for a legacy name. ``lookup(name)`` -> MD row."""
    if lookup(legacy_name):
        return "ok", legacy_name, "", ""
    if legacy_name in RENAME_RULES and lookup(RENAME_RULES[legacy_name]):
        return "renamed", RENAME_RULES[legacy_name], "", "Master Data 3.12 name of the same flow"
    case_match = [n for n in pool if n.lower() == legacy_name.lower()]
    if case_match:
        return "renamed", case_match[0], "", "capitalisation only"
    if legacy_name in PROPOSAL_RULES and lookup(PROPOSAL_RULES[legacy_name][0]):
        name, reason = PROPOSAL_RULES[legacy_name]
        return "proposed", name, "", reason
    if legacy_name in DECISION_RULES:
        options, reason = DECISION_RULES[legacy_name]
        return "decision", "", " | ".join(o for o in options if lookup(o)), reason
    return "missing", "", " | ".join(difflib.get_close_matches(legacy_name, pool, n=4, cutoff=0.6)), ""


def update_table(path, lookup, pool_for):
    """Recompute unsigned rows, refresh signed rows, write the table back; return problems."""
    rows = read_table(path)
    problems = []
    for row in rows:
        md_lookup = lambda name, r=row: lookup(r, name)  # noqa: E731
        if row.get("reviewed_by", "").strip():
            md = md_lookup(row["md312_name"]) if row["md312_name"] else None
            if row["status"] not in REVIEW_STATUSES:
                problems.append("%s: signed row with status '%s' (use confirmed or not_needed)"
                                % (row["legacy_name"], row["status"]))
            if row["status"] == "confirmed" and not md:
                problems.append("%s: md312_name '%s' not in the Master Data" % (row["legacy_name"], row["md312_name"]))
        else:
            status, name, candidates, note = propose(row["legacy_name"], md_lookup, pool_for(row))
            md = md_lookup(name) if name else None
            row.update(status=status, md312_name=name, candidates=candidates, note=note)
        row["md312_uuid"] = md["id"] if md else ""
        row["md312_unit"] = md["unitName"] if md else ""
        if row["md312_unit"] and row["md312_unit"] != row["legacy_unit"] and "UNIT:" not in row["note"]:
            row["note"] = (row["note"] + "; " if row["note"] else "") + \
                "UNIT: tool uses %s, Master Data %s" % (row["legacy_unit"], row["md312_unit"])
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print("%s: %d rows %s" % (path.relative_to(ROOT), len(rows), counts))
    for p in problems:
        print("  PROBLEM:", p)
    return problems


def main():
    from openpyxl import load_workbook
    wb = load_workbook(config.require_master_data_path(), read_only=True, data_only=True)
    elementary = {(r["name"], r["compartment"], r["subcompartment"]): r for r in read_sheet(wb, "ElementaryExchanges")}
    intermediate = {r["name"]: r for r in read_sheet(wb, "IntermediateExchanges") if r["name"]}
    pools = {}
    for (n, c, s) in elementary:
        pools.setdefault((c, s), []).append(n)
    all_products = sorted(intermediate)

    problems = update_table(
        ELEMENTARY_FILE,
        lambda row, name: elementary.get((name, row["compartment"], row["subcompartment"])),
        lambda row: pools.get((row["compartment"], row["subcompartment"]), []))
    problems += update_table(INTERMEDIATE_FILE, lambda row, name: intermediate.get(name), lambda row: all_products)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

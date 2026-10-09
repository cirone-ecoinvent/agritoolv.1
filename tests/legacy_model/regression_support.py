"""Helpers shared by the regression test and the comparison script.

A regression case is a pair of JSON files in ``regression_cases/``:
``<name>.inputs.json`` (raw inputs as produced by the Java ``ValueGroup.flattenValues()``) and
``<name>.expected.json`` (the ``OutputMapping.output`` dict recorded for the committed code).
"""
import json
from pathlib import Path

CASES_DIR = Path(__file__).resolve().parent / "regression_cases"
REL_TOL = 1e-9
ABS_TOL = 1e-12


def case_names():
    return sorted(p.name[: -len(".inputs.json")] for p in CASES_DIR.glob("*.inputs.json"))


def load_inputs(name):
    with open(CASES_DIR / (name + ".inputs.json"), encoding="utf-8") as f:
        data = json.load(f)
    data.pop("_description", None)
    return data


def load_expected(name):
    path = CASES_DIR / (name + ".expected.json")
    if not path.is_file():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_expected(name, output):
    with open(CASES_DIR / (name + ".expected.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(output, f, indent=2, sort_keys=True)
        f.write("\n")


def run_case(name):
    """Run the model sequence on a case and return the JSON-compatible output dict.

    The snapshots record the model numbers only: the Master Data seed lookup (Fix F6, tested in
    test_fix_f6_seed_exchanges.py) is switched off so that the result does not depend on the
    local agritool.cfg or on the review state of seed_exchange_mapping.csv.
    """
    import config
    from modelsSequence import ModelsSequence
    original = config.master_data_path
    config.master_data_path = lambda: None
    try:
        output = ModelsSequence(load_inputs(name)).executeSequence()
    finally:
        config.master_data_path = original
    return json.loads(json.dumps(output, default=str))


def differences(old, new):
    """Keys whose value changed (or appeared / disappeared) between two output dicts."""
    diffs = []
    for key in sorted(set(old) | set(new)):
        a, b = old.get(key), new.get(key)
        if a == b:
            continue
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            if abs(a - b) <= max(ABS_TOL, REL_TOL * max(abs(a), abs(b))):
                continue
        diffs.append((key, a, b))
    return diffs

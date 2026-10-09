"""Compare the current model outputs of the regression cases with the recorded snapshots.

Usage (from the repository root, with the Python layer on the path):
    (no PYTHONPATH needed)
    python scripts/compare_regression.py            # print old vs new for changed keys
    python scripts/compare_regression.py --update   # also rewrite the snapshots
    python scripts/compare_regression.py --keys ammonia_total N2o_air   # restrict the report
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "legacy_model"))
sys.path.insert(0, str(ROOT / "tests" / "legacy_model"))

import regression_support as rs  # noqa: E402


def fmt(value):
    if isinstance(value, float):
        return "%.6g" % value
    return repr(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--update", action="store_true", help="rewrite the snapshots with the current outputs")
    parser.add_argument("--keys", nargs="*", help="report only these output keys")
    parser.add_argument("--markdown", action="store_true", help="print a Markdown table")
    args = parser.parse_args()

    for name in rs.case_names():
        old = rs.load_expected(name) or {}
        new = rs.run_case(name)
        diffs = rs.differences(old, new)
        if args.keys:
            diffs = [d for d in diffs if d[0] in args.keys]
        print("\n=== %s: %d changed key(s) ===" % (name, len(diffs)))
        if args.markdown and diffs:
            print("| key | old | new | ratio new/old |")
            print("|---|---|---|---|")
        for key, a, b in diffs:
            ratio = ""
            if isinstance(a, (int, float)) and isinstance(b, (int, float)) and a not in (0, None):
                ratio = "%.4f" % (b / a)
            if args.markdown:
                print("| `%s` | %s | %s | %s |" % (key, fmt(a), fmt(b), ratio))
            else:
                print("  %-55s %14s -> %14s  %s" % (key, fmt(a), fmt(b), ratio))
        if args.update:
            rs.save_expected(name, new)
            print("  snapshot written")


if __name__ == "__main__":
    main()

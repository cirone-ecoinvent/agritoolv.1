"""Regression test: the model outputs for the reference cases must equal the recorded snapshots.

Every intentional numerical change of a fix commit is made visible by updating the snapshots
with ``scripts/compare_regression.py --update`` and reviewing the printed old/new table.
"""
import pytest

import regression_support as rs


@pytest.mark.parametrize("name", rs.case_names())
def test_outputs_match_snapshot(name):
    expected = rs.load_expected(name)
    assert expected is not None, "no snapshot for %s; run scripts/compare_regression.py --update" % name
    diffs = rs.differences(expected, rs.run_case(name))
    assert not diffs, "\n".join("%s: %r -> %r" % d for d in diffs)

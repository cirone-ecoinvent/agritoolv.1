"""pytest configuration for the legacy model port.

Puts ``src/legacy_model`` (the model layer, flat imports such as ``import dataloader`` and
``from models.nmodel import NModel``) and this folder on ``sys.path``, so the tests run from the
repository root with:

    .venv\\Scripts\\python -m pytest tests/legacy_model -q
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (HERE.parents[1] / "src" / "legacy_model", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

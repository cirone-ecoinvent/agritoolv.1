"""Shared units, validation, and traceable calculation results."""

from dataclasses import dataclass
from math import isfinite


def nonnegative(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite, non-negative number")
    try:
        valid = isfinite(value) and value >= 0
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError(f"{name} must be a finite, non-negative number")
    return value


def nonempty(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


@dataclass(frozen=True)
class EmissionFactor:
    """A caller-selected factor with its units and bibliographic source."""

    value: float
    unit: str
    source: str

    def __post_init__(self) -> None:
        nonnegative(self.value, "factor value")
        nonempty(self.unit, "factor unit")
        nonempty(self.source, "factor source")


@dataclass(frozen=True)
class Emission:
    """Total emitted mass in kg over the caller's assessment period."""

    flow: str
    amount_kg: float
    methodology: str
    factor_source: str
    compartment: str = "air"

    def __post_init__(self) -> None:
        nonnegative(self.amount_kg, "emission amount")
        for name in ("flow", "methodology", "factor_source", "compartment"):
            nonempty(getattr(self, name), name)

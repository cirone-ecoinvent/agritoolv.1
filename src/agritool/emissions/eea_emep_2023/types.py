"""Shared typed reference data for the EMEP/EEA 2023 methods."""

from dataclasses import dataclass
from enum import Enum

from agritool.models import nonempty, nonnegative


class ClimateZone(str, Enum):
    """Guidebook PM climate classes: Mediterranean (dry) and all others (wet)."""

    DRY = "dry"
    WET = "wet"


@dataclass(frozen=True)
class FactorEntry:
    """A guidebook factor with its published unit and table citation."""

    value: float
    unit: str
    table_reference: str

    def __post_init__(self) -> None:
        nonnegative(self.value, "factor value")
        nonempty(self.unit, "factor unit")
        nonempty(self.table_reference, "factor table reference")

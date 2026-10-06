"""Tier 2 NH3 emissions from inorganic fertilisers.

Factors are from EMEP/EEA Guidebook 2023, Chapter 3.D, section 3.4.1,
Equation (4) and Table 3-2. The table gives g NH3 per kg N applied; values
are converted to kg NH3 per kg N for the calculation.
"""

from collections.abc import Mapping
from enum import Enum

from agritool.models import Emission, EmissionFactor, nonnegative
from agritool.emissions.eea_emep_2023.types import ClimateZone, FactorEntry


class FertilizerType(str, Enum):
    ANHYDROUS_AMMONIA = "Anhydrous ammonia (AH)"
    AN = "AN"
    AMMONIUM_PHOSPHATE = "Ammonium phosphate (AP)"
    AS = "AS"
    CAN = "CAN"
    NK_MIXTURES = "NK mixtures"
    NPK_MIXTURES = "NPK mixtures"
    NP_MIXTURES = "NP mixtures"
    N_SOLUTIONS = "N solutions"
    OTHER_STRAIGHT_N_COMPOUNDS = "Other straight N compounds"
    UREA = "Urea"


class SoilPHClass(str, Enum):
    NORMAL = "normal"
    HIGH = "high"


_TABLE_REFERENCE = (
    "EMEP/EEA Guidebook 2023, Chapter 3.D, section 3.4.1, Table 3-2"
)
_NH3_EF_G_PER_KG_N: dict[tuple[FertilizerType, SoilPHClass], FactorEntry] = {
    key: FactorEntry(value, "g NH3/kg N", _TABLE_REFERENCE)
    for key, value in {
        (FertilizerType.ANHYDROUS_AMMONIA, SoilPHClass.NORMAL): 20,
        (FertilizerType.ANHYDROUS_AMMONIA, SoilPHClass.HIGH): 20,
        (FertilizerType.AN, SoilPHClass.NORMAL): 24,
        (FertilizerType.AN, SoilPHClass.HIGH): 52,
        (FertilizerType.AMMONIUM_PHOSPHATE, SoilPHClass.NORMAL): 84,
        (FertilizerType.AMMONIUM_PHOSPHATE, SoilPHClass.HIGH): 187,
        (FertilizerType.AS, SoilPHClass.NORMAL): 84,
        (FertilizerType.AS, SoilPHClass.HIGH): 187,
        (FertilizerType.CAN, SoilPHClass.NORMAL): 24,
        (FertilizerType.CAN, SoilPHClass.HIGH): 52,
        (FertilizerType.NK_MIXTURES, SoilPHClass.NORMAL): 24,
        (FertilizerType.NK_MIXTURES, SoilPHClass.HIGH): 52,
        (FertilizerType.NPK_MIXTURES, SoilPHClass.NORMAL): 84,
        (FertilizerType.NPK_MIXTURES, SoilPHClass.HIGH): 187,
        (FertilizerType.NP_MIXTURES, SoilPHClass.NORMAL): 84,
        (FertilizerType.NP_MIXTURES, SoilPHClass.HIGH): 187,
        (FertilizerType.N_SOLUTIONS, SoilPHClass.NORMAL): 87,
        (FertilizerType.N_SOLUTIONS, SoilPHClass.HIGH): 161,
        (FertilizerType.OTHER_STRAIGHT_N_COMPOUNDS, SoilPHClass.NORMAL): 24,
        (FertilizerType.OTHER_STRAIGHT_N_COMPOUNDS, SoilPHClass.HIGH): 187,
        (FertilizerType.UREA, SoilPHClass.NORMAL): 195,
        (FertilizerType.UREA, SoilPHClass.HIGH): 206,
    }.items()
}

_FACTOR_UNIT = "g NH3/kg N"
_TABLE_SOURCE = _TABLE_REFERENCE


def _enum_value(enum_type: type[Enum], value: object, name: str) -> Enum:
    if enum_type is FertilizerType and value == "Anhydrous ammonia":
        value = FertilizerType.ANHYDROUS_AMMONIA.value
    elif enum_type is FertilizerType and value == "Ammonium phosphate":
        value = FertilizerType.AMMONIUM_PHOSPHATE.value
    try:
        return enum_type(value)
    except (TypeError, ValueError):
        raise ValueError(f"unknown {name}: {value!r}") from None


def ammonia_from_n_fertilizers(
    nitrogen_kg_by_fertilizer: Mapping[FertilizerType | str, float],
    climate_zone: ClimateZone | str,
    soil_ph: SoilPHClass | str,
    factor_overrides: Mapping[
        tuple[FertilizerType | str, SoilPHClass | str], EmissionFactor
    ]
    | None = None,
) -> Emission:
    """Calculate total NH3 from applied inorganic fertiliser N.

    Input amounts are total kg N by fertiliser type for one soil-pH region.
    Normal pH is ≤7.0; high pH is >7.0. ``climate_zone`` is validated and
    retained as caller context, but Table 3-2 specifies no climate adjustment.
    To represent more than one pH region, calculate each region separately.
    Overrides are keyed by (fertiliser type, soil-pH class) and use the table
    unit, g NH3/kg N.
    """
    if not isinstance(nitrogen_kg_by_fertilizer, Mapping):
        raise ValueError("nitrogen_kg_by_fertilizer must be a mapping")
    _enum_value(ClimateZone, climate_zone, "climate zone")
    pH_class = _enum_value(SoilPHClass, soil_ph, "soil pH class")
    if factor_overrides is not None and not isinstance(factor_overrides, Mapping):
        raise ValueError("factor_overrides must be a mapping")

    overrides: dict[tuple[FertilizerType, SoilPHClass], EmissionFactor] = {}
    for key, factor in (factor_overrides or {}).items():
        if not isinstance(key, tuple) or len(key) != 2:
            raise ValueError("NH3 factor override keys must be (fertilizer, soil pH)")
        fertilizer = _enum_value(FertilizerType, key[0], "fertilizer type")
        override_pH = _enum_value(SoilPHClass, key[1], "soil pH class")
        if not isinstance(factor, EmissionFactor):
            raise ValueError("NH3 factor overrides must be EmissionFactor instances")
        if factor.unit != _FACTOR_UNIT:
            raise ValueError(f"NH3 factor overrides require units {_FACTOR_UNIT!r}")
        overrides[(fertilizer, override_pH)] = factor

    total_kg = 0.0
    sources: list[str] = []
    for fertilizer_value, nitrogen_kg in nitrogen_kg_by_fertilizer.items():
        fertilizer = _enum_value(
            FertilizerType, fertilizer_value, "fertilizer type"
        )
        nonnegative(nitrogen_kg, f"nitrogen_kg_by_fertilizer[{fertilizer.value!r}]")
        factor = overrides.get((fertilizer, pH_class))
        if factor is None:
            default_factor = _NH3_EF_G_PER_KG_N[(fertilizer, pH_class)]
            factor_value = default_factor.value
            factor_source = default_factor.table_reference
        else:
            factor_value = factor.value
            factor_source = factor.source
        total_kg += nitrogen_kg * factor_value / 1000
        if factor_source not in sources:
            sources.append(factor_source)

    return Emission(
        flow="Ammonia",
        amount_kg=total_kg,
        methodology=(
            "EMEP/EEA Guidebook 2023, Chapter 3.D, section 3.4.1, "
            "Equation (4), Table 3-2. Table 3-2 factors vary by fertiliser "
            "and soil pH, not climate; NH3 mass is calculated directly."
        ),
        factor_source="; ".join(sources) or _TABLE_SOURCE,
    )

"""Tier 2 crop-operation PM emissions from agricultural fields."""

from collections.abc import Mapping
from enum import Enum

from agritool.models import Emission, EmissionFactor, nonnegative
from agritool.emissions.eea_emep_2023.types import ClimateZone, FactorEntry


class Crop(str, Enum):
    WHEAT = "Wheat"
    RYE = "Rye"
    BARLEY = "Barley"
    OATS = "Oats"
    OTHER_ARABLE = "Other arable"
    GRASS = "Grass"


class Operation(str, Enum):
    SOIL_CULTIVATION = "Soil cultivation"
    HARVESTING = "Harvesting"
    CLEANING = "Cleaning"
    DRYING = "Drying"


class PMSize(str, Enum):
    PM10 = "PM10"
    PM25 = "PM2.5"


_OPERATION_ORDER = tuple(Operation)
_ROWS: dict[Crop, dict[ClimateZone, dict[PMSize, tuple[float | None, ...]]]] = {
    Crop.WHEAT: {
        ClimateZone.WET: {
            PMSize.PM10: (0.25, 2.7, 0.19, 0.56),
            PMSize.PM25: (0.015, 0.02, 0.009, 0.168),
        },
        ClimateZone.DRY: {
            PMSize.PM10: (2.25, 2.45, 0.19, 0),
            PMSize.PM25: (0.12, 0.098, 0.0095, 0),
        },
    },
    Crop.RYE: {
        ClimateZone.WET: {
            PMSize.PM10: (0.25, 2.0, 0.16, 0.37),
            PMSize.PM25: (0.015, 0.015, 0.008, 0.111),
        },
        ClimateZone.DRY: {
            PMSize.PM10: (2.25, 1.85, 0.16, 0),
            PMSize.PM25: (0.12, 0.074, 0.008, 0),
        },
    },
    Crop.BARLEY: {
        ClimateZone.WET: {
            PMSize.PM10: (0.25, 2.3, 0.16, 0.43),
            PMSize.PM25: (0.015, 0.016, 0.008, 0.129),
        },
        ClimateZone.DRY: {
            PMSize.PM10: (2.25, 2.05, 0.16, 0),
            PMSize.PM25: (0.12, 0.082, 0.008, 0),
        },
    },
    Crop.OATS: {
        ClimateZone.WET: {
            PMSize.PM10: (0.25, 3.4, 0.25, 0.66),
            PMSize.PM25: (0.015, 0.025, 0.0125, 0.198),
        },
        ClimateZone.DRY: {
            PMSize.PM10: (2.25, 3.10, 0.25, 0),
            PMSize.PM25: (0.12, 0.125, 0.0125, 0),
        },
    },
    Crop.OTHER_ARABLE: {
        ClimateZone.WET: {
            PMSize.PM10: (0.25, None, None, None),
            PMSize.PM25: (0.015, None, None, None),
        },
        ClimateZone.DRY: {
            PMSize.PM10: (2.25, None, None, None),
            PMSize.PM25: (0.12, None, None, None),
        },
    },
    Crop.GRASS: {
        ClimateZone.WET: {
            PMSize.PM10: (0.25, 0.25, 0, 0),
            PMSize.PM25: (0.015, 0.01, 0, 0),
        },
        ClimateZone.DRY: {
            PMSize.PM10: (2.25, 1.25, 0, 0),
            PMSize.PM25: (0.12, 0.05, 0, 0),
        },
    },
}
_TABLE_BY_SIZE_AND_CLIMATE = {
    (PMSize.PM10, ClimateZone.WET): "Table 3-6",
    (PMSize.PM10, ClimateZone.DRY): "Table 3-7",
    (PMSize.PM25, ClimateZone.WET): "Table 3-8",
    (PMSize.PM25, ClimateZone.DRY): "Table 3-9",
}
_PM_FACTORS: dict[tuple[Crop, Operation, ClimateZone, PMSize], FactorEntry] = {}
for crop, climate_factors in _ROWS.items():
    for climate, size_factors in climate_factors.items():
        for size, operation_values in size_factors.items():
            table = _TABLE_BY_SIZE_AND_CLIMATE[(size, climate)]
            unit = f"kg {size.value}/ha"
            for operation, value in zip(_OPERATION_ORDER, operation_values):
                if value is not None:
                    _PM_FACTORS[(crop, operation, climate, size)] = FactorEntry(
                        value,
                        unit,
                        f"EMEP/EEA Guidebook 2023, Chapter 3.D, section 3.4.1, {table}",
                    )


def _enum_value(enum_type: type[Enum], value: object, name: str) -> Enum:
    if enum_type is Crop and value == "Oat":
        value = Crop.OATS.value
    try:
        return enum_type(value)
    except (TypeError, ValueError):
        raise ValueError(f"unknown {name}: {value!r}") from None


def _factor_for(
    crop: Crop,
    operation: Operation,
    climate: ClimateZone,
    size: PMSize,
    overrides: Mapping[tuple[Crop, Operation, ClimateZone, PMSize], EmissionFactor],
) -> tuple[float, str]:
    key = (crop, operation, climate, size)
    override = overrides.get(key)
    if override is not None:
        expected_unit = f"kg {size.value}/ha"
        if override.unit != expected_unit:
            raise ValueError(f"{size.value} factor overrides require units {expected_unit!r}")
        return override.value, override.source
    entry = _PM_FACTORS.get(key)
    if entry is None:
        raise ValueError(
            f"no Tier 2 factor is given for {crop.value}/{operation.value} "
            f"in {climate.value} climate ({size.value})"
        )
    return entry.value, entry.table_reference


def particulate_matter_from_field_operations(
    crop: Crop | str,
    area_ha: float,
    climate_zone: ClimateZone | str,
    operation_counts: Mapping[Operation | str, int],
    factor_overrides: Mapping[
        tuple[Crop | str, Operation | str, ClimateZone | str, PMSize | str],
        EmissionFactor,
    ]
    | None = None,
) -> tuple[Emission, Emission]:
    """Return ecoinvent PM2.5 and PM2.5–10 emissions, in that order.

    Operation counts are annual occurrences. EMEP/EEA Guidebook 2023,
    Chapter 3.D, section 3.4.1, Equation (5), and Tables 3-6–3-9 provide
    crop-, operation-, climate-, and size-specific kg/ha factors. Dry means
    Mediterranean climate; wet means all other climates. The guidebook's
    PM10 EF includes PM2.5; ecoinvent fractions are mutually exclusive, so
    the >2.5–<10 μm result is PM10 minus PM2.5. Grass factors include haymaking
    only. The tables give no factors for Other arable operations marked NC.

    Overrides use (crop, operation, climate, size) keys and units kg PM10/ha
    or kg PM2.5/ha, applied per operation occurrence.
    """
    selected_crop = _enum_value(Crop, crop, "crop")
    selected_climate = _enum_value(ClimateZone, climate_zone, "climate zone")
    nonnegative(area_ha, "area_ha")
    if not isinstance(operation_counts, Mapping):
        raise ValueError("operation_counts must be a mapping")
    if factor_overrides is not None and not isinstance(factor_overrides, Mapping):
        raise ValueError("factor_overrides must be a mapping")

    overrides: dict[
        tuple[Crop, Operation, ClimateZone, PMSize], EmissionFactor
    ] = {}
    for key, factor in (factor_overrides or {}).items():
        if not isinstance(key, tuple) or len(key) != 4:
            raise ValueError("PM factor override keys must be (crop, operation, climate, size)")
        override_key = (
            _enum_value(Crop, key[0], "crop"),
            _enum_value(Operation, key[1], "operation"),
            _enum_value(ClimateZone, key[2], "climate zone"),
            _enum_value(PMSize, key[3], "PM size"),
        )
        if not isinstance(factor, EmissionFactor):
            raise ValueError("PM factor overrides must be EmissionFactor instances")
        expected_unit = f"kg {override_key[3].value}/ha"
        if factor.unit != expected_unit:
            raise ValueError(f"{override_key[3].value} factor overrides require units {expected_unit!r}")
        overrides[override_key] = factor

    selected_counts: dict[Operation, int] = {}
    for operation_value, count in operation_counts.items():
        operation = _enum_value(Operation, operation_value, "operation")
        nonnegative(count, f"operation_counts[{operation.value!r}]")
        if isinstance(count, bool) or not isinstance(count, int):
            raise ValueError(f"operation count for {operation.value!r} must be an integer")
        selected_counts[operation] = count

    totals = {size: 0.0 for size in PMSize}
    sources: dict[PMSize, list[str]] = {size: [] for size in PMSize}
    for operation, count in selected_counts.items():
        if count == 0:
            continue
        for size in PMSize:
            factor_value, factor_source = _factor_for(
                selected_crop, operation, selected_climate, size, overrides
            )
            totals[size] += area_ha * count * factor_value
            if factor_source not in sources[size]:
                sources[size].append(factor_source)

    coarse_kg = totals[PMSize.PM10] - totals[PMSize.PM25]
    if coarse_kg < 0:
        raise ValueError("PM10 factors must be at least as large as PM2.5 factors")
    if not sources[PMSize.PM10]:
        sources[PMSize.PM10].append(
            "EMEP/EEA Guidebook 2023, Chapter 3.D, section 3.4.1, Tables 3-6 and 3-7"
        )
    if not sources[PMSize.PM25]:
        sources[PMSize.PM25].append(
            "EMEP/EEA Guidebook 2023, Chapter 3.D, section 3.4.1, Tables 3-8 and 3-9"
        )
    all_sources = list(dict.fromkeys(sources[PMSize.PM10] + sources[PMSize.PM25]))
    methodology = (
        "EMEP/EEA Guidebook 2023, Chapter 3.D, section 3.4.1, Equation (5), "
        "Tables 3-6–3-9; ecoinvent PM2.5–10 is derived as PM10 minus PM2.5."
    )
    return (
        Emission(
            flow="Particulate Matter, < 2.5 um",
            amount_kg=totals[PMSize.PM25],
            methodology=methodology,
            factor_source="; ".join(sources[PMSize.PM25]),
        ),
        Emission(
            flow="Particulate Matter, > 2.5 um and < 10um",
            amount_kg=coarse_kg,
            methodology=methodology,
            factor_source="; ".join(all_sources),
        ),
    )
